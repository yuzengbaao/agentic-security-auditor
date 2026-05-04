"""OpenRouter client — DeepSeek v3.1 as primary model.

Note (2026-05-04): Claude Opus 4.7 / Gemini 2.5 Pro / GPT 5.5 
all return 403 "violation of provider Terms Of Service".
DeepSeek v3.1 is the only working model on OpenRouter currently.
"""

import os
from typing import Optional, Dict, Any
import requests

API_KEY_PATH = "/root/.openrouter_api_key"
BASE_URL = "https://openrouter.ai/api/v1"

# DeepSeek v3.1 — current only working model
DEFAULT_MODEL = "deepseek/deepseek-chat-v3.1"
AUDIT_MODEL = "deepseek/deepseek-chat-v3.1"


class OpenRouterClient:
    """OpenRouter client with lazy initialization."""
    
    _initialized = False
    _instance: Optional["OpenRouterClient"] = None
    
    def __new__(cls) -> "OpenRouterClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if OpenRouterClient._initialized:
            return
        
        if os.path.exists(API_KEY_PATH):
            with open(API_KEY_PATH) as f:
                self.api_key = f.read().strip()
        else:
            self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not found")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yuzengbaao/agentic-security-auditor",
            "X-Title": "Agentic Security Auditor",
        }
        
        OpenRouterClient._initialized = True
        print("✅ OpenRouter client initialized (DeepSeek v3.1)")
    
    def _chat(self, messages: list, model: str = DEFAULT_MODEL, max_tokens: int = 4000, temperature: float = 0.1) -> str:
        """Send chat completion request."""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                return f"❌ Empty response: {data}"
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                return "❌ Rate limit exceeded. Please wait."
            if e.response.status_code == 403:
                return f"❌ API error 403: Provider Terms of Service violation. Model may be unavailable."
            return f"❌ API error {e.response.status_code}: {e.response.text[:200]}"
        except Exception as e:
            return f"❌ Request failed: {type(e).__name__}: {e}"
    
    def audit_contract(self, code: str, model: str = AUDIT_MODEL) -> str:
        """Run full security audit using DeepSeek v3.1."""
        system_prompt = """You are an expert smart contract security auditor.

## Audit Protocol
Check for: Reentrancy, access control, integer overflow, tx.origin,
timestamp dependence, unchecked calls, floating pragma.

## Output Format
Return a structured markdown audit report with:
- Executive Summary (Risk Score, Finding counts)
- Each finding: ID, Severity, Category, Description, Evidence, Impact, Recommendation with code fix

## Rules
- Every claim needs a code reference (function/line)
- Recommendations must include specific fix code
- Never fabricate vulnerabilities — mark uncertain as "Suspected"
- Match Immunefi/Code4rena quality standards"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Audit this smart contract:\n\n```solidity\n{code}\n```\n\nProvide a full audit report."},
        ]
        
        return self._chat(messages, model=model, max_tokens=8000, temperature=0.1)
    
    def quick_scan(self, code: str, model: str = DEFAULT_MODEL) -> str:
        """Fast scan using DeepSeek v3.1."""
        messages = [
            {"role": "system", "content": "You are a security scanner. List ONLY confirmed vulnerabilities with severity and brief description."},
            {"role": "user", "content": f"Quick scan this contract:\n\n```solidity\n{code}\n```\n\nFormat: [Severity] Category: Brief description + line reference"},
        ]
        
        return self._chat(messages, model=model, max_tokens=2000, temperature=0.1)


def get_openrouter_client() -> OpenRouterClient:
    return OpenRouterClient()


if __name__ == "__main__":
    client = get_openrouter_client()
    
    test_code = """
    contract Test {
        mapping(address => uint256) public balances;
        function withdraw() public {
            uint256 amount = balances[msg.sender];
            (bool success,) = msg.sender.call{value: amount}("");
            require(success, "Transfer failed");
            balances[msg.sender] = 0;
        }
    }
    """
    
    print("\n=== Quick Scan ===")
    result = client.quick_scan(test_code)
    print(result[:500])
    
    print("\n=== Full Audit ===")
    result = client.audit_contract(test_code)
    print(result[:500])
