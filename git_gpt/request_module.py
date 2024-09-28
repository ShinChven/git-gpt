from typing import Dict, Any
import json
import requests
from openai import OpenAI

class RequestModule:
    def __init__(self, config: Dict[str, Any]):
        self.api_type = config.get('api_type', 'openai')
        self.api_key = config.get('api_key')
        
        if self.api_type == 'openai':
            self.api_base = config.get('base', 'https://api.openai.com/v1')
            self.client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        elif self.api_type == 'ollama':
            self.api_base = config.get('ollama_base', 'http://localhost:11434')
        else:
            raise ValueError(f"Unsupported API type: {self.api_type}")

    def send_request(self, messages: list, model: str, temperature: float = 0.7) -> Dict[str, Any]:
        if self.api_type == "openai":
            return self._send_openai_request(messages, model, temperature)
        elif self.api_type == "ollama":
            return self._send_ollama_request(messages, model, temperature)
        else:
            raise ValueError(f"Unsupported API type: {self.api_type}")

    def _send_openai_request(self, messages: list, model: str, temperature: float) -> Dict[str, Any]:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            response = json.loads(response.model_dump_json())
            print(f"OpenAI API Response: {response}")  # Debug print
            return response
        except Exception as e:
            print(f"Error in OpenAI API request: {e}")
            raise

    def _send_ollama_request(self, messages: list, model: str, temperature: float) -> Dict[str, Any]:
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        try:
            response = requests.post(f"{self.api_base}/api/chat", json=data)
            response.raise_for_status()
            content = response.content.decode('utf-8')
            print(f"Ollama API Response: {content}")  # Debug print
            return self._process_ollama_response(content)
        except requests.exceptions.RequestException as e:
            print(f"Error in Ollama API request: {e}")
            if response is not None:
                print(f"Response content: {response.content}")
            raise

    def _process_ollama_response(self, content: str) -> Dict[str, Any]:
        lines = content.strip().split('\n')
        full_response = ""
        for line in lines:
            try:
                json_obj = json.loads(line)
                if 'response' in json_obj:
                    full_response += json_obj['response']
                if json_obj.get('done', False):
                    break
            except json.JSONDecodeError:
                print(f"Error decoding JSON line: {line}")
                continue
        
        return {"response": full_response.strip()}

    def get_response_content(self, response: Dict[str, Any]) -> str:
        if self.api_type == "openai":
            return response['choices'][0]['message']['content']
        elif self.api_type == "ollama":
            return response['response']
        else:
            raise ValueError(f"Unsupported API type: {self.api_type}")
