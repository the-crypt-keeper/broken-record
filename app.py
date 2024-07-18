import streamlit as st
import yaml
import plotly.express as px
from transformers import AutoTokenizer
import argparse
import sys

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def create_histogram(data, tokenizer):
    token_counts = {}
    for token in data['output_tokens']:
        if token in token_counts:
            token_counts[token] += 1
        else:
            token_counts[token] = 1
    
    sorted_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)
    top_tokens = sorted_tokens[:50]  # Display top 50 tokens
    
    tokens = [f"{token} ({tokenizer.decode([token])})" for token, _ in top_tokens]
    counts = [count for _, count in top_tokens]
    
    fig = px.bar(x=tokens, y=counts, labels={'x': 'Token (Text)', 'y': 'Count'})
    fig.update_layout(title='Most Common Output Tokens', xaxis_tickangle=-45)
    return fig

def main():
    parser = argparse.ArgumentParser(description='Create a Streamlit app for LLM logit visualization')
    parser.add_argument('yaml_path', type=str, help='Path to the YAML file')
    parser.add_argument('tokenizer_name', type=str, help='Name of the Hugging Face tokenizer')
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    
    args = parser.parse_args()
    
    st.set_page_config(page_title='Broken Record: LLM Repetition Analyzer', layout='wide')
    
    data = load_yaml(args.yaml_path)
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_name)
    
    fig = create_histogram(data, tokenizer)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()