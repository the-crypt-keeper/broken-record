import sys
import os
from collections import Counter
import re
from collections import OrderedDict

IGNORED_WORDS = [] #"of","a","at","and","her","his","as","in","that","the","with","","are","to","she","he","for","I","him","says"]

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
            return "", 0

        # Extract lines starting with "Skye:" after the marker
        skye_lines = [line.strip() for line in lines[done_index+1:] if line.startswith("Skye:")]
        
        # Join all the lines into a single text block
        skye_text = ' '.join(skye_lines)
        
        # Remove "Skye:" from the beginning of each line
        skye_text = re.sub(r"Skye:", "", skye_text)
        
        # Count characters
        character_count = len(skye_text)
        
        return skye_text.strip(), character_count
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

def display_histogram(density_buckets):
    print("\nHistogram of Loop Densities:")
    for bucket, filenames in density_buckets.items():
        next_bucket = list(density_buckets.keys())[list(density_buckets.keys()).index(bucket) + 1] if bucket != list(density_buckets.keys())[-1] else float("inf")
        print(f"{bucket:.2f}-{next_bucket:.2f}: {'#' * len(filenames)} ({len(filenames)})")

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
        (0.1, []),
        (0.2, []),
        (0.3, []),
        (0.4, []),
        (0.5, []),
        (0.6, []),
        (0.7, []),
        (0.8, []),
        (0.9, []),
        (1.0, [])
    ])
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.log'):
            file_path = os.path.join(folder_path, filename)
            text, character_count = extract_skye_lines(file_path)
            if text:
                print(f"\n{filename}")
                all_ngrams = []
                for n in range(64, 4, -1):
                    common_ngrams, text = find_and_remove_ngrams(text, n)
                    all_ngrams.extend(common_ngrams)
                
                # Sort all_ngrams by count in descending order
                sorted_ngrams = sorted(all_ngrams, key=lambda x: x[1], reverse=True)
                
                # Calculate and print the loop score and density
                loop_score = calculate_loop_score(sorted_ngrams)
                loop_density = loop_score / character_count if character_count > 0 else 0
                print(f"Character Count: {character_count}")
                print(f"Loop Score: {loop_score}")
                print(f"Loop Density: {loop_density:.4f}")
                
                # Add filename to appropriate bucket
                for bucket in reversed(density_buckets.keys()):
                    if loop_density >= bucket:
                        density_buckets[bucket].append(filename)
                        break
                
                if loop_score > 1000 and loop_density > 0.3:
                    for ngram, count in sorted_ngrams[0:20]:
                        print(f"  {ngram} (found {count} times)")

    # Display histogram
    display_histogram(density_buckets)
