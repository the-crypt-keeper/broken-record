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
        "stream": True,
        "use_cache": True,
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
                        json_data = json.loads(decoded_line[6:])
                        if 'content' in json_data:                           
                            completion += json_data['content']
                            print(json_data['content'], end='')
                            sys.stdout.flush()
                            tokens += 1
                            if first_token_time is None: first_token_time = time.time()
                            
                            if json_data['stop']:
                                break
                        else:
                            print(f"Error: {json_data}")
                        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        
    ttfs = first_token_time-req_start_time if (first_token_time is not None) and (req_start_time is not None) else None
    elapsed = time.time()-first_token_time if first_token_time is not None else None
        
    return completion, tokens, ttfs, elapsed

if __name__ == "__main__":
    with open('config.json') as f:
        config = json.load(f)
        
    llm = {'api_url': config['api_url'] }
    llm['model'] = requests.get(llm['api_url']+'/v1/models').json()['data'][0]['id']
    
    tokenizer = AutoTokenizer.from_pretrained(config['tokenizer'])

    conversation = config['conversation']
    total_tokens = 0
   
    while total_tokens < config.get('total_tokens', 2048):
        prompt = tokenizer.apply_chat_template(conversation, bos_token='', tokenize=False, add_generation_prompt=True)
        
        print("---")
        print(prompt)
        
        completion, tokens, _, _ = stream_response(llm, prompt, config.get('sampler'), config.get('turn_max_tokens', 512))        
        total_tokens += tokens
        
        conversation += [{"role": "assistant", "content": completion}]       
        print(f"\n\ntotal_tokens = {total_tokens}")
        
        user_messages = [
            {"role": "system", "content": config["user_system"]}
        ]
        for msg in conversation[-3:]:
            if msg["role"] == "user":
                user_messages.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "assistant":
                user_messages.append({"role": "user", "content": msg["content"]})
        user_prompt = tokenizer.apply_chat_template(user_messages, bos_token='', tokenize=False, add_generation_prompt=True) + config['user_prefix']
        user_text, tokens, _, _ = stream_response(llm, user_prompt, config.get('sampler'), config.get('turn_max_tokens', 512))        

        conversation += [{"role": "user", "content": config["user_prefix"] + user_text}]
