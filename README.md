# Agentic Security Auditor

**AI-Powered Smart Contract & Code Security Scanner**

Built for [Google Cloud Rapid Agent Hackathon 2026](https://rapid-agent.devpost.com/) — *Building Agents for Real-World Challenges*

---

## 🎯 What It Does

Agentic Security Auditor is an autonomous AI agent that performs **end-to-end smart contract security audits**:

1. **Input**: Contract code (Solidity/Vyper), GitHub repo, or deployed address
2. **Analysis**: Multi-layered security scanning — static analysis + dynamic detection + browser-based interaction verification
3. **Output**: Structured audit report with severity ratings, proof-of-concept traces, and remediation code

### Key Differentiators
- 🧠 **Multi-Agent Architecture**: Task Receiver → Security Auditor → Report Generator (3 agents orchestrated via Google ADK)
- 🔗 **MCP Integration**: Plugs into existing audit toolchains (Slither, Mythril, custom scripts via browser automation)
- 🌐 **Browser-Powered**: Uses anti-detection browser (v3.0) for live vulnerability verification on testnets
- 📊 **Evidence-Anchored**: Every finding includes reproducible traces, not just pattern matching

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Task Receiver  │────▶│ Security Auditor │────▶│ Report Generator│
│    (ADK Agent)  │     │   (ADK Agent)    │     │   (ADK Agent)   │
└────────┬────────┘     └────────┬─────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│ Browser v3.0    │     │ Audit Toolchain  │
│ (Code fetch,    │     │ (Static analysis,│
│  TX simulation) │     │  Reentrancy check│
└─────────────────┘     │  Access control) │
                         └──────────────────┘
```

**Core Stack**: Google Vertex AI Agent Builder + ADK + Gemini 1.5 Pro + MCP + Cloud Run

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`)
- GCP project with Vertex AI API enabled

### Installation
```bash
# Clone repo
git clone https://github.com/yuzengbaao/agentic-security-auditor.git
cd agentic-security-auditor

# Install dependencies
pip install -r requirements.txt

# Set up GCP authentication
gcloud auth application-default login

# Run the agent
python src/agent.py --contract-code ./examples/vulnerable.sol
```

### Demo
```bash
# Audit a sample contract
python src/agent.py --github-repo https://github.com/example/vulnerable-contract

# Output: structured_report.md with findings + remediation
```

---

## 📁 Project Structure

```
agentic-security-auditor/
├── src/
│   ├── agent.py              # ADK multi-agent orchestrator
│   ├── tools/
│   │   ├── audit_tools.py    # Core security analysis tools
│   │   ├── browser_tools.py  # Browser automation integration
│   │   └── mcp_tools.py      # MCP protocol adapters
│   └── prompts/
│       └── auditor_prompt.md # Core agent prompt
├── tests/
│   └── test_audit_tools.py   # Test suite (pytest)
├── docs/
│   ├── architecture.md       # Technical design
│   └── deployment.md         # Cloud Run deployment guide
├── examples/
│   └── vulnerable.sol        # Demo contract for testing
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent Framework** | Google ADK (Agent Development Kit) | Multi-agent orchestration |
| **LLM** | Gemini 1.5 Pro/Ultra | Code understanding, vulnerability reasoning |
| **Agent Builder** | Vertex AI Agent Builder | Visual prompt management, tool registry |
| **MCP** | Model Control Plane | External tool integration |
| **Browser** | Playwright + anti-detection (v3.0) | Live contract interaction, TX simulation |
| **Static Analysis** | Slither, Mythril (via subprocess) | Solidity vulnerability detection |
| **Deployment** | Cloud Run | Agent service hosting |
| **Storage** | Cloud Storage | Audit reports, screenshots |

---

## 🎥 Demo Video

*[Coming soon — 3-minute end-to-end demo]*

Planned flow:
1. Input: Paste vulnerable Solidity code
2. Analysis: Agent runs static analysis + browser verification
3. Output: Markdown report with Critical/High/Medium findings
4. Bonus: One-click remediation code generation

---

## 📄 License

MIT License — Built for Google Cloud Rapid Agent Hackathon 2026

---

**Author**: [zengbao yu](https://devpost.com/yuzengbaao) | GitHub: [@yuzengbaao](https://github.com/yuzengbaao)

**Related Projects**: [AuditCraft](https://devpost.com/software/auditcraft-smart-contract-security-sandbox) | [FIND EVIL!](https://devpost.com/software/self-correcting-dfir-agent-with-evidence-anchored-findings)
