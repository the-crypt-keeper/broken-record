import sys
import os
from collections import Counter
import re
from collections import OrderedDict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import matplotlib.pyplot as plt
import json
from transformers import AutoTokenizer
from parrot import stream_response
import requests

def create_length_histogram(lengths):
    if not lengths:
        return OrderedDict()
    
    buckets = OrderedDict([
        ((0, 1), 0),
        *[((i * 100, (i + 1) * 100), 0) for i in range(20)],
        ((2000, float('inf')), 0)
    ])
    
    for length in lengths:
        if length <= 1:
            buckets[(0, 1)] += 1
        elif length > 2000:
            buckets[(2000, float('inf'))] += 1
        else:
            bucket_index = (length - 1) // 100
            bucket_key = list(buckets.keys())[bucket_index + 1]  # +1 to account for the 0-1 bucket
            buckets[bucket_key] += 1
    
    return buckets

def calculate_loop_score(ngrams):
    return sum(len(ngram) * count for ngram, count in ngrams)

def remove_ngram_from_text(text, ngram):
    if not ngram in text: print('REMOVE ERROR', ngram)
    return text.replace(ngram, '')

def extract_skye_lines(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        # Find the "--- DONE ---" marker
        try:
            done_index = next(i for i, line in enumerate(lines) if "--- DONE ---" in line)
        except StopIteration:
            print(f"Marker '--- DONE ---' not found in the file: {filename}")
            return "", 0, []

        # Extract lines starting with "Skye:" after the marker
        skye_lines = [line.strip() for line in lines[done_index+1:] if line.startswith("Skye:")]
        
        # Remove "Skye:" from the beginning of each line and get individual response lengths
        response_lengths = []
        cleaned_lines = []

        for line in skye_lines:
            cleaned_line = re.sub(r"^Skye:", "", line).strip()
            response_lengths.append(len(cleaned_line))
            if cleaned_line == "": cleaned_line = "[empty]"
            cleaned_lines.append(cleaned_line)

        
        # Join all the lines into a single text block
        skye_text = ' '.join(cleaned_lines)
        
        return skye_text.strip(), lines[done_index+1:], response_lengths
    except Exception as e:
        print(f"Error processing file {filename}: {str(e)}")
        return "", 0

def find_and_remove_ngrams(text, n):
    def find_and_remove_ngrams_once(text):
        words = text.split(' ')
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)
        
        ngram_counts = Counter(ngrams)
        common_ngrams = [(ngram, count) for ngram, count in ngram_counts.items() if count > 1]
        
        if common_ngrams:
            most_common_ngram = max(common_ngrams, key=lambda x: x[1])
            text = remove_ngram_from_text(text, most_common_ngram[0])
            return [most_common_ngram], text
        
        return [], text

    all_common_ngrams = []
    while True:
        common_ngrams, new_text = find_and_remove_ngrams_once(text)
        if not common_ngrams:
            break
        all_common_ngrams.extend(common_ngrams)
        text = new_text

    # Combine counts for ngrams that were removed multiple times
    ngram_counts = Counter()
    for ngram, count in all_common_ngrams:
        ngram_counts[ngram] += count

    return list(ngram_counts.items()), text

judge_tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-medium-128k-instruct")
judge_llm = { 'api_url': 'http://100.109.96.89:8099' }
judge_llm['model'] = requests.get(judge_llm['api_url']+'/v1/models').json()['data'][0]['id']

def judge_conversation2(raw_lines, step = 5):
    first_line = None
    for idx, line in enumerate(raw_lines):
        if line.startswith("=== assistant @"):
            first_line = idx
            break

    SYSTEM_PROMPT = """The user will provide sections of a conversation between a couple on a date."""
    INSTRUCT_PROMPT = """INSTRUCTION:
Respond with a JSON object with three keys: `summary`, `topics` and `themes`.
`summary` should be a brief summary of the exchange.
`topics` and `themes` should be lists of single words."""
    
    lines = [x for x in raw_lines[first_line+1:] if not x[0:3] in ["---","==="] and x.strip() != '']
    topics = {}
    replies = []
         
    for idx in range(0, len(lines), step):
        chunk_text = '\n'.join(lines[idx:idx+step])
        messages = [{ "role": "system", "content": SYSTEM_PROMPT }]        
        messages.append({'role': 'user', 'content': chunk_text+INSTRUCT_PROMPT})
        prompt = judge_tokenizer.apply_chat_template(messages, bos_token='', tokenize=False, add_generation_prompt=True)
        summary_text, _, _, _ = stream_response(judge_llm, prompt, { 'temperature': 0.0, "repetition_penalty": 1.1, "top_p": 0.8 }, 1024, False)
        
        try:
            left_bracket = summary_text.find('{')
            right_bracket = summary_text.rfind('}')
            data = json.loads(summary_text[left_bracket:right_bracket+1])
            replies.append(data)
            for k,v in data.items():
                if k not in ['topics','themes']: continue
                for item in v:
                    if item not in topics: topics[item] = 0
                    topics[item]+= 1
        except Exception as e:
            print("ERROR:", str(e))
            print(summary_text)

    return topics, replies

