# Configuration Documentation

## General Settings

- `conversation`: An array of initial conversation messages to start the dialogue.
- `agent_prefix`: The prefix used for the AI assistant's responses.

## Token Limits

- `initial_tokens`: Number of tokens in the initial conversation.
- `total_tokens`: The maximum number of tokens for the entire conversation.
- `turn_max_tokens`: The maximum number of tokens per turn.

## Sampling Parameters

The `sampler` object contains parameters for text generation:

- `temperature`: Controls randomness in generation. Higher values make output more random.
- `top_p`: Nucleus sampling parameter. Lower values make output more focused.
- `repetition_penalty`: Penalizes repetition in generated text (vllm/aphrodite-engine server)
- `repeat_penalty`: Penalizes repetition in generated text (llama.cpp server)
- `repeat_last_n`: Number of tokens to consider for repeat penalty (llama.cpp server)
- `stop`: Array of strings that will stop generation when encountered.

## API and Model Settings

- `api_url`: The URL for the main language model API.
- `tokenizer`: The tokenizer to use for the main model.
- `user_api_url`: The URL for the user simulation model API.
- `user_tokenizer`: The tokenizer to use for the user model.

## User Simulation Settings

- `user_prefix`: The prefix used for user responses.
- `user_system`: The system prompt for user simulation.
- `user_memory`: The number of recent messages to include in user context.
- `user_sampler`: Sampling parameters for user (defaults to `sampler`)

## Example

See `config.json` for a complete example of these settings in use.
