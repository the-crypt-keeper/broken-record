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
        skye_lines = [line for line in lines[done_index+1:] if line.startswith("Skye:")]
        
        # Join all the lines into a single text block
        skye_text = ' '.join(skye_lines)
        
        # Remove "Skye:" from the beginning of each line
        skye_text = re.sub(r"Skye:", "", skye_text)
        
        return skye_text.strip()
    except Exception as e:
        print(f"Error processing file {filename}: {str(e)}")
        return ""

def find_and_remove_ngrams(text, n):
    words = text.split()
    ngrams = []
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        if not any(word.lower() in IGNORED_WORDS for word in ngram.split()):
            ngrams.append(ngram)
    
    ngram_counts = Counter(ngrams)
    common_ngrams = [ngram for ngram, count in ngram_counts.items() if count > 1]
    
    for ngram in common_ngrams:
        text = remove_ngram_from_text(text, ngram)
    
    return common_ngrams, text

def process_folder(folder_path):
    combined_counts = Counter()
    file_counts = {}
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.log'):
            file_path = os.path.join(folder_path, filename)
            file_count = extract_skye_lines(file_path, n)
            if file_count:
                file_counts[os.path.basename(filename)] = file_count[os.path.basename(filename)]
                combined_counts.update(file_count[os.path.basename(filename)])
    
    return combined_counts, file_counts

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    file_results = process_folder(folder_path)
    
    for filename, ngrams in file_results.items():
        print(f"\n{filename}")
        for ngram in ngrams:
            print(f"  {ngram}")
