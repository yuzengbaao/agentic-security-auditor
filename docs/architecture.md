# Architecture Design: Agentic Security Auditor

## System Overview

Agentic Security Auditor is a multi-agent system built on Google ADK that performs autonomous smart contract security audits through three specialized agents.

---

## Agent Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         User Interface                                  │
│                (CLI / Web UI / DevPost Demo)                          │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Orchestrator (ADK Root Agent)                        │
│         Routes tasks + manages state + coordinates sub-agents            │
└──────────────┬────────────────────────────┬─────────────────────────────┘
               │                            │
               ▼                            ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  Task Receiver   │      │ Security Auditor │
    │    Agent         │─────▶│    Agent         │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Browser v3.0     │      │ Audit Tools      │
    │ (Code fetch)     │      │ (Static analysis)│
    └──────────────────┘      └────────┬─────────┘
                                       │
                                       ▼
                            ┌──────────────────┐
                            │ Report Generator │
                            │    Agent         │
                            └──────────────────┘
                                       │
                                       ▼
                            ┌──────────────────┐
                            │  Output (MD/HTML)  │
                            │  Cloud Storage     │
                            └──────────────────┘
```

---

## Agent Specifications

### Agent 1: Task Receiver
**Role**: Entry point + input normalization
**Model**: Gemini 1.5 Flash (fast, cheap)
**Tools**:
- `browser_fetch(url)` — Download contract source from Etherscan/Basescan
- `github_clone(repo)` — Clone repository for local analysis
- `file_read(path)` — Read local contract files
**Output**: Structured task object `{contract_type, source_code, entry_points, analysis_scope}`

### Agent 2: Security Auditor
**Role**: Core analysis engine
**Model**: Gemini 1.5 Pro (strong reasoning)
**Tools**:
- `analyze_contract_code(code)` — Pattern-based static analysis
- `check_reentrancy(code)` — Specific reentrancy checks
- `check_access_control(code)` — Permission model analysis
- `check_erc_compliance(code, standard)` — ERC-20/721/1155 validation
- `simulate_transaction(network, params)` — Fork-based verification
**Output**: List of findings `{severity, category, location, evidence, confidence}`

### Agent 3: Report Generator
**Role**: Report formatting + export
**Model**: Gemini 1.5 Flash
**Tools**:
- `generate_markdown(findings)` — Generate Markdown report
- `generate_html(findings)` — Generate HTML report
- `upload_to_gcs(path, bucket)` — Upload to Cloud Storage
**Output**: Public URL to report

---

## Data Flow

```
1. User Input
   └── "Audit contract 0x... on Base"

2. Task Receiver
   └── browser_fetch() → fetch verified source from Basescan
   └── parse_abi() → extract function signatures
   └── classify_contract() → ERC-20 / DeFi / Governance
   └── emit: TaskReadyEvent

3. Security Auditor (parallel sub-tasks)
   ├── Thread A: static_analysis()
   │   └── analyze_contract_code() → pattern findings
   ├── Thread B: reentrancy_check()
   │   └── check_reentrancy() → call graph analysis
   ├── Thread C: access_control_check()
   │   └── check_access_control() → permission map
   └── Thread D: dynamic_verify()
       └── simulate_transaction() → fork PoC (for Critical/High only)

4. Report Generator
   └── aggregate_findings() → deduplicate + sort by severity
   └── generate_markdown() → formatted report
   └── upload_to_gcs() → public URL
   └── emit: ReportReadyEvent

5. Orchestrator
   └── return: {report_url, summary, risk_score}
```

---

## MCP Integration

### Tool Registry

| Tool Name | Type | Input | Output | Cost |
|-----------|------|-------|--------|------|
| `browser_fetch` | Browser | URL | Source code + metadata | Low |
| `analyze_contract_code` | Local | Solidity code | Findings list | Free |
| `simulate_transaction` | RPC | Network + TX params | TX receipt + traces | Medium |
| `generate_report` | Local | Findings | Markdown/HTML | Free |
| `upload_to_gcs` | Cloud | File path | Public URL | Low |

### MCP Server (Local)
```python
# mcp_server.py
from google.adk.tools import mcp_tool

@mcp_tool(name="analyze_contract_code")
def analyze_contract_code(code: str) -> dict:
    """Analyze Solidity code for vulnerabilities"""
    findings = static_analyzer.run(code)
    return {"findings": findings, "risk_score": calculate_score(findings)}
```

---

## Deployment Architecture

### Development (Local)
- ADK agents running locally
- Tools executed via subprocess (Slither, Mythril)
- Browser automation via Playwright (headed, persistent profile)

### Production (Cloud Run)
- Containerized agent service
- Vertex AI Agent Builder for prompt management
- Cloud Storage for report persistence
- Secret Manager for API keys (Etherscan, RPC endpoints)

```
┌──────────────────┐
│   Cloud Run      │
│   ┌──────────┐   │
│   │ ADK Agent│   │
│   │ Service  │   │
│   └────┬─────┘   │
│        │         │
│   ┌────┴─────┐   │
│   │  Tools   │   │
│   │ Container│   │
│   └────┬─────┘   │
└────────┼─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│Vertex  │ │ Cloud    │
│AI      │ │ Storage  │
└────────┘ └──────────┘
```

---

## State Management

### Shared State (ADK Session)
```json
{
  "task": {
    "contract_address": "0x...",
    "network": "base",
    "source_code": "// ...",
    "contract_type": "ERC-20"
  },
  "findings": [
    {"severity": "Critical", "category": "Reentrancy", ...}
  ],
  "report": {
    "url": "https://storage.googleapis.com/...",
    "risk_score": 78,
    "total_findings": 12
  }
}
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Analysis latency (static) | < 30s |
| Analysis latency (with fork PoC) | < 5min |
| Report generation | < 10s |
| Concurrent audits | 3+ |
| Report quality | Match Immunefi Low-grade standard |

---

## Security Considerations

1. **Input validation**: Sanitize all contract code before analysis (prevent DoS via crafted input)
2. **Sandboxing**: Run static analysis in isolated subprocess with timeout
3. **API key management**: Use Secret Manager, never hardcode credentials
4. **Rate limiting**: Etherscan/RPC calls throttled to avoid blocking
5. **Output sanitization**: Reports don't expose internal system details

---

## Future Extensions

- **Multi-chain support**: Ethereum, Base, Arbitrum, Optimism
- **CI/CD integration**: GitHub Action for automatic PR audits
- **Real-time monitoring**: Watch deployed contracts for new vulnerabilities
- **Audit marketplace**: Submit findings to Immunefi/Code4rena via API

---

*Design Version: 1.0 | 2026-05-04*
