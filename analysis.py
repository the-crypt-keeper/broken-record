import sys
from collections import Counter
import re

IGNORED_WORDS = ["of","a","at","and","her","his","as","in","that","the","with","","are","to","she","he","for","I","him","says"]

def extract_skye_lines(filename, n=1):
    with open(filename, 'r') as file:
        lines = file.readlines()
    
    # Find the "--- DONE ---" marker
    try:
        done_index = next(i for i, line in enumerate(lines) if "--- DONE ---" in line)
    except StopIteration:
        print("Marker '--- DONE ---' not found in the file.")
        return

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
    
    return ngram_counts

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script.py <filename> [n]")
        sys.exit(1)
    
    filename = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) == 3 else 1
    
    ngram_counts = extract_skye_lines(filename, n)
    
    if ngram_counts:
        print(f"Most common {n}-grams:")
        for ngram, count in ngram_counts.most_common(25):
            print(f"{ngram}: {count}")
