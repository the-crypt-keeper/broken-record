import requests
import time
import json
import sys
import random
from transformers import AutoTokenizer

def stream_response(llm, prompt, sampler, max_tokens = 2048):
    data = {
        "model": llm['model'],
        "n": 1,
        "prompt": prompt,
        "n_predict": max_tokens,
        "max_tokens": max_tokens,
        "stream": True,
        "cache_prompt": True,
        **sampler
    }
    
    completion = ''
    tokens = 0
    
    try:
        req_start_time = time.time()
        first_token_time = None
        
        with requests.post(llm['api_url']+"/v1/completions", headers={"Content-Type": "application/json"}, json=data, stream=True) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        if decoded_line[6:] == '[DONE]':
                            break
                        
                        try:
                            json_data = json.loads(decoded_line[6:])
                        except Exception as e:
                            print('ERROR')
                            print(decoded_line)
                            print(str(e))
                            continue
                            
                        
                        fragment = None
                        stop = False
                        
                        if 'content' in json_data:
                            fragment = json_data['content']
                            stop = json_data['stop']
                        elif 'choices' in json_data:
                            fragment = json_data['choices'][0]['text']
                            stop = json_data['choices'][0].get('stop_reason') is not None
                        else:
                            print(f"Error: {json_data}")
                            
                        completion += fragment
                        print(fragment, end='')
                        sys.stdout.flush()
                        tokens += 1
                        if first_token_time is None: first_token_time = time.time()
                        
                        if stop: break                            
                        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        
    ttfs = first_token_time-req_start_time if (first_token_time is not None) and (req_start_time is not None) else None
    elapsed = time.time()-first_token_time if first_token_time is not None else None
        
    return completion, tokens, ttfs, elapsed

if __name__ == "__main__":
    with open('config.json' if len(sys.argv) == 1 else sys.argv[1]) as f:
        config = json.load(f)
        
    llm = {'api_url': config['api_url'] }
    llm['model'] = requests.get(llm['api_url']+'/v1/models').json()['data'][0]['id']

    user_llm = {'api_url': config['user_api_url'] }
    user_llm['model'] = requests.get(user_llm['api_url']+'/v1/models').json()['data'][0]['id']
        
    tokenizer = AutoTokenizer.from_pretrained(config['tokenizer'])
    user_tokenizer = AutoTokenizer.from_pretrained(config.get('user_tokenizer', config['tokenizer']))

    conversation = config['conversation']
    token_counts = [0 for x in range(len(conversation))]
    token_counts[0] = config.get('initial_tokens',0)
   
    while sum(token_counts) < config.get('total_tokens', 2048):
        prompt = tokenizer.apply_chat_template(conversation, bos_token='', tokenize=False, add_generation_prompt=True) + config['agent_prefix']
        print(f"\n--- {sum(token_counts)} ---\n")
        print(config['agent_prefix'], end='')
        
        completion, tokens, _, _ = stream_response(llm, prompt, config.get('sampler'), config.get('turn_max_tokens', 512))        
        token_counts.append(tokens)
        conversation += [{"role": "assistant", "content": config['agent_prefix']+completion}]
        
        user_messages = [
            {"role": "system", "content": config["user_system"]}
        ]
        for msg in conversation[-1*config.get('user_memory',9):]:
            if msg["role"] == "user":
                user_messages.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "assistant":
                user_messages.append({"role": "user", "content": msg["content"]})
        user_prompt = user_tokenizer.apply_chat_template(user_messages, bos_token='', tokenize=False, add_generation_prompt=True) + config['user_prefix']

        print()
        print(config['user_prefix'], end='')
        user_text, tokens, _, _ = stream_response(user_llm, user_prompt, config.get('user_sampler', config.get('sampler')), config.get('turn_max_tokens', 512))        

        token_counts.append(tokens)
        conversation += [{"role": "user", "content": config["user_prefix"] + user_text}]

    total_tokens = 0
    print()
    print("--- DONE ---")
    print(f"Assistant Model: {llm.get('model')}")
    print(f"User Model: {user_llm.get('model')}")    
    print()
    for msg, count in zip(conversation, token_counts):
        print(f'=== {msg.get("role")} @ {total_tokens} ===')
        print(msg['content'])
        total_tokens += count
    print(f"\n--- {total_tokens} tokens, {len(conversation)} turns ---\n")