"""
LLM Engine supporting multiple providers (OpenAI, Anthropic)
"""

import os
import asyncio
from typing import Optional, Dict, Any, Literal
import aiohttp
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    latency_ms: float


class LLMEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.primary_provider = config.get('primary', 'openai')
        self.fallback_provider = config.get('fallback', 'anthropic')
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY')
        }
        self.semaphore = asyncio.Semaphore(config.get('max_concurrent', 5))
        
    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000, json_mode: bool = False) -> str:
        async with self.semaphore:
            try:
                response = await self._call_provider(self.primary_provider, prompt, temperature, max_tokens, json_mode)
                return response.content
            except Exception as e:
                print(f"Primary failed: {e}, trying fallback...")
                response = await self._call_provider(self.fallback_provider, prompt, temperature, max_tokens, json_mode)
                return response.content
    
    async def generate_json(self, prompt: str) -> Dict[str, Any]:
        response = await self.generate(prompt + "\n\nRespond with valid JSON only.", temperature=0.1, json_mode=True)
        import json
        return json.loads(response)
    
    async def _call_provider(self, provider: Literal['openai', 'anthropic'], prompt: str, temperature: float, max_tokens: int, json_mode: bool) -> LLMResponse:
        if provider == 'openai':
            return await self._call_openai(prompt, temperature, max_tokens, json_mode)
        elif provider == 'anthropic':
            return await self._call_anthropic(prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_openai(self, prompt: str, temperature: float, max_tokens: int, json_mode: bool) -> LLMResponse:
        import time
        start = time.time()
        
        headers = {
            "Authorization": f"Bearer {self.api_keys['openai']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4-turbo-preview",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as resp:
                data = await resp.json()
                content = data['choices'][0]['message']['content']
                tokens = data['usage']['total_tokens']
                return LLMResponse(content=content, model="gpt-4-turbo-preview", tokens_used=tokens, latency_ms=(time.time() - start) * 1000)
    
    async def _call_anthropic(self, prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        import time
        start = time.time()
        
        headers = {
            "x-api-key": self.api_keys['anthropic'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload) as resp:
                data = await resp.json()
                content = data['content'][0]['text']
                tokens = data['usage']['input_tokens'] + data['usage']['output_tokens']
                return LLMResponse(content=content, model="claude-3-opus-20240229", tokens_used=tokens, latency_ms=(time.time() - start) * 1000)
