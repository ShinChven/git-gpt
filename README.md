# Git-GPT

Git-GPT is a versatile CLI tool designed to auto-generate git commit messages, issues, and perform various code quality checks using multiple AI providers. It supports OpenAI, Azure OpenAI, Ollama, Claude, and Google Generative AI, giving you the flexibility to choose the best model for your needs.

![generate-commit-message](/assets/generate-commit-message.webp)

## Installation

Install `git-gpt` via pip:

```bash
pip install git+https://github.com/ShinChven/git-gpt.git
```

Upgrade:

```bash
pip install --upgrade git+https://github.com/ShinChven/git-gpt.git
```

## Development

To set up the development environment:

```bash
git clone https://github.com/ShinChven/git-gpt.git
cd git-gpt
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Project Structure

The project is organized as follows:

- `git_gpt/main.py`: The main entry point of the CLI application.
- `git_gpt/__init__.py`: Initializes the package and defines the version.
- `git_gpt/config_command.py`: Handles the configuration command.
- `git_gpt/commit_command.py`: Implements the commit message generation.
- `git_gpt/issue_command.py`: Manages the issue creation functionality.
- `git_gpt/quality_command.py`: Performs quality checks on code changes.
- `git_gpt/changelog_command.py`: Generates changelogs based on commits.
- `git_gpt/ask_command.py`: Allows asking custom questions about code diffs.
- `git_gpt/ai_client.py`: Handles API requests to multiple AI providers.

Each command is implemented in its own file for better organization and maintainability.

## Configuration

Before using `git-gpt`, you'll need to configure it with your API settings. For a step-by-step guided configuration, use the following command:

```bash
git-gpt config
```

This command will prompt you for each configuration setting, making the process easier and more user-friendly.

To configure a new model or update an existing one using a single command (all options are mandatory):

```bash
git-gpt config --alias MODEL_ALIAS --model_name MODEL_NAME --provider PROVIDER --key API_KEY --api_base API_BASE
```

- `--alias`: A unique name for the model configuration
- `--model_name`: The name of the model (e.g., "gpt-4" for OpenAI, "claude-3-sonnet-20240229" for Claude, "gemini-1.5-pro" for Google Generative AI)
- `--provider`: The provider of the model (e.g., "openai", "azure-openai", "ollama", "claude", or "google-generativeai")
- `--key`: The API key (optional, depending on the provider)
- `--api_base`: The API base URL (optional, defaults to https://api.anthropic.com for Claude)

If you don't provide all options using the single command method, you'll be prompted to enter the missing information.

### Setting the Default Model

To set the default model:

```bash
git-gpt set-default MODEL_ALIAS
```

### Deleting a Model Configuration

To delete a model configuration:

```bash
git-gpt delete-model MODEL_ALIAS
```

### Showing All Configured Models

To display all configured models with their provider and masked API key:

```bash
git-gpt show-models
```

## Supported AI Providers

Git-GPT supports multiple AI providers, allowing you to choose the one that best fits your needs. The supported providers are:

1. **OpenAI**: Use models like GPT-3 and GPT-4.
2. **Azure OpenAI**: Access OpenAI models through Microsoft's Azure platform.
3. **Ollama**: An open-source, locally hosted language model.
4. **Claude (Anthropic)**: Use models like Claude-3.
5. **Google Generative AI**: Access models like Gemini.

Each provider may have specific requirements for model names and API configurations. When configuring a new model, make sure to use the correct provider name and follow any provider-specific instructions.

## Ollama Support

Git-GPT now supports Ollama, an open-source, locally hosted language model. This allows you to use Git-GPT without relying on external API services.

### Setting up Ollama:

1. Install and set up Ollama on your local machine (visit [Ollama's website](https://ollama.ai/) for instructions).
2. Pull the desired model(s) using Ollama's CLI (e.g., `ollama pull gemma2`).

### Configuring Git-GPT for Ollama:

To use Ollama with Git-GPT, configure it as follows:

```bash
git-gpt config --api-type ollama --ollama-base http://localhost:11434 --model <MODEL_NAME>
```

Replace `<MODEL_NAME>` with the model you've pulled in Ollama (e.g., llama2, codellama, mistral, etc.).

### Default Model:

The default model for Ollama in Git-GPT is set to 'gpt-4o-mini'. You can change this by specifying a different model during configuration or when running commands.

### Using Ollama:

Once configured, you can use Git-GPT with Ollama just like you would with OpenAI. All commands (commit, issue, quality, changelog, ask) will automatically use your Ollama configuration.

Note: When using Ollama, you don't need to provide an API key.

## Usage

### Generating Commit Messages

Stage all changes and generate a commit message:

```bash
git-gpt commit [--lang <LANGUAGE>] [--model <MODEL>] [--run-dry]
```

Options:

- `--lang`: Target language for the generated message (default is 'en').
- `--model`: The model to use for generating messages (default is set in config).
- `--run-dry`: Print the generated message without committing.

### Creating Issues

To create an issue based on the diffs of the latest commit(s), run:

```bash
git-gpt issue [--lang <LANGUAGE>] [--model <MODEL>] [--max-tokens <MAX_TOKENS>] [--commit-range <COMMIT_RANGE>]
```

Options:

- `--lang`: Target language for the generated message (default is 'en').
- `--model`: The model to use for generating messages (default is set in config).
- `--max-tokens`: The maximum number of tokens to use for the issue prompt (overrides the configured value).
- `--commit-range`: The range of commits to consider for generating the issue.

### Performing a Quality Check

To perform a quality check on the diffs of the latest commit(s), run:

```bash
git-gpt quality [--lang <LANGUAGE>] [--model <MODEL>] [--max-tokens <MAX_TOKENS>] [--commit-range <COMMIT_RANGE>]
```

Options:

- `--lang`: Target language for the generated message (default is 'en').
- `--model`: The model to use for generating messages (default is set in config).
- `--max-tokens`: The maximum number of tokens to use for the quality check prompt (overrides the configured value).
- `--commit-range`: The range of commits to consider for the quality check.

### Generating a Changelog

To generate a changelog based on the diffs of the latest commit(s), run:

```bash
git-gpt changelog [--lang <LANGUAGE>] [--model <MODEL>] [--max-tokens <MAX_TOKENS>] [--commit-range <COMMIT_RANGE>]
```

Options:

- `--lang`: Target language for the generated changelog (default is 'en').
- `--model`: The model to use for generating the changelog (default is set in config).
- `--max-tokens`: The maximum number of tokens to use for the changelog prompt (overrides the configured value).
- `--commit-range`: The range of commits to consider for generating the changelog.

### Asking a Custom Question

To ask a custom question about the code diffs, run:

```bash
git-gpt ask --question <YOUR_QUESTION> [--model <MODEL>] [--commit-range <COMMIT_RANGE>]
```

Options:

- `--question`: The question to ask about the code diffs.
- `--model`: The model to use for generating the response (default is set in config).
- `--commit-range`: The range of commits to consider when forming the response.

## Trouble Shooting

### aiohttp

If you encounter any issues concerning `aiohttp`, please try to downgrade python to 3.11, as this issue is reported with python 3.12:

```log
ERROR: Could not build wheels for aiohttp, which is required to install pyproject.toml-based projects
```

## Disclaimer

- Content generated by this tool is not guaranteed to be correct. You should always review and edit the generated content before committing.

## Contributing

Feel free to fork the repository, create a feature branch, and open a Pull Request.

## License

[MIT License](LICENSE)