def top_topics(topics):
    topics_by_count = sorted(topics.keys(), key=lambda x: topics[x], reverse=True)
    for topic in topics_by_count:
        count = topics[topic]
        if count > 1:
            print(f"{count} {topic}")

def process_file(file_path):
    filename = os.path.basename(file_path)
    text, raw_lines, response_lengths = extract_skye_lines(file_path)
    character_count = sum(response_lengths)
    if not text:
        return None
    
    topics, replies = judge_conversation2(raw_lines)

    all_ngrams = []
    for n in range(64, 4, -1):
        common_ngrams, text = find_and_remove_ngrams(text, n)
        all_ngrams.extend(common_ngrams)
    
    sorted_ngrams = sorted(all_ngrams, key=lambda x: x[1], reverse=True)
    loop_score = calculate_loop_score(sorted_ngrams)
    loop_density = loop_score / character_count if character_count > 0 else 0

    avg_response_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
    return filename, character_count, loop_score, loop_density, sorted_ngrams, response_lengths, avg_response_length, topics, replies

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
        
    density_buckets = OrderedDict([
        (0.0, []),
        (0.05, []),
        (0.1, []),
        (0.15, []),
        (0.2, []),
        (0.25, []),
        (0.3, []),
        (0.35, []),
        (0.4, []),
        (0.45, []),
        (0.5, []),
        (0.55, []),
        (0.6, []),
        (0.65, []),
        (0.7, []),
        (0.75, []),
        (0.8, [])
    ])
    
    all_response_lengths = []
    scatterplot_data = []
    
    log_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.log')]
    log_files = sorted(log_files)
    
    lock = threading.Lock()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_file = {executor.submit(process_file, file_path): file_path for file_path in log_files}
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    filename, character_count, loop_score, loop_density, sorted_ngrams, response_lengths, avg_response_length, topics, replies = result
                    
                    with lock:
                        print(f"\n{filename}")
                        print(f"Character Count: {character_count}")
                        print(f"Loop Score: {loop_score}")
                        print(f"Loop Density: {loop_density:.4f}")
                        print(f"Average Response Length: {avg_response_length:.2f}")
                        
                        for bucket in reversed(density_buckets.keys()):
                            if loop_density >= bucket:
                                density_buckets[bucket].append(filename)
                                break
                        
                        for ngram, count in sorted_ngrams[0:20]:
                            print(f"  {ngram} (found {count} times)")
                            for ng2, ct2 in sorted_ngrams:
                                if ng2.startswith(ngram) and ng2 != ngram:
                                    print(f"  >> {ng2} (found {ct2} times)")
                        
                        all_response_lengths.extend(response_lengths)
                        scatterplot_data.append((avg_response_length, loop_density))
                        
                        print("Summary:")
                        for data in replies:
                            print("- "+data['summary'])
                        print("Top topics")
                        top_topics(topics)
            except Exception as exc:
                print(f'{file_path} generated an exception: {exc}')

    # Display loop density histogram
    print("\nHistogram of Loop Densities:")
    for bucket, filenames in density_buckets.items():
        next_bucket = list(density_buckets.keys())[list(density_buckets.keys()).index(bucket) + 1] if bucket != list(density_buckets.keys())[-1] else float("inf")
        print(f"{bucket:.2f}-{next_bucket:.2f}: {'#' * len(filenames)} ({len(filenames)})")

    # Create and display response length histogram
    length_histogram = create_length_histogram(all_response_lengths)
    print("\nHistogram of Response Lengths:")
    for (lower, upper), count in length_histogram.items():
        print(f"{lower:.0f}-{upper:.0f}: {'#' * count} ({count})")

    # Create and display the scatterplot
    plt.figure(figsize=(10, 6))
    x, y = zip(*scatterplot_data)
    plt.xlabel('Average Response Length')
    plt.ylabel('Loop Density')
    plt.title('Average Response Length vs Loop Density')
    plt.xlim(0, 2000)
    plt.ylim(0, 1)
    plt.scatter(x, y)
    plt.savefig(os.path.join(folder_path, 'response_length_vs_loop_density.png'))
    plt.close()
    
    with open(os.path.join(folder_path, 'response_length_vs_loop_density.json'), 'w') as f:
        json.dump(scatterplot_data, f)
