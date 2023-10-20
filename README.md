# git-gpt

A CLI tool to generate commit messages and issues based on staged Git diffs using OpenAI GPT-3.5-turbo.

## Installation

To install `git-gpt`, you can use pip:

```bash
pip install git+https://github.com/ShinChven/git-gpt.git#egg=git-gpt
```

## Configuration

Before you can start using `git-gpt`, you'll need to configure it with your OpenAI API credentials and other optional settings:

```bash
git-gpt config --api-key <your-api-key> --host <alternative-openai-host> --max-tokens <max-tokens> --lang <language>
```

- `--api-key`: Your OpenAI API key.
- `--host`: An alternative OpenAI host (optional).
- `--max-tokens`: Maximum number of tokens for the generated message (optional, default is 100).
- `--lang`: Target language for the generated message (optional, default is 'en').

Configuration will be saved to `~/.config/git-gpt/config.json`.

## Usage

### Commit

To generate a commit message for staged Git diffs:

```bash
git-gpt commit --max-tokens <max-tokens> --lang <language>
```

- `--max-tokens`: Maximum number of tokens for the generated message (optional).
- `--lang`: Target language for the generated message (optional).

### Recommit

To reset the latest commit, stage all changes, and generate a new commit message:

```bash
git-gpt recommit --max-tokens <max-tokens> --lang <language>
```

- `--max-tokens`: Maximum number of tokens for the generated message (optional).
- `--lang`: Target language for the generated message (optional).

## License

LICENSE: [MIT](/LICENSE)
