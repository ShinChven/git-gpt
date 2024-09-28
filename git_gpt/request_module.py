import os
import requests
from typing import Dict, Any, Optional

class RequestModule:
    def __init__(self, api_type: str, api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.api_type = api_type
        self.api_key = api_key
        self.api_base = api_base or "https://api.openai.com"

    def send_request(self, messages: list, model: str, temperature: float = 0.7) -> Dict[str, Any]:
        if self.api_type == "openai":
            return self._send_openai_request(messages, model, temperature)
        elif self.api_type == "ollama":
            return self._send_ollama_request(messages, model, temperature)
        else:
            raise ValueError(f"Unsupported API type: {self.api_type}")

    def _send_openai_request(self, messages: list, model: str, temperature: float) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def _send_ollama_request(self, messages: list, model: str, temperature: float) -> Dict[str, Any]:
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        response = requests.post(f"{self.api_base}/api/chat", json=data)
        response.raise_for_status()
        return response.json()