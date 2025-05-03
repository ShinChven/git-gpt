import json
from openai import OpenAI, AzureOpenAI
import requests
import anthropic
from google import genai
from google.genai import types # Import types

class AIClient:
    def __init__(self, config):
        self.config = config

    def request(self, messages, model_alias=None, max_tokens=None):
        if not model_alias:
            model_alias = self.config.get('default_model')
            if not model_alias:
                raise ValueError("No default model specified in configuration. Please run git-gpt set-default to set default model or run git-gpt config to add model configuration.")

        if model_alias not in self.config.get('models', {}):
            raise ValueError(f"Model alias '{model_alias}' not found in configuration")

        model_config = self.config['models'][model_alias]
        provider = model_config.get('provider')

        if not provider:
            raise ValueError(f"Provider not specified for model alias '{model_alias}'")

        print(f"Requesting content from model '{model_alias}' using provider '{provider}'")

        if provider == 'openai':
            return self._openai_request(messages, model_config, max_tokens)
        elif provider == 'azure-openai':
            return self._azure_openai_request(messages, model_config, max_tokens)
        elif provider == 'ollama':
            return self._ollama_request(messages, model_config, max_tokens)
        elif provider == 'claude':
            return self._claude_request(messages, model_config, max_tokens)
        elif provider == 'google-generativeai':
            return self._google_generativeai_request(messages, model_config, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _openai_request(self, messages, model_config, max_tokens):
        if 'key' not in model_config or not model_config['key']:
            raise ValueError("API key not provided for OpenAI")

        api_base = model_config.get('api_base')
        if not api_base:
            api_base = 'https://api.openai.com/v1'

        openAIClient = OpenAI(api_key=model_config['key'], base_url=api_base)
        response = openAIClient.chat.completions.create(
                model=model_config['model_name'],
                messages=messages,
                stream=False,
                max_tokens=max_tokens)
        return response.choices[0].message.content

    def _azure_openai_request(self, messages, model_config, max_tokens):
        if 'key' not in model_config or not model_config['key']:
            raise ValueError("API key not provided for Azure OpenAI")

        if 'api_base' not in model_config or not model_config['api_base']:
            raise ValueError("API base URL not provided for Azure OpenAI")

        if 'model_name' not in model_config or not model_config['model_name']:
            raise ValueError("Azure deployment name not provided for Azure OpenAI, please set it as 'model_name' in the configuration")

        azureOpenAIClient = AzureOpenAI(
            api_key=model_config['key'],
            api_version="2023-07-01-preview",
            azure_endpoint=model_config['api_base']
        )

        response = azureOpenAIClient.chat.completions.create(
            model=model_config['model_name'],
            messages=messages,
            stream=False,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    def _ollama_request(self, messages, model_config, max_tokens):
        api_base = model_config.get('api_base', 'http://localhost:11434')
        if not api_base:
            api_base = 'http://localhost:11434'
        api_base += '/api/chat'

        request_data = {
            "model": model_config['model_name'],
            "messages": messages,
        }
        if max_tokens:
            request_data["options"] = {"num_predict": max_tokens}

        try:
            response = requests.post(api_base, json=request_data)
            response.raise_for_status()
            content = response.content.decode('utf-8')
            full_response = ""
            for line in content.strip().split('\n'):
                try:
                    json_obj = json.loads(line)
                    if 'message' in json_obj and 'content' in json_obj['message']:
                        full_response += json_obj['message']['content']
                    if json_obj.get('done', False):
                        break
                except json.JSONDecodeError:
                    print(f"Error decoding JSON line: {line}")
                    continue
            return full_response.strip()

        except requests.exceptions.RequestException as e:
            print(f"Error in Ollama API request: {e}")
            if response is not None:
                print(f"Response content: {response.content}")
            raise

    def _claude_request(self, messages, model_config, max_tokens):
        if 'key' not in model_config or not model_config['key']:
            raise ValueError("API key not provided for Claude")

        client = anthropic.Anthropic(api_key=model_config['key'])

        # Convert messages to Anthropic's format
        anthropic_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]

        response = client.messages.create(
            model=model_config['model_name'],
            max_tokens=max_tokens or model_config.get('max_tokens', 1024),
            messages=anthropic_messages
        )
        return response.content

    def _google_generativeai_request(self, messages, model_config, max_tokens):
        if 'key' not in model_config or not model_config['key']:
            raise ValueError("API key not provided for Google Generative AI")

        # Keep the original client instantiation
        client = genai.Client(api_key=model_config['key'])
        model_name = model_config['model_name']

        system_instruction = None
        chat_messages_parts = []
        for msg in messages:
            if msg['role'] == 'system':
                # Extract system instruction
                system_instruction = msg['content']
            else:
                # Format other messages for the prompt string
                chat_messages_parts.append(f"{msg['role']}: {msg['content']}")

        # Combine non-system messages into a single prompt string
        prompt = "\n".join(chat_messages_parts)

        # Prepare configuration dictionary
        config_dict = {
            'max_output_tokens': max_tokens or None,
            'system_instruction': system_instruction or None,
            # Add other config parameters from model_config if needed, e.g.:
            # 'top_k': model_config.get('top_k'),
            # 'top_p': model_config.get('top_p'),
            # 'temperature': model_config.get('temperature'),
        }

        # Remove None values from config_dict as GenerateContentConfig might not accept them
        config_dict = {k: v for k, v in config_dict.items() if v is not None}

        # Create GenerateContentConfig object
        generation_config = types.GenerateContentConfig(**config_dict)

        # Use the generate_content call with the config object
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=generation_config # Pass the config object here
        )
        # Keep the original return statement
        return response.text
