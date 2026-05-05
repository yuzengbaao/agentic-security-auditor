#!/usr/bin/env python3
"""Agentic Security Auditor — ADK Multi-Agent System (v2.0)

Refactored for Google Cloud Rapid Agent Hackathon.
Uses Google ADK with Vertex AI backend.

Agents:
1. ScannerAgent — Fetches contract from Etherscan
2. StaticAnalyzerAgent — Pattern-based static analysis  
3. AIReviewerAgent — Gemini-powered deep audit
4. ReportAgent — Generates structured audit report
5. CoordinatorAgent — Orchestrates the pipeline
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

# Force Vertex AI backend
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0679032909")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# ─── MCP Tool Wrappers ───

def etherscan_fetch_mcp(address: str, chain: str = "ethereum") -> str:
    """MCP-style tool: Fetch contract source from Etherscan."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.utils.etherscan_fetcher import fetch_contract_etherscan_api
        result = fetch_contract_etherscan_api(address, chain=chain)
        if "error" in result:
            return json.dumps({"error": result["error"]})
        return json.dumps({
            "success": True,
            "contract_name": result.get("contract_name", "Unknown"),
            "source_code": result.get("source_code", "")[:5000],  # Truncate for token limit
            "compiler_version": result.get("compiler_version", "unknown"),
            "address": address,
            "chain": chain
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def static_analyze_mcp(code: str) -> str:
    """MCP-style tool: Run static pattern analysis."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.tools.audit_tools import analyze_contract_code
        result = analyze_contract_code(code)
        return json.dumps({
            "findings_count": len(result.get("findings", [])),
            "risk_score": result.get("risk_score", 0),
            "findings": result.get("findings", [])[:10]  # Limit output
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def slither_analyze_mcp(code: str) -> str:
    """MCP-style tool: Run Slither analysis."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.tools.slither_integration import run_slither_analysis
        result = run_slither_analysis(code)
        if not result.get("success"):
            return json.dumps({"skipped": True, "reason": result.get("error", "unknown")})
        from src.tools.vulnerability_db import enrich_finding
        findings = [enrich_finding(f) for f in result.get("findings", [])]
        return json.dumps({
            "findings_count": len(findings),
            "findings": findings[:10]
        })
    except Exception as e:
        return json.dumps({"error": str(e), "skipped": True})

def ai_audit_mcp(code: str) -> str:
    """MCP-style tool: AI-powered audit via OpenRouter."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from src.core.openrouter_client import get_openrouter_client
        client = get_openrouter_client()
        report = client.audit_contract(code)
        return json.dumps({"report": report[:3000]})  # Truncate
    except Exception as e:
        return json.dumps({"error": str(e), "skipped": True})

def calculate_risk_mcp(findings_json: str) -> str:
    """MCP-style tool: Calculate risk score from findings."""
    try:
        findings = json.loads(findings_json)
        from src.tools.audit_tools import calculate_risk_score
        score = calculate_risk_score(findings)
        return json.dumps({"risk_score": score, "total_findings": len(findings)})
    except Exception as e:
        return json.dumps({"error": str(e)})

# ─── Agents ───

scanner_agent = Agent(
    name="scanner_agent",
    model="gemini-2.5-flash",
    description="Fetches smart contract source code from blockchain explorers",
    instruction="""You are a Contract Scanner Agent.

Your job: Given a contract address and chain, fetch the source code.

Use the `etherscan_fetch_mcp` tool to fetch contract data.
Input: address (e.g., "0x...") and chain (e.g., "ethereum", "base", "bsc")
Output the result as JSON with fields: success, contract_name, source_code, compiler_version.

If the fetch fails, report the error clearly.
""",
    tools=[etherscan_fetch_mcp],
)

static_analyzer_agent = Agent(
    name="static_analyzer",
    model="gemini-2.5-flash",
    description="Runs static pattern analysis on Solidity code",
    instruction="""You are a Static Analysis Agent.

Your job: Analyze Solidity code for common vulnerability patterns.

Use the `static_analyze_mcp` tool to run analysis.
Input: Solidity source code string
Output: JSON with findings_count, risk_score, and findings array.

Also use the `slither_analyze_mcp` tool for deeper control-flow analysis.
Combine findings from both tools and present a unified summary.

Rate each finding severity: Critical / High / Medium / Low / Info.
For Critical/High findings, explain the exploit path in 1-2 sentences.
""",
    tools=[static_analyze_mcp, slither_analyze_mcp],
)

ai_reviewer_agent = Agent(
    name="ai_reviewer",
    model="gemini-2.5-flash",
    description="Deep AI-powered audit using Gemini",
    instruction="""You are an AI Security Reviewer Agent powered by Gemini.

Your job: Perform a deep security review of Solidity code.

Use the `ai_audit_mcp` tool to get an initial AI assessment.
Then enhance it with your own analysis:

1. Identify subtle logic flaws missed by static analysis
2. Check for business logic vulnerabilities (price oracle manipulation, flash loan attacks)
3. Verify access control correctness
4. Review gas optimization vs security tradeoffs

For each finding:
- Severity: Critical/High/Medium/Low
- Evidence: Code snippet with line context
- Impact: What an attacker can achieve
- Fix: Specific remediation code

Return findings as structured JSON.
""",
    tools=[ai_audit_mcp],
)

report_agent = Agent(
    name="report_generator",
    model="gemini-2.5-flash",
    description="Generates professional audit reports",
    instruction="""You are a Report Generator Agent.

Your job: Transform raw audit findings into a professional security report.

Input: JSON with static findings, AI findings, risk score, contract metadata.
Output: Markdown report matching Immunefi/Code4rena quality standards.

Report structure:
# Security Audit Report

## Executive Summary
- Contract address/name
- Lines of code
- Risk score (0-100)
- Findings summary (Critical: X, High: Y, Medium: Z, Low: W)

## Findings (sorted by severity)

### [ID] [Title]
| Field | Value |
|-------|-------|
| Severity | [Level] |
| Status | Confirmed/Suspected |
| Location | [file.sol:line] |

**Description**
[Clear explanation]

**Evidence**
```solidity
[code snippet]
```

**Impact**
[What attacker can achieve]

**Recommendation**
[Specific fix]

## Appendix
- Tools used
- Analysis scope
- Disclaimer

Rules:
- Every claim needs a code reference
- Recommendations must include specific fix code
- Professional tone, no speculation
""",
    tools=[calculate_risk_mcp],
)

coordinator_agent = Agent(
    name="coordinator",
    model="gemini-2.5-flash",
    description="Orchestrates the multi-agent audit pipeline",
    instruction="""You are the Coordinator Agent for a multi-agent smart contract security auditing system.

Your job: Orchestrate the 4-stage audit pipeline:
1. Scanner → fetch contract source
2. Static Analyzer → pattern + Slither analysis
3. AI Reviewer → deep Gemini-powered audit
4. Report Generator → compile professional report

Given user input (address, code, or file), decide which agents to invoke and in what order.

Pipeline logic:
- If input is an address: Scanner → Static → AI → Report
- If input is code/file: Static → AI → Report (skip Scanner)

For each stage, invoke the appropriate agent and pass the output to the next stage.
Track progress and report completion status.

Final output must include:
- Full markdown report
- Risk score
- Finding count by severity
- Contract metadata
""",
)

# ─── Orchestrator ───

class ADKSecurityAuditor:
    """Production-grade ADK multi-agent orchestrator."""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.app_name = "agentic-security-auditor-v2"
    
    async def _run_agent(self, agent: Agent, user_input: str, session_id: str = None) -> str:
        """Run a single agent and return text output."""
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        runner = Runner(
            agent=agent,
            app_name=self.app_name,
            session_service=self.session_service
        )
        
        # Create content object
        content = types.Content(
            role="user",
            parts=[types.Part(text=user_input)]
        )
        
        # Run and collect events
        response_text = ""
        async for event in runner.run_async(
            session_id=session_id,
            user_id="audit_user",
            new_message=content
        ):
            if (hasattr(event, 'content') and event.content and 
                event.content.parts and event.content.parts[0].text):
                response_text = event.content.parts[0].text
        
        return response_text
    
    async def audit_address(self, address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Full audit pipeline for a deployed contract address."""
        print(f"🚀 Starting ADK Audit: {address} ({chain})")
        
        # Stage 1: Scanner
        print("📥 Stage 1: Scanner Agent — fetching contract...")
        scanner_input = f'Fetch contract {address} on chain {chain}'
        scanner_result = await self._run_agent(scanner_agent, scanner_input)
        
        # Parse scanner result
        try:
            contract_data = json.loads(scanner_result)
            if not contract_data.get("success"):
                return {"error": contract_data.get("error", "Failed to fetch contract")}
            code = contract_data.get("source_code", "")
            contract_name = contract_data.get("contract_name", "Unknown")
        except json.JSONDecodeError:
            code = scanner_result
            contract_name = "Unknown"
        
        if not code or len(code) < 10:
            return {"error": "No source code available"}
        
        print(f"   ✅ Contract: {contract_name} ({len(code)} chars)")
        
        # Stage 2: Static Analysis
        print("🔍 Stage 2: Static Analyzer — pattern + Slither...")
        static_input = f'Analyze this Solidity code:\n\n{code[:8000]}'  # Truncate for token limit
        static_result = await self._run_agent(static_analyzer_agent, static_input)
        
        # Stage 3: AI Review
        print("🤖 Stage 3: AI Reviewer — deep Gemini audit...")
        ai_input = f'Perform deep security audit:\n\n{code[:8000]}\n\nStatic analysis results:\n{static_result[:3000]}'
        ai_result = await self._run_agent(ai_reviewer_agent, ai_input)
        
        # Stage 4: Report
        print("📊 Stage 4: Report Generator — compiling report...")
        report_input = json.dumps({
            "contract_name": contract_name,
            "address": address,
            "chain": chain,
            "static_analysis": static_result,
            "ai_analysis": ai_result,
            "code_length": len(code)
        }, indent=2)
        report_result = await self._run_agent(report_agent, report_input)
        
        return {
            "contract_name": contract_name,
            "address": address,
            "chain": chain,
            "report": report_result,
            "static_raw": static_result,
            "ai_raw": ai_result,
        }
    
    async def audit_code(self, code: str) -> Dict[str, Any]:
        """Audit raw Solidity code (skip scanner)."""
        print(f"🚀 Starting ADK Audit: {len(code)} chars of code")
        
        # Stage 1: Static Analysis
        print("🔍 Stage 1: Static Analyzer — pattern + Slither...")
        static_input = f'Analyze this Solidity code:\n\n{code[:8000]}'
        static_result = await self._run_agent(static_analyzer_agent, static_input)
        
        # Stage 2: AI Review
        print("🤖 Stage 2: AI Reviewer — deep Gemini audit...")
        ai_input = f'Perform deep security audit:\n\n{code[:8000]}\n\nStatic analysis results:\n{static_result[:3000]}'
        ai_result = await self._run_agent(ai_reviewer_agent, ai_input)
        
        # Stage 3: Report
        print("📊 Stage 3: Report Generator — compiling report...")
        report_input = json.dumps({
            "contract_name": "Unknown",
            "code_length": len(code),
            "static_analysis": static_result,
            "ai_analysis": ai_result,
        }, indent=2)
        report_result = await self._run_agent(report_agent, report_input)
        
        return {
            "report": report_result,
            "static_raw": static_result,
            "ai_raw": ai_result,
        }


# ─── CLI ───

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Agentic Security Auditor v2.0 (ADK)")
    parser.add_argument("--file", help="Path to Solidity contract file")
    parser.add_argument("--code", help="Solidity code string")
    parser.add_argument("--address", help="Deployed contract address")
    parser.add_argument("--chain", default="ethereum", help="Blockchain")
    parser.add_argument("--output", default="audit_report_adk.md", help="Output path")
    args = parser.parse_args()
    
    auditor = ADKSecurityAuditor()
    
    if args.address:
        result = asyncio.run(auditor.audit_address(args.address, args.chain))
    elif args.file:
        code = Path(args.file).read_text()
        result = asyncio.run(auditor.audit_code(code))
    elif args.code:
        result = asyncio.run(auditor.audit_code(args.code))
    else:
        print("Usage: python src/agent_v2.py --address 0x... --chain ethereum")
        print("       python src/agent_v2.py --file contract.sol")
        sys.exit(1)
    
    if "error" in result:
        print(f"\n❌ Audit failed: {result['error']}")
        sys.exit(1)
    
    # Save report
    if isinstance(result.get("report"), str):
        Path(args.output).write_text(result["report"])
        print(f"\n✅ Report saved to: {args.output}")
    
    print("\n📊 ADK Audit Complete")
    return result


if __name__ == "__main__":
    main()
