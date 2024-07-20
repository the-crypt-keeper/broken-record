import sys
from collections import Counter
import re

IGNORED_WORDS = ["of","a","at","and","her","his","as","in","that","the","with","","are","to","she","he","for","I","him","says"]

def extract_skye_lines(filename):
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
    
    # Split the text into words and filter out non-alphabetic characters
    words = [x for x in skye_text.split(' ') if x.lower() not in IGNORED_WORDS]
    
    # Create a histogram of the most common words
    word_counts = Counter(words)
    
    return word_counts

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    word_counts = extract_skye_lines(filename)
    
    if word_counts:
        print("Most common words:")
        for word, count in word_counts.most_common(25):
            print(f"{word}: {count}")
