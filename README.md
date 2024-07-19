# Parrot: Synthetic Deep-Roleplay Dialogue Generation Tool

## Overview

Parrot is a powerful tool designed for generating synthetic deep-roleplay dialogues using advanced language models. It simulates conversations between two characters, allowing for the creation of rich, interactive narratives and enable investigation into LLM conversation looping behaviors.

## Features

- Configurable conversation settings
- Utilizes two separate language models for assistant and user roles
- Streaming response generation
- Token counting and management
- Customizable sampling parameters

## Components

1. `parrot.py`: The main Python script that handles the dialogue generation.
2. `parrot.sh`: A Bash script for running multiple iterations of the dialogue generation.
3. `config.json`: Configuration file for setting up the dialogue parameters.

## Usage

1. Set up your configuration in `config.json`. Refer to [CONFIG.md](CONFIG.md) for detailed information on the configuration options.

2. Run a single iteration for testing:
   ```
   python parrot.py
   ```

3. Run multiple iterations with logging using the bash script:
   ```
   ./parrot.sh <number_of_iterations>
   ```

## Configuration

The `config.json` file allows you to customize various aspects of the dialogue generation, including:

- Initial conversation prompts
- Character prefixes
- Token limits
- Sampling parameters
- API endpoints
- User simulation settings

For a complete breakdown of the configuration options, please refer to [CONFIG.md](CONFIG.md).

## Requirements

- Python 3.x
- `requests` library
- `transformers` library
- Access to language model APIs (as specified in the configuration)

## License

[MIT](LICENSE.md)