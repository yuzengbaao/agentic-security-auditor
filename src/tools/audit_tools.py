"""Audit tools for the Security Auditor Agent"""
import re
from typing import Dict, List, Any

def analyze_contract_code(code: str) -> Dict[str, Any]:
    """Analyze smart contract code for vulnerabilities"""
    findings = []
    
    if "selfdestruct" in code.lower():
        findings.append({
            "severity": "High",
            "category": "Access Control",
            "description": "Contract contains selfdestruct - verify access control"
        })
    
    if re.search(r'call\{.*value:', code):
        findings.append({
            "severity": "Medium",
            "category": "Reentrancy",
            "description": "External call with value detected - check for reentrancy guards"
        })
    
    return {
        "findings": findings,
        "lines_of_code": len(code.split('\n')),
        "risk_score": len(findings) * 10
    }

def check_reentrancy(code: str) -> Dict[str, Any]:
    """Check for reentrancy vulnerabilities"""
    issues = []
    
    if "nonReentrant" not in code and (".call" in code or ".transfer" in code):
        issues.append({
            "severity": "Critical",
            "description": "External calls without reentrancy guard detected"
        })
    
    return {"reentrancy_issues": issues, "safe": len(issues) == 0}

def check_access_control(code: str) -> Dict[str, Any]:
    """Check for access control issues"""
    issues = []
    
    dangerous_functions = ['selfdestruct', 'mint', 'burn', 'transferOwnership']
    for func in dangerous_functions:
        if func in code and "onlyOwner" not in code and "onlyAdmin" not in code:
            issues.append({
                "severity": "High",
                "description": f"{func} may lack proper access control"
            })
    
    return {"access_control_issues": issues}

def generate_report(findings: List[Dict], contract_name: str = "Unknown") -> str:
    """Generate a structured audit report"""
    critical = sum(1 for f in findings if f.get('severity') == 'Critical')
    high = sum(1 for f in findings if f.get('severity') == 'High')
    medium = sum(1 for f in findings if f.get('severity') == 'Medium')
    low = sum(1 for f in findings if f.get('severity') == 'Low')
    
    report = f"""# Security Audit Report: {contract_name}

## Executive Summary
- Total Findings: {len(findings)}
- Critical: {critical}
- High: {high}
- Medium: {medium}
- Low: {low}

## Detailed Findings
"""
    for i, finding in enumerate(findings, 1):
        report += f"""
### {i}. [{finding.get('severity', 'Unknown')}] {finding.get('category', 'General')}
{finding.get('description', 'No description')}

**Recommendation:** {finding.get('recommendation', 'Review and fix')}
"""
    return report
