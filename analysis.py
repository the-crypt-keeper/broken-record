import sys
import os
from collections import Counter
import re

IGNORED_WORDS = [] #"of","a","at","and","her","his","as","in","that","the","with","","are","to","she","he","for","I","him","says"]

def remove_ngram_from_text(text, ngram):
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
            return ""

        # Extract lines starting with "Skye:" after the marker
        skye_lines = [line.strip() for line in lines[done_index+1:] if line.startswith("Skye:")]
        
        # Join all the lines into a single text block
        skye_text = ' '.join(skye_lines)
        
        # Remove "Skye:" from the beginning of each line
        skye_text = re.sub(r"Skye:", "", skye_text)
        
        return skye_text.strip()
    except Exception as e:
        print(f"Error processing file {filename}: {str(e)}")
        return ""

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
        
        for ngram, _ in common_ngrams:
            text = remove_ngram_from_text(text, ngram)
        
        return common_ngrams, text

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.log'):
            file_path = os.path.join(folder_path, filename)
            text = extract_skye_lines(file_path)
            if text:
                print(f"\n{filename}")
                all_ngrams = []
                for n in range(64, 4, -1):
                    common_ngrams, text = find_and_remove_ngrams(text, n)
                    all_ngrams.extend(common_ngrams)
                
                # Sort all_ngrams by count in descending order
                sorted_ngrams = sorted(all_ngrams, key=lambda x: x[1], reverse=True)
                
                for ngram, count in sorted_ngrams[0:20]:
                    print(f"  {ngram} (found {count} times)")
