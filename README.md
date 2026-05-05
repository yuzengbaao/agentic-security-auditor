# Agentic Security Auditor v2.0

**Multi-Agent Smart Contract Security Auditing System powered by Google ADK & Vertex AI.**

[![GitHub](https://img.shields.io/badge/GitHub-yuzengbaao-blue)](https://github.com/yuzengbaao/agentic-security-auditor)
[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Live-green)](https://agentic-security-auditor-270892092095.us-central1.run.app)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎯 Overview

Agentic Security Auditor v2.0 is a **production-grade multi-agent system** built with **Google Agent Development Kit (ADK)** and **Vertex AI Gemini**. It orchestrates 5 specialized AI agents to deliver comprehensive smart contract security audits combining deterministic static analysis with deep AI-powered reasoning.

**Key Innovation**: ADK multi-agent orchestration — each agent specializes in one audit phase, coordinated by a central orchestrator for maximum accuracy and depth.

---

## 🚀 Quick Start

### Cloud Run (Live)
```bash
# Audit a deployed contract
curl -X POST https://agentic-security-auditor-270892092095.us-central1.run.app/v2/audit \
  -H "Content-Type: application/json" \
  -d '{"address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", "chain": "ethereum"}'

# Audit raw code
curl -X POST https://agentic-security-auditor-270892092095.us-central1.run.app/v2/audit/code \
  -H "Content-Type: application/json" \
  -d '{"code": "pragma solidity ^0.8.0; contract Test { ... }"}'
```

### Local Development
```bash
# 1. Clone repository
git clone https://github.com/yuzengbaao/agentic-security-auditor.git
cd agentic-security-auditor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT=gen-lang-client-0679032909
export GOOGLE_CLOUD_LOCATION=us-central1

# 4. Run ADK multi-agent audit
python src/agent_v2.py --address 0x... --chain ethereum
python src/agent_v2.py --file examples/vulnerable.sol
```

---

## 🏗️ ADK v2.0 Architecture

```
User Input (Address / Code / File)
  ↓
┌──────────────────┐
│ CoordinatorAgent   │  Route to appropriate pipeline
└──────────────────┘
  ↓
┌──────────────────┐
│ ScannerAgent     │  Fetch contract from Etherscan
└──────────────────┘
  ↓
┌──────────────────┐
│ StaticAnalyzer   │  Pattern analysis + Slither control-flow
└──────────────────┘
  ↓
┌──────────────────┐
│ AIReviewerAgent  │  Gemini deep reasoning audit
└──────────────────┘
  ↓
┌──────────────────┐
│ ReportAgent      │  Generate Immunefi-grade report
└──────────────────┘
  ↓
Output: Professional Audit Report (Markdown)
```

### Agent Details

| Agent | Model | Role | Tools |
|-------|-------|------|-------|
| **ScannerAgent** | Gemini 2.5 Flash | Fetch contract source from blockchain | `etherscan_fetch_mcp` |
| **StaticAnalyzer** | Gemini 2.5 Flash | Pattern + Slither control-flow analysis | `static_analyze_mcp`, `slither_analyze_mcp` |
| **AIReviewer** | Gemini 2.5 Flash | Deep AI audit (business logic, subtle flaws) | `ai_audit_mcp` |
| **ReportAgent** | Gemini 2.5 Flash | Professional report generation | `calculate_risk_mcp` |
| **Coordinator** | Gemini 2.5 Flash | Orchestrate 4-stage pipeline | — |

---

## 📊 v2 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/audit` | POST | v1: Legacy audit (static + Slither + OpenRouter) |
| `/v2/audit` | POST | ADK multi-agent audit (auto-routing) |
| `/v2/audit/address` | POST | ADK audit by contract address |
| `/v2/audit/code` | POST | ADK audit by Solidity code |

### v2 Request/Response Example

**Request:**
```json
POST /v2/audit/code
{
  "code": "pragma solidity ^0.8.0; contract Test { uint public x; function set(uint _x) public { x = _x; } }"
}
```

**Response:**
```json
{
  "status": "success",
  "version": "2.0",
  "code_length": 97,
  "report": "# Security Audit Report\n\n## Executive Summary\n..."
}
```

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | Google ADK v1.32 |
| **AI Backend** | Vertex AI Gemini 2.5 Flash |
| **Fallback AI** | OpenRouter (DeepSeek v3.1) |
| **Static Analysis** | Slither 0.11.5 |
| **Blockchain** | Etherscan API V2 (6 chains) |
| **Language** | Python 3.10 |
| **Deployment** | Google Cloud Run |
| **MCP Tools** | Etherscan, Slither, OpenRouter |

---

## 🧪 Testing & Validation

### Unit Tests
```bash
pytest tests/ -v
```

### ADK Agent Test
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from agent_v2 import scanner_agent, static_analyzer_agent
print('Scanner:', scanner_agent.name, scanner_analyzer_agent.model)
print('Static:', static_analyzer_agent.name, static_analyzer_agent.model)
"
```

### API Integration Test
```bash
# Test live endpoint
curl -X POST https://agentic-security-auditor-270892092095.us-central1.run.app/v2/audit/code \
  -H "Content-Type: application/json" \
  -d '{"code":"pragma solidity ^0.8.0; contract T { uint x; function set(uint _x) public { x = _x; } }"}'

# Test vulnerable contract detection
curl -X POST https://agentic-security-auditor-270892092095.us-central1.run.app/v2/audit/code \
  -H "Content-Type: application/json" \
  -d '{"code": "'$(cat examples/vulnerable_reentrancy.sol | sed 's/"/\\"/g')'"}'
```

### Real Vulnerability Validation
The system has been validated against:
- **Reentrancy** (Critical): Detected in `examples/vulnerable_reentrancy.sol`
- **Access Control** (High): Missing `onlyOwner` modifiers
- **Integer Overflow** (Medium): Unchecked arithmetic
- **Timestamp Dependence** (Low): `block.timestamp` usage

---

## 🏆 Hackathon Context

**Event**: Google Cloud Rapid Agent Hackathon 2026  
**Track**: Building Agents for Real-World Challenges  
**Prize Pool**: $60,000  
**Status**: ✅ Submitted & Deployed  

**What Makes This Special:**
- ✅ **5-Agent ADK Pipeline**: Each agent specializes, coordinated for depth
- ✅ **Vertex AI Native**: Built on Google's Agent Platform (formerly Vertex AI)
- ✅ **MCP Integration**: Etherscan, Slither, OpenRouter as MCP tools
- ✅ **Cloud Run Live**: Production deployment with <60s audit turnaround
- ✅ **Real Vulnerability Detection**: Verified against reentrancy, access control flaws

---

## 🔮 Roadmap

- [x] ADK v2.0 5-Agent architecture
- [x] Vertex AI Gemini 2.5 Flash integration
- [x] MCP tool wrappers (Etherscan, Slither, OpenRouter)
- [x] Cloud Run deployment with v2 endpoints
- [x] Real vulnerability detection validation
- [x] DevPost submission
- [x] 3-minute demo video
- [ ] ADK Studio integration
- [ ] Agent Garden blueprint
- [ ] Real-time blockchain monitoring agent

---

## 📄 License

MIT License — See [LICENSE](LICENSE)

**Built with ❤️ by 虾总 (Xia Zong) for Google Cloud Rapid Agent Hackathon 2026**

---

## ☁️ Cloud Run Deployment

**Service URL**: https://agentic-security-auditor-270892092095.us-central1.run.app

**Current Revision**: `agentic-security-auditor-00009-mpn`

**Environment**: Vertex AI (Agent Platform) | `us-central1` | `gen-lang-client-0679032909`
