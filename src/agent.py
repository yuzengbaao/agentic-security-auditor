"""Agentic Security Auditor — Multi-Agent Orchestrator

Uses Google ADK to coordinate three agents:
1. Task Receiver — Ingests contract code/address
2. Security Auditor — Analyzes for vulnerabilities  
3. Report Generator — Produces structured audit report
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Google ADK imports
from google.adk import Agent, Runner
from google.adk.tools import google_search
from google.adk.events import Event

# Local tools
from tools.audit_tools import (
    analyze_contract_code,
    check_reentrancy,
    check_access_control,
    check_erc_compliance,
    generate_report,
    calculate_risk_score
)

# ── Agent 1: Task Receiver ──
task_receiver = Agent(
    name="task_receiver",
    model="gemini-2.0-flash-exp",
    instruction="""You are the Task Receiver for a smart contract security auditing system.

Your job: accept user input and normalize it into a structured audit task.

Input types you handle:
1. Solidity code snippets (paste directly)
2. GitHub repository URLs (clone and extract contracts)
3. Deployed contract addresses (fetch from block explorer)
4. File paths (read local contract files)

For each input, produce a structured task object:
{
  "source_type": "code|github|address|file",
  "source_value": "<raw input>",
  "contract_code": "<extracted solidity code>",
  "contract_type": "ERC20|ERC721|DeFi|Governance|Unknown",
  "analysis_scope": ["static", "dynamic", "access_control", "reentrancy"],
  "priority": "high|medium|low"
}

If the input is unclear, ask for clarification before proceeding.
Always verify the contract code is valid Solidity before passing to the Security Auditor.
""",
    tools=[google_search],
)

# ── Agent 2: Security Auditor ──
security_auditor = Agent(
    name="security_auditor",
    model="gemini-1.5-pro",
    instruction="""You are an expert smart contract security auditor with 5 years of experience.

## Audit Protocol (5 phases)

### Phase 1: Reconnaissance
- Identify contract type (ERC-20, ERC-721, DeFi, governance, etc.)
- Map all external/public functions and their access controls
- Identify state variables and their mutability patterns

### Phase 2: Threat Surface Mapping
For each function, check:
- Who can call it? (permissionless / admin-only)
- What state does it modify?
- Does it make external calls?
- Does it handle funds?
- Is there a reentrancy guard?

### Phase 3: Vulnerability Detection
Check for these issues in order of severity:

**Critical** (must report):
- [ ] Reentrancy (no guard + external call + state change)
- [ ] Access control bypass (selfdestruct, ownership transfer without auth)
- [ ] Unchecked low-level calls (call/transfer/send return value ignored)
- [ ] Integer overflow/underflow (pre-0.8 Solidity)
- [ ] Front-running vulnerability

**High**:
- [ ] Timestamp/Blockhash dependence
- [ ] tx.origin authorization
- [ ] Delegatecall to untrusted contract
- [ ] Unprotected initializer
- [ ] Missing zero-address checks

**Medium**:
- [ ] Unchecked arithmetic in newer Solidity
- [ ] Lack of event emission
- [ ] Unbounded loop / DoS via gas exhaustion
- [ ] Floating pragma

**Low**:
- [ ] Gas inefficiencies
- [ ] Missing NatSpec documentation

### Phase 4: Evidence Collection
For each finding:
- Extract vulnerable code snippet with line numbers
- Rate confidence: Confirmed / Highly Likely / Suspected
- Document exploit preconditions

### Phase 5: Severity Calibration
- Severity must be justified by demonstrated impact
- Never fabricate vulnerabilities
- If uncertain, say "Suspected" not "Confirmed"

## Output Format
Return findings as JSON array:
[
  {
    "id": "C-01",
    "severity": "Critical",
    "category": "Reentrancy",
    "function": "withdraw",
    "line": 42,
    "description": "External call before state update allows reentrancy",
    "evidence": "(bool success,) = msg.sender.call{value: amount}('')",
    "confidence": "Confirmed",
    "impact": "Attacker can drain all contract funds",
    "recommendation": "Add nonReentrant modifier and move state update before external call"
  }
]
""",
    tools=[
        analyze_contract_code,
        check_reentrancy,
        check_access_control,
        check_erc_compliance,
        calculate_risk_score,
    ],
)

# ── Agent 3: Report Generator ──
report_generator = Agent(
    name="report_generator",
    model="gemini-2.0-flash-exp",
    instruction="""You are a professional security audit report writer.

