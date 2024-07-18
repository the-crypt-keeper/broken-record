import requests
import time
import json
import sys
import random

def stream_response(llm, prompt, max_tokens = 2048):
    data = {
        "model": llm['model'],
        "n": 1,
        "prompt": prompt,
        "temperature": 0.87,
        "top_p": 0.8,
        "repeat_penalty": 1.1,
        "top_k": 0,
        "min_p": 0,
        "n_predict": max_tokens,
        "stream": True,
#        "use_cache": True
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

    prompt = config['prefix'] + config['system']
    for idx, entry in enumerate(config['example']):
        prompt += config['sot'].replace('{role}', entry['role']) + entry['text'] + config['eot']
        
    total_tokens = 0
   
    while total_tokens < config.get('total_tokens', 2048):    
        
        # reply as user
        user_message = random.choice(config['user_replies'])
        prompt += config['sot'].replace('{role}', 'user') + config['user_prefix'] + user_message + config['eot']
        
        # now asisstant
        prompt += config['sot'].replace('{role}', 'assistant')
        
        print("---\n")
        print(prompt, end='<END_OF_PROMPT>')
        completion, tokens, _, _ = stream_response(llm, prompt, config.get('turn_max_tokens', 512))
        
        total_tokens += tokens
        prompt += completion + config['eot']
        
        print(f"\n\ntotal_tokens = {total_tokens}")

    