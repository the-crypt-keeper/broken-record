import sys
import os
from collections import Counter
import re
from collections import OrderedDict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

IGNORED_WORDS = [] #"of","a","at","and","her","his","as","in","that","the","with","","are","to","she","he","for","I","him","says"]

def create_length_histogram(lengths):
    if not lengths:
        return OrderedDict()
    
    buckets = OrderedDict([
        ((0, 1), 0),
        *[((i * 100, (i + 1) * 100), 0) for i in range(10)],
        ((1000, float('inf')), 0)
    ])
    
    for length in lengths:
        if length <= 1:
            buckets[(0, 1)] += 1
        elif length > 1000:
            buckets[(1000, float('inf'))] += 1
        else:
            bucket_index = (length - 1) // 100
            bucket_key = list(buckets.keys())[bucket_index + 1]  # +1 to account for the 0-1 bucket
            buckets[bucket_key] += 1
    
    return buckets

def calculate_loop_score(ngrams):
    return sum(len(ngram.split()) * count for ngram, count in ngrams)

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
        character_count = 0
        for line in skye_lines:
            cleaned_line = re.sub(r"^Skye:", "", line).strip()
            response_lengths.append(len(cleaned_line))
            cleaned_lines.append(cleaned_line)
            character_count += len(cleaned_line)
        
        # Join all the lines into a single text block
        skye_text = ' '.join(cleaned_lines)
        
        return skye_text.strip(), character_count, response_lengths
    except Exception as e:
        print(f"Error processing file {filename}: {str(e)}")
        return "", 0

def find_and_remove_ngrams(text, n):
    def find_and_remove_ngrams_once(text):
        words = text.split(' ')
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            if not any(word.lower() in IGNORED_WORDS for word in ngram.split()):
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

def process_file(file_path):
    filename = os.path.basename(file_path)
    text, character_count, response_lengths = extract_skye_lines(file_path)
    if not text:
        return None

    all_ngrams = []
    for n in range(64, 4, -1):
        common_ngrams, text = find_and_remove_ngrams(text, n)
        all_ngrams.extend(common_ngrams)
    
    sorted_ngrams = sorted(all_ngrams, key=lambda x: x[1], reverse=True)
    loop_score = calculate_loop_score(sorted_ngrams)
    loop_density = loop_score / character_count if character_count > 0 else 0

    return {
        'filename': filename,
        'character_count': character_count,
        'loop_score': loop_score,
        'loop_density': loop_density,
        'sorted_ngrams': sorted_ngrams,
        'response_lengths': response_lengths
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
        
    density_buckets = OrderedDict([
        (0.00, []),
        (0.01, []),
        (0.02, []),
        (0.03, []),
        (0.04, []),
        (0.05, []),
        (0.06, []),
        (0.07, []),
        (0.08, []),
        (0.09, []),
        (0.10, [])
    ])
    
    all_response_lengths = []
    
    log_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.log')]
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_file = {executor.submit(process_file, file_path): file_path for file_path in log_files}
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    print(f"\n{result['filename']}")
                    print(f"Character Count: {result['character_count']}")
                    print(f"Loop Score: {result['loop_score']}")
                    print(f"Loop Density: {result['loop_density']:.4f}")
                    
                    for bucket in reversed(density_buckets.keys()):
                        if result['loop_density'] >= bucket:
                            density_buckets[bucket].append(result['filename'])
                            break
                    
                    if result['loop_score'] > 1000 and result['loop_density'] > 0.05:
                        for ngram, count in result['sorted_ngrams'][0:20]:
                            print(f"  {ngram} (found {count} times)")
                    
                    all_response_lengths.extend(result['response_lengths'])
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
