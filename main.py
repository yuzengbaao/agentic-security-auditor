#!/usr/bin/env python3
"""Agentic Security Auditor — Main Entry Point

Usage:
    python main.py --file examples/vulnerable.sol
    python main.py --code "pragma solidity ..."
    python main.py --address 0x... --chain ethereum
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from core.openrouter_client import get_openrouter_client
from tools.audit_tools import analyze_contract_code, calculate_risk_score, generate_report
from utils.etherscan_fetcher import fetch_contract_etherscan_api


def load_contract(source_type: str, source_value: str) -> str:
    """Load contract code from various sources."""
    if source_type == "file":
        return Path(source_value).read_text()
    elif source_type == "code":
        return source_value
    elif source_type == "address":
        # For now, use static analysis placeholder
        # In production, this would fetch from Etherscan
        raise NotImplementedError("Address fetching requires API key configuration")
    else:
        raise ValueError(f"Unknown source type: {source_type}")


def run_audit(code: str, use_ai: bool = True) -> dict:
    """Run complete audit pipeline."""
    print("🔍 Step 1: Static Analysis")
    static_result = analyze_contract_code(code)
    print(f"   Found {len(static_result['findings'])} issues (Risk Score: {static_result['risk_score']})")
    
    ai_report = None
    if use_ai:
        print("🤖 Step 2: AI-Powered Audit (OpenRouter)")
        try:
            client = get_openrouter_client()
            ai_report = client.audit_contract(code)
            print(f"   AI report: {len(ai_report)} chars")
        except Exception as e:
            print(f"   ⚠️ AI audit skipped: {e}")
    
    # Generate combined report
    print("📊 Step 3: Generating Report")
    static_report = generate_report(static_result['findings'], "VulnerableBank")
    
    return {
        "static": static_result,
        "static_report": static_report,
        "ai_report": ai_report,
        "risk_score": static_result['risk_score'],
    }


def main():
    parser = argparse.ArgumentParser(description="Agentic Security Auditor")
    parser.add_argument("--file", help="Path to Solidity contract file")
    parser.add_argument("--code", help="Solidity code string")
    parser.add_argument("--address", help="Deployed contract address")
    parser.add_argument("--chain", default="ethereum", help="Blockchain (ethereum, bsc, polygon)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI audit (static only)")
    parser.add_argument("--output", default="audit_report.md", help="Output report path")
    args = parser.parse_args()
    
    # Load contract
    if args.file:
        code = load_contract("file", args.file)
    elif args.code:
        code = load_contract("code", args.code)
    elif args.address:
        print("⚠️ Address audit requires Etherscan API key. Using placeholder.")
        code = f"// Contract at {args.address} on {args.chain}\n// Fetch not implemented"
    else:
        print("Usage: python main.py --file contract.sol")
        print("       python main.py --code 'pragma solidity ...'")
        sys.exit(1)
    
    # Run audit
    print(f"\n🚀 Agentic Security Auditor")
    print(f"   Contract size: {len(code)} chars\n")
    
    result = run_audit(code, use_ai=not args.no_ai)
    
    # Save report
    report_parts = []
    report_parts.append("# Agentic Security Audit Report\n")
    report_parts.append(f"**Risk Score**: {result['risk_score']}/100\n")
    report_parts.append("---\n")
    report_parts.append("## Static Analysis Report\n")
    report_parts.append(result['static_report'])
    
    if result['ai_report']:
        report_parts.append("\n---\n")
        report_parts.append("## AI-Powered Audit Report (OpenRouter)\n")
        report_parts.append(result['ai_report'])
    
    full_report = "\n".join(report_parts)
    Path(args.output).write_text(full_report)
    
    print(f"\n✅ Report saved to: {args.output}")
    print(f"📊 Final Risk Score: {result['risk_score']}/100")
    print(f"🔍 Static findings: {len(result['static']['findings'])}")
    if result['ai_report']:
        print(f"🤖 AI audit: ENABLED")


if __name__ == "__main__":
    main()
