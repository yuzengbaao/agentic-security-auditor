"""Vertex AI client for Gemini 1.5 Pro/Flash inference."""

import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "gen-lang-client-0679032909"
LOCATION = "us-central1"
DEFAULT_MODEL = "gemini-1.5-flash-002"
AUDIT_MODEL = "gemini-1.5-pro-002"


class VertexClient:
    """Vertex AI client with lazy initialization."""
    
    _initialized = False
    
    def __init__(self):
        if not VertexClient._initialized:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.flash_model = GenerativeModel(DEFAULT_MODEL)
            self.pro_model = GenerativeModel(AUDIT_MODEL)
            VertexClient._initialized = True
            print(f"✅ Vertex AI: project={PROJECT_ID}")
    
    def audit_contract(self, code: str) -> str:
        """Full security audit using Gemini Pro."""
        prompt = f"""You are an expert smart contract security auditor.

## Audit Protocol
Check for: Reentrancy, access control, integer overflow, tx.origin,
timestamp dependence, unchecked calls, floating pragma.

## Contract
```solidity
{code}
```

## Report (markdown)"""
        
        try:
            return self.pro_model.generate_content(prompt).text
        except Exception as e:
            return f"❌ Audit failed: {e}"
    
    def quick_scan(self, code: str) -> str:
        """Fast scan using Gemini Flash."""
        prompt = f"""Quick security scan - list only confirmed vulnerabilities.

```solidity
{code}
```

Format: [Severity] Category: Brief description + line reference"""
        
        try:
            return self.flash_model.generate_content(prompt).text
        except Exception as e:
            return f"❌ Quick scan failed: {e}"


def get_vertex_client() -> VertexClient:
    return VertexClient()
