"""Agentic Security Auditor - Google ADK Agent"""
from google.adk import Agent
from google.adk.tools import google_search
from tools.audit_tools import (
    analyze_contract_code,
    check_reentrancy,
    check_access_control,
    generate_report
)

# Define the security auditor agent
security_auditor = Agent(
    name="security_auditor",
    model="gemini-2.0-flash-exp",
    instruction="""You are an expert smart contract security auditor.
    
    Your capabilities:
    1. Analyze Solidity/Vyper smart contracts for vulnerabilities
    2. Identify common issues: reentrancy, access control, integer overflow, etc.
    3. Generate structured audit reports with severity (Critical/High/Medium/Low)
    4. Provide specific remediation recommendations
    
    When given contract code:
    - First run static analysis tools
    - Then perform manual logic review
    - Finally generate a comprehensive report
    """,
    tools=[
        google_search,
        analyze_contract_code,
        check_reentrancy,
        check_access_control,
        generate_report
    ],
)

if __name__ == "__main__":
    print("Agentic Security Auditor starting...")
