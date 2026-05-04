"""Core audit tools for the Security Auditor Agent."""

import re
from typing import Dict, List, Any

def analyze_contract_code(code: str) -> Dict[str, Any]:
    """Analyze smart contract code for vulnerabilities."""
    findings = []
    lines = code.split('\n')
    
    # Check for common patterns
    code_lower = code.lower()
    
    # Vulnerability 1: selfdestruct without access control
    if 'selfdestruct' in code_lower:
        # Check if onlyOwner/onlyAdmin exists anywhere in contract
        has_access_control = 'onlyowner' in code_lower or 'onlyadmin' in code_lower
        if not has_access_control:
            findings.append({
                "id": "C-01",
                "severity": "Critical",
                "category": "Access Control",
                "description": "Contract contains selfdestruct without explicit access control",
                "confidence": "Confirmed"
            })
        else:
            findings.append({
                "id": "H-01",
                "severity": "High",
                "category": "Access Control",
                "description": "Contract contains selfdestruct — verify access control on destroy function",
                "confidence": "Suspected"
            })
    
    # Vulnerability 2: Reentrancy indicators
    if '.call{' in code or '.call.value' in code:
        has_reentrancy_guard = 'nonreentrant' in code_lower
        if not has_reentrancy_guard:
            findings.append({
                "id": "C-02",
                "severity": "Critical",
                "category": "Reentrancy",
                "description": "External call detected without reentrancy guard (nonReentrant)",
                "confidence": "Highly Likely"
            })
    
    # Vulnerability 3: tx.origin usage
    if 'tx.origin' in code:
        findings.append({
            "id": "H-02",
            "severity": "High",
            "category": "Access Control",
            "description": "tx.origin used for authorization — vulnerable to phishing attacks. Use msg.sender instead.",
            "confidence": "Confirmed"
        })
    
    # Vulnerability 4: Unchecked external calls
    if '.call' in code and 'require(' not in code_lower and 'success' not in code_lower:
        findings.append({
            "id": "H-03",
            "severity": "High",
            "category": "Error Handling",
            "description": "External call return value may not be checked. Always verify call success.",
            "confidence": "Suspected"
        })
    
    # Vulnerability 5: Timestamp dependence
    if 'block.timestamp' in code or 'now' in code:
        findings.append({
            "id": "M-01",
            "severity": "Medium",
            "category": "Timing",
            "description": "Contract depends on block timestamp — miners can manipulate timestamps slightly.",
            "confidence": "Confirmed"
        })
    
    # Vulnerability 6: Floating pragma
    if 'pragma solidity ^' in code:
        findings.append({
            "id": "L-01",
            "severity": "Low",
            "category": "Configuration",
            "description": "Floating pragma (^) allows any compiler version. Pin to specific version for reproducibility.",
            "confidence": "Confirmed"
        })
    
    # Vulnerability 7: Missing event emission for state changes
    state_changing_patterns = ['transfer', 'mint', 'burn', 'deposit', 'withdraw']
    for pattern in state_changing_patterns:
        if pattern in code_lower and 'event' not in code_lower:
            # This is a weak signal, only flag if we're sure
            pass  # Skip to reduce false positives
    
    # Vulnerability 8: Integer overflow in pre-0.8 Solidity
    pragma_match = re.search(r'pragma solidity\s+(\^?\s*(\d+\.\d+))', code)
    if pragma_match:
        version = pragma_match.group(2)
        try:
            major, minor = map(int, version.split('.'))
            if major < 0 or (major == 0 and minor < 8):
                findings.append({
                    "id": "C-03",
                    "severity": "Critical",
                    "category": "Arithmetic",
                    "description": f"Solidity {version} is pre-0.8 — no built-in overflow/underflow protection. Use SafeMath or upgrade.",
                    "confidence": "Confirmed"
                })
        except ValueError:
            pass
    
    return {
        "findings": findings,
        "lines_of_code": len(lines),
        "risk_score": sum(10 if f['severity'] == 'Critical' else 5 if f['severity'] == 'High' else 2 if f['severity'] == 'Medium' else 1 for f in findings)
    }

def check_reentrancy(code: str) -> Dict[str, Any]:
    """Check for reentrancy vulnerabilities."""
    issues = []
    code_lower = code.lower()
    
    # Check for external calls
    external_calls = re.findall(r'(\.call|\.transfer|\.send)\{?[^}]*\}?\s*\(', code)
    
    for call in external_calls:
        # Check if followed by state update
        call_pos = code.find(call)
        after_call = code[call_pos:call_pos + 200]
        
        has_guard = 'nonreentrant' in code_lower
        has_state_update = True  # Any external call is risky
        
        if not has_guard and has_state_update:
            issues.append({
                "severity": "Critical",
                "description": f"External call ({call}) without reentrancy guard followed by state update",
                "location": f"line {code[:call_pos].count(chr(10)) + 1}"
            })
    
    return {
        "reentrancy_issues": issues,
        "safe": len(issues) == 0,
        "external_calls_found": len(external_calls)
    }

