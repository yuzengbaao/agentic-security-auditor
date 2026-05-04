#!/usr/bin/env python3
"""Agentic Security Auditor — Production-Grade Entry Point

Integrates:
- Static Analysis (pattern matching)
- Slither (control/data flow analysis)
- AI Audit (OpenRouter Gemini)
- Vulnerability Database (SWC Registry)

Usage:
    python main.py --file examples/vulnerable.sol
    python main.py --code "pragma solidity ..."
    python main.py --address 0x... --chain ethereum
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, 'src')

from core.openrouter_client import get_openrouter_client
from tools.audit_tools import analyze_contract_code, calculate_risk_score, generate_report
from tools.slither_integration import run_slither_analysis, format_slither_findings
from tools.vulnerability_db import enrich_finding, format_vulnerability_report, get_vulnerability_stats
from utils.etherscan_fetcher import fetch_contract_etherscan_api


def load_contract(source_type: str, source_value: str, chain: str = "ethereum") -> str:
    if source_type == "file":
        return Path(source_value).read_text()
    elif source_type == "code":
        return source_value
    elif source_type == "address":
        print(f"🔍 Fetching contract from Etherscan ({chain})...")
        result = fetch_contract_etherscan_api(source_value, chain=chain)
        if "error" in result:
            raise RuntimeError(f"Failed to fetch contract: {result['error']}")
        print(f"   ✅ Contract: {result['contract_name']} ({len(result['source_code'])} chars)")
        return result["source_code"]
    else:
        raise ValueError(f"Unknown source type: {source_type}")


def run_production_audit(code: str, use_ai: bool = True) -> dict:
    """Run complete production-grade audit pipeline."""
    print("\n🔍 Phase 1: Static Pattern Analysis")
    static_result = analyze_contract_code(code)
    print(f"   Found {len(static_result['findings'])} issues (Risk Score: {static_result['risk_score']})")
    
    print("\n🔬 Phase 2: Slither Control Flow Analysis")
    slither_result = run_slither_analysis(code)
    if slither_result["success"]:
        print(f"   Found {len(slither_result['findings'])} issues via Slither")
        # Enrich with SWC data
        slither_result["findings"] = [enrich_finding(f) for f in slither_result["findings"]]
    else:
        print(f"   ⚠️ Slither skipped: {slither_result['error']}")
    
    ai_report = None
    if use_ai:
        print("\n🤖 Phase 3: AI-Powered Audit (OpenRouter)")
        try:
            client = get_openrouter_client()
            ai_report = client.audit_contract(code)
            print(f"   AI report: {len(ai_report)} chars")
        except Exception as e:
            print(f"   ⚠️ AI audit skipped: {e}")
    
    # Combine findings
    all_findings = static_result["findings"] + slither_result.get("findings", [])
    
    # Calculate updated risk score
    combined_risk = calculate_risk_score(all_findings)
    
    print("\n📊 Phase 4: Report Generation")
    static_report = generate_report(static_result["findings"], "Contract")
    
    return {
        "static": static_result,
        "slither": slither_result,
        "ai_report": ai_report,
        "all_findings": all_findings,
        "risk_score": combined_risk,
    }


def main():
    parser = argparse.ArgumentParser(description="Agentic Security Auditor (Production)")
    parser.add_argument("--file", help="Path to Solidity contract file")
    parser.add_argument("--code", help="Solidity code string")
    parser.add_argument("--address", help="Deployed contract address")
    parser.add_argument("--chain", default="ethereum", help="Blockchain (ethereum, bsc, polygon, arbitrum, optimism, base)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI audit (static + Slither only)")
    parser.add_argument("--output", default="audit_report.md", help="Output report path")
    args = parser.parse_args()
    
    if args.file:
        code = load_contract("file", args.file)
    elif args.code:
        code = load_contract("code", args.code)
    elif args.address:
        code = load_contract("address", args.address, chain=args.chain)
    else:
        print("Usage: python main.py --file contract.sol")
        print("       python main.py --code 'pragma solidity ...'")
        print("       python main.py --address 0x... --chain ethereum")
        sys.exit(1)
    
    print(f"\n🚀 Agentic Security Auditor (Production)")
    print(f"   Contract size: {len(code)} chars\n")
    
    result = run_production_audit(code, use_ai=not args.no_ai)
    
    # Generate comprehensive report
    report_parts = []
    report_parts.append("# Agentic Security Audit Report (Production)\n")
    report_parts.append(f"**Risk Score**: {result['risk_score']}/100\n")
    report_parts.append(f"**Total Findings**: {len(result['all_findings'])}\n")
    report_parts.append("---\n")
    
    report_parts.append("## Static Analysis Report\n")
    report_parts.append(generate_report(result["static"]["findings"], "Contract"))
    
    if result["slither"]["success"]:
        report_parts.append("\n---\n")
        report_parts.append("## Slither Analysis (Control Flow)\n")
        report_parts.append(format_slither_findings(result["slither"]["findings"]))
        
        report_parts.append("\n---\n")
        report_parts.append("## Vulnerability Database (SWC Registry)\n")
        report_parts.append(format_vulnerability_report(result["slither"]["findings"]))
    
    if result["ai_report"]:
        report_parts.append("\n---\n")
        report_parts.append("## AI-Powered Audit Report (OpenRouter)\n")
        report_parts.append(result["ai_report"])
    
    full_report = "\n".join(report_parts)
    Path(args.output).write_text(full_report)
    
    print(f"\n✅ Report saved to: {args.output}")
    print(f"📊 Final Risk Score: {result['risk_score']}/100")
    print(f"🔍 Static findings: {len(result['static']['findings'])}")
    if result["slither"]["success"]:
        print(f"🔬 Slither findings: {len(result['slither']['findings'])}")
    if result["ai_report"]:
        print(f"🤖 AI audit: ENABLED")


if __name__ == "__main__":
    main()