Your job: transform raw findings into a polished, publication-ready audit report.

## Report Structure

```markdown
# Security Audit Report: [Contract Name]

## Executive Summary
- Contract: [address/filename]
- Lines of Code: [N]
- Risk Score: [0-100]
- Findings: [N total] (Critical: X, High: Y, Medium: Z, Low: W)

## Critical Findings

### C-01: [Title]
| Field | Value |
|-------|-------|
| Severity | Critical |
| Category | [Reentrancy / Access Control / ...] |
| Status | Confirmed |
| Location | [File.sol:Line-Col] |

**Description**
[Clear explanation]

**Proof of Concept**
```solidity
[Minimal exploit code]
```

**Impact**
[What can an attacker achieve]

**Recommendation**
[Specific fix with code]

**Fix Code**
```solidity
[Remediation code]
```

---

## High Findings
[Same structure]

## Medium Findings
[Same structure]

## Low / Informational
[Same structure]

## Appendix A: Analysis Scope
## Appendix B: Tools Used
## Appendix C: Disclaimer
```

## Rules
- Match Immunefi/Code4rena report quality standards
- Every claim needs a code reference
- Recommendations must include specific fix code
- Professional tone, no speculation
""",
    tools=[generate_report],
)

# ── Orchestrator ──
class AgenticSecurityAuditor:
    """Orchestrates the 3-agent audit pipeline."""
    
    def __init__(self):
        self.task_receiver = task_receiver
        self.security_auditor = security_auditor
        self.report_generator = report_generator
    
    async def audit(self, contract_input: str) -> Dict[str, Any]:
        """Run full audit pipeline."""
        print("🚀 Starting Agentic Security Audit...")
        
        # Step 1: Task Receiver
        print("📥 Step 1: Task Receiver — parsing input...")
        task = await self._run_agent(self.task_receiver, contract_input)
        print(f"   Source type: {task.get('source_type', 'unknown')}")
        
        # Step 2: Security Auditor
        print("🔍 Step 2: Security Auditor — analyzing...")
        code = task.get('contract_code', contract_input)
        findings = await self._run_agent(self.security_auditor, code)
        print(f"   Findings: {len(findings) if isinstance(findings, list) else 'N/A'}")
        
        # Step 3: Report Generator
        print("📊 Step 3: Report Generator — compiling report...")
        report = await self._run_agent(
            self.report_generator, 
            json.dumps(findings, indent=2)
        )
        
        return {
            "task": task,
            "findings": findings,
            "report": report,
            "risk_score": calculate_risk_score(findings) if isinstance(findings, list) else 0,
        }
    
    async def _run_agent(self, agent: Agent, input_text: str) -> Any:
        """Run a single agent and parse output."""
        runner = Runner(agent=agent, app_name="agentic-auditor")
        
        # Run agent
        events = []
        async for event in runner.run_async(session_id="audit-session", new_message=input_text):
            events.append(event)
        
        # Extract final response from last event
        if events and events[-1].content:
            response = events[-1].content.parts[0].text if events[-1].content.parts else ""
            
            # Try to parse as JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return response
        
        return {}


# CLI interface
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agentic Security Auditor")
    parser.add_argument("--code", help="Solidity code to audit")
    parser.add_argument("--file", help="Path to contract file")
    parser.add_argument("--address", help="Deployed contract address")
    parser.add_argument("--output", default="audit_report.md", help="Output report path")
    args = parser.parse_args()
    
    # Determine input
    if args.file:
        input_text = Path(args.file).read_text()
    elif args.code:
        input_text = args.code
    elif args.address:
        input_text = f"address:{args.address}"
    else:
        print("Usage: python src/agent.py --file contract.sol")
        print("       python src/agent.py --code 'pragma solidity...'")
        print("       python src/agent.py --address 0x...")
        sys.exit(1)
    
    # Run audit
    auditor = AgenticSecurityAuditor()
    result = asyncio.run(auditor.audit(input_text))
    
    # Save report
    if isinstance(result.get("report"), str):
        Path(args.output).write_text(result["report"])
        print(f"\n✅ Report saved to: {args.output}")
    
    # Print summary
    print(f"\n📊 Audit Summary:")
    print(f"   Risk Score: {result.get('risk_score', 'N/A')}")
    print(f"   Findings: {len(result.get('findings', []))}")
    
    return result

if __name__ == "__main__":
    main()