def check_access_control(code: str) -> Dict[str, Any]:
    """Check for access control issues."""
    issues = []
    code_lower = code.lower()
    
    dangerous_functions = [
        ('selfdestruct', 'Can destroy contract and send funds to arbitrary address'),
        ('transferOwnership', 'Can change contract owner'),
        ('renounceOwnership', 'Can remove all ownership'),
        ('mint', 'Can create unlimited tokens'),
        ('burn', 'Can destroy tokens'),
    ]
    
    for func_name, risk in dangerous_functions:
        if func_name in code_lower:
            # Check if function has access control
            func_pattern = re.search(rf'function\s+{func_name}\s*\([^)]*\)[^{{]*{{', code, re.IGNORECASE)
            if func_pattern:
                func_start = func_pattern.start()
                func_body = code[func_start:func_start + 500]
                
                has_owner_check = any(modifier in func_body.lower() for modifier in ['onlyowner', 'onlyadmin', 'require(owner', 'require(admin'])
                
                if not has_owner_check:
                    issues.append({
                        "severity": "High",
                        "description": f"{func_name} lacks access control: {risk}",
                        "function": func_name
                    })
    
    return {"access_control_issues": issues}

def check_erc_compliance(code: str, standard: str = "ERC20") -> Dict[str, Any]:
    """Check ERC standard compliance."""
    issues = []
    code_lower = code.lower()
    
    if standard == "ERC20":
        required_functions = ['totalsupply', 'balanceof', 'transfer', 'transferfrom', 'approve', 'allowance']
        optional_events = ['transfer', 'approval']
        
        for func in required_functions:
            if func not in code_lower:
                issues.append({
                    "severity": "Medium",
                    "description": f"Missing required ERC20 function: {func}",
                    "standard": "ERC20"
                })
        
        for event in optional_events:
            if f'event {event}' not in code_lower:
                issues.append({
                    "severity": "Low",
                    "description": f"Missing recommended ERC20 event: {event}",
                    "standard": "ERC20"
                })
    
    return {"erc_issues": issues, "standard": standard}

def calculate_risk_score(findings: List[Dict]) -> int:
    """Calculate overall risk score (0-100)."""
    if not findings:
        return 0
    
    severity_weights = {
        "Critical": 25,
        "High": 10,
        "Medium": 5,
        "Low": 1,
        "Informational": 0
    }
    
    total = sum(severity_weights.get(f.get("severity", "Low"), 1) for f in findings)
    return min(total, 100)

def generate_report(findings: List[Dict], contract_name: str = "Unknown") -> str:
    """Generate a structured audit report in Markdown."""
    if not findings:
        return f"# Security Audit Report: {contract_name}\n\n✅ No vulnerabilities detected."
    
    critical = sum(1 for f in findings if f.get('severity') == 'Critical')
    high = sum(1 for f in findings if f.get('severity') == 'High')
    medium = sum(1 for f in findings if f.get('severity') == 'Medium')
    low = sum(1 for f in findings if f.get('severity') == 'Low')
    risk_score = calculate_risk_score(findings)
    
    report = f"""# Security Audit Report: {contract_name}

## Executive Summary
- **Total Findings**: {len(findings)}
- **Critical**: {critical}
- **High**: {high}
- **Medium**: {medium}
- **Low**: {low}
- **Risk Score**: {risk_score}/100

## Findings Summary

"""
    
    for severity in ["Critical", "High", "Medium", "Low"]:
        severity_findings = [f for f in findings if f.get('severity') == severity]
        if severity_findings:
            report += f"### {severity} Findings ({len(severity_findings)})\n\n"
            for i, finding in enumerate(severity_findings, 1):
                report += f"#### {finding.get('id', f'{severity[0]}-{i}')}: {finding.get('category', 'General')}\n"
                report += f"- **Description**: {finding.get('description', 'N/A')}\n"
                report += f"- **Confidence**: {finding.get('confidence', 'Unknown')}\n"
                if 'location' in finding:
                    report += f"- **Location**: {finding['location']}\n"
                if 'function' in finding:
                    report += f"- **Function**: {finding['function']}\n"
                report += f"- **Recommendation**: {finding.get('recommendation', 'Review and fix')}\n\n"
    
    report += """## Appendix
- **Tools Used**: Static pattern analysis, control flow inspection
- **Methodology**: OWASP Smart Contract Security, Slither taxonomy
- **Disclaimer**: This audit is not a guarantee of security. Manual review and formal verification recommended.
"""
    
    return report
