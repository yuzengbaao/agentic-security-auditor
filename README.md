# Agentic Security Auditor

**AI-powered smart contract security auditing system for Google Cloud Rapid Agent Hackathon 2026.**

[![GitHub](https://img.shields.io/badge/GitHub-yuzengbaao-blue)](https://github.com/yuzengbaao/agentic-security-auditor)

---

## 🎯 Overview

Agentic Security Auditor is a multi-agent system that combines **static analysis** (Slither), **AI-powered inference** (OpenRouter DeepSeek), and **blockchain data fetching** (Etherscan API V2) to deliver production-grade smart contract security audits.

**Key Innovation**: Multi-model AI + deterministic static analysis — AI explains vulnerabilities while Slither guarantees discovery accuracy.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/yuzengbaao/agentic-security-auditor.git
cd agentic-security-auditor

# Install dependencies
pip install -r requirements.txt

# Run audit on local contract
python main.py --file examples/vulnerable.sol

# Run audit on deployed contract
python main.py --address 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D --chain ethereum
```

---

## 📊 Features

| Feature | Technology | Status |
|---------|-----------|--------|
| **Static Analysis** | Slither (Trail of Bits) | ✅ Production-grade |
| **AI Audit** | OpenRouter DeepSeek v3.1 | ✅ Active |
| **Contract Fetching** | Etherscan API V2 | ✅ 6 chains |
| **Vulnerability DB** | SWC Registry | ✅ 10 categories |
| **Multi-Model** | Claude/GPT/Gemini/DeepSeek | ⚠️ DeepSeek only (Claude/GPT/Gemini 403) |
| **Cloud Deploy** | Cloud Run ✅

---

## 🏗️ Architecture

```
Input (File / Code / Address)
  ↓
┌─────────────────┐
│  Task Receiver  │  Parse input type
└─────────────────┘
  ↓
┌─────────────────┐
│ Static Analysis │  Slither control/data flow
└─────────────────┘
  ↓
┌─────────────────┐
│ Vulnerability DB│  SWC mapping + CWE refs
└─────────────────┘
  ↓
┌─────────────────┐
│  AI Auditor     │  DeepSeek v3.1 — fix suggestions
└─────────────────┘
  ↓
┌─────────────────┐
│ Report Generator│  Markdown with severity scoring
└─────────────────┘
  ↓
Output: audit_report.md
```

---

## 📸 Screenshots

### Terminal Execution
```bash
$ python main.py --file examples/vulnerable.sol

🚀 Agentic Security Auditor (Production)
   Contract size: 2088 chars

🔍 Phase 1: Static Pattern Analysis
   Found 4 issues (Risk Score: 26)

🔬 Phase 2: Slither Control Flow Analysis
   Found 8 issues via Slither

🤖 Phase 3: AI-Powered Audit (OpenRouter)
   AI report: 4499 chars

📊 Phase 4: Report Generation

✅ Report saved to: audit_report.md
📊 Final Risk Score: 93/100
🔍 Static findings: 4
🔬 Slither findings: 8
🤖 AI audit: ENABLED
```

### Sample Report Output
- **Executive Summary**: Risk Score 93/100, 12 total findings
- **Critical Findings**: Reentrancy, Unprotected selfdestruct
- **SWC References**: SWC-107 (Reentrancy), SWC-106 (Suicidal)
- **Fix Code**: Checks-Effects-Interactions pattern + ReentrancyGuard

---

## 🛠️ Technology Stack

| Component | Tool |
|-----------|------|
| Framework | Google ADK v1.32 |
| AI Models | OpenRouter (DeepSeek v3.1) |
| Static Analysis | Slither 0.11.5 |
| Fuzzing | Echidna 2.2.5 (module ready) |
| Blockchain | Etherscan API V2 |
| Language | Python 3.10 |
| Deployment | Cloud Run ✅

---

## 📋 Usage Examples

### Example 1: Local File Audit
```bash
python main.py --file examples/vulnerable.sol --output report.md
```

### Example 2: Live Contract Audit
```bash
python main.py --address 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D --chain ethereum
```

### Example 3: Skip AI (Static + Slither only)
```bash
python main.py --file contract.sol --no-ai
```

---

## 🧪 Testing

```bash
pytest tests/test_audit_tools.py -v
```

**Results**: 7/7 tests passing

---

## 🏆 Hackathon Context

**Event**: Google Cloud Rapid Agent Hackathon 2026  
**Track**: Building Agents for Real-World Challenges  
**Prize Pool**: $60,000  
**Submission Opens**: May 5, 2026 18:00 UTC  
**Deadline**: Jun 12, 2026  

**Judging Criteria** (expected):
- Innovation and creativity
- Technical implementation
- Real-world applicability
- Demo quality

---

## 📦 GitHub Release

**Latest**: [v0.2.1-audit-models](https://github.com/yuzengbaao/agentic-security-auditor/releases/tag/v0.2.1-audit-models)

Download test data package:
```bash
wget https://github.com/yuzengbaao/agentic-security-auditor/releases/download/v0.2.1-audit-models/audit_test_data_package.zip
```

---

## ⚠️ Known Issues

| Issue | Status | Workaround |
|-------|--------|------------|
| Claude/GPT/Gemini 403 | 🔴 | Use DeepSeek v3.1 |
| Cloud Run ✅
| Echidna needs test props | 🟡 | Module ready, not integrated |

---

## 🔮 Roadmap

- [x] Project skeleton + GitHub repo
- [x] Core Agent development (3-agent pipeline)
- [x] OpenRouter integration
- [x] Etherscan API V2 integration
- [x] Slither production pipeline
- [x] 4-model comparison testing
- [ ] Cloud Run ✅
- [ ] Demo video recording
- [ ] DevPost submission page

---

## 📄 License

MIT License — See [LICENSE](LICENSE)

---

**Built with ❤️ by 虾总 (Xia Zong) for Google Cloud Rapid Agent Hackathon 2026**

---

## ☁️ Cloud Run Deployment

**Service URL**: https://agentic-security-auditor-270892092095.us-central1.run.app

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | Service info |
| `/audit` | POST | Audit smart contract (JSON body: `{code: "..."}` or `{address: "0x...", chain: "ethereum"}`) |

### Example: Audit via API

```bash
curl -X POST https://agentic-security-auditor-270892092095.us-central1.run.app/audit \
  -H "Content-Type: application/json" \
  -d '{"code":"pragma solidity ^0.8.0; contract Test { ... }"}'
```

### Response Format

```json
{
  "status": "success",
  "risk_score": 21,
  "total_findings": 7,
  "results": {
    "static": { "findings": [...], "risk_score": 21 },
    "slither": { "success": true, "findings": [...] },
    "ai": { "enabled": true, "report": "..." }
  }
}
```
