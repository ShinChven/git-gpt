# Git-GPT

A CLI tool to auto-generate git commit messages and issues using OpenAI's GPT-3.5 model.

## Installation

Install `git-gpt` via pip:

```bash
pip install git+https://github.com/ShinChven/git-gpt.git#egg=git-gpt
```

Upgrade:
  
```bash
pip install --upgrade git+https://github.com/ShinChven/git-gpt.git#egg=git-gpt
```

## Configuration

Before using `git-gpt`, you'll need to configure it with your OpenAI API key and other optional settings. Run the following command and follow the prompts:

```bash
git-gpt config --api-key <API_KEY>
```

### Options:
- `--api-key`: The API key to use with OpenAI.
- `--base`: The alternative OpenAI host.
- `--lang`: Target language for the generated message (default is 'en').
- `--issue-max-tokens`: The maximum number of tokens to use for the issue prompt.

## Usage

### Generating Commit Messages

To generate a commit message based on your staged changes, run:

```bash
git-gpt commit [--lang <LANGUAGE>]
```

### Creating Issues

To create an issue based on the diffs of the latest commit(s), run:

```bash
git-gpt issue [--lang <LANGUAGE>] [--max-tokens <MAX_TOKENS>] [--commit-range <COMMIT_RANGE>]
```

### Options:
- `--lang`: Target language for the generated message (default is 'en').
- `--max-tokens`: The maximum number of tokens to use for the issue prompt.
- `--commit-range`: The range of commits to consider for generating the issue.

## Trouble Shooting

### aiohttp

If you encounter any issues concerning `aiohttp`, please try to downgrade python to 3.11, I encountered this issue when using python 3.12:

```log
ERROR: Could not build wheels for aiohttp, which is required to install pyproject.toml-based projects
```

## Contributing

Feel free to fork the repository, create a feature branch, and open a Pull Request.

## License

[MIT License](LICENSE)
