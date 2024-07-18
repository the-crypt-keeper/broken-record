# parameters
MODEL=~/models/L3-8B-Celeste-v1.Q6_K.gguf
TOKENIZER=nothingiisreal/L3-8B-Celeste-v1
PROMPT=roleplay.txt
LLAMA_CPP_PATH=./build
LLAMA_CPP_ARGS="-ngl 99 -fa --temp 0 --top-k 0 --top-p 1.0 --min-p 0.0"
CONTEXT_LENGTH=4096
GENERATION_LENGTH=4096
BIASES="--ignore-eos"

# build?
if [ ! -e $LLAMA_CPP_PATH/llama-cli ]; then
  source build.sh
fi

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