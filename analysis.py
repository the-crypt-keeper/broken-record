import sys
import os
from collections import Counter
import re

IGNORED_WORDS = [] #"of","a","at","and","her","his","as","in","that","the","with","","are","to","she","he","for","I","him","says"]

def extract_skye_lines(filename, n=1):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        
        # Find the "--- DONE ---" marker
        try:
            done_index = next(i for i, line in enumerate(lines) if "--- DONE ---" in line)
        except StopIteration:
            print(f"Marker '--- DONE ---' not found in the file: {filename}")
            return Counter()

        # Extract lines starting with "Skye:" after the marker
        skye_lines = [line for line in lines[done_index+1:] if line.startswith("Skye:")]
        
        # Join all the lines into a single text block
        skye_text = ' '.join(skye_lines)
        
        # Remove "Skye:" from the beginning of each line
        skye_text = re.sub(r"Skye:", "", skye_text)
        
        # Split the text into words
        words = skye_text.split()
        
        # Generate n-grams
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            if not any(word.lower() in IGNORED_WORDS for word in ngram.split()):
                ngrams.append(ngram)
        
        # Create a histogram of the most common n-grams
        ngram_counts = Counter(ngrams)
        
        return {os.path.basename(filename): ngram_counts}
    except Exception as e:
        print(f"Error processing file {filename}: {str(e)}")
        return {}

def process_folder(folder_path, n=1):
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
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script.py <folder_path> [n]")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) == 3 else 1
    
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)
    
    combined_counts, file_counts = process_folder(folder_path, n)
    
    # if combined_counts:
    #     print(f"Most common {n}-grams across all files:")
    #     for ngram, count in combined_counts.most_common(25):
    #         print(f"\n{ngram}: {count}")
    #         print("Files:")
    #         for filename, counts in file_counts.items():
    #             if ngram in counts:
    #                 print(f"  {filename}: {counts[ngram]}")
    # else:
    #     print("No valid data found in the specified folder.")

    for filename, counts in file_counts.items():
        print()
        print(f"{filename}")
        for ngram, count in counts.most_common(10):
            print(f"  {ngram}: {counts[ngram]}")