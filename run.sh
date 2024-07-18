# parameters
MODEL=~/models/L3-8B-Celeste-v1.Q6_K.gguf
TOKENIZER=nothingiisreal/L3-8B-Celeste-v1
PROMPT=prompt.txt
LLAMA_CPP_PATH=./
LLAMA_CPP_ARGS="-ngl 99 -fa --temp 0 --top-k 0 --top-p 1.0 --min-p 0.0"
CONTEXT_LENGTH=1024
GENERATION_LENGTH=1024
BIASES="--logit-bias 128009-inf"

# make logs dir
mkdir -p logs

# run inference
$LLAMA_CPP_PATH/llama-cli \
 $LLAMA_CPP_ARGS \
 -m $MODEL \
 -c $CONTEXT_LENGTH \
 -n $GENERATION_LENGTH \
 -f $PROMPT \
 $BIASES \
 --verbose-prompt \
 --verbose \
 --logdir logs/ \
 --log-new

# open app
LATEST_LOG=`ls -tr logs | tail -n 1`
streamlit run app.py logs/$LATEST_LOG $TOKENIZER