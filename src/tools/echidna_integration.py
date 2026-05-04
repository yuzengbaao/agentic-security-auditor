"""Echidna integration for property-based fuzzing.

Uses Echidna to automatically generate test cases and find edge cases
that static analysis might miss.

Requires: echidna, slither, crytic-compile, solc
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional


def generate_echidna_config(contract_name: str = "TestContract") -> Dict[str, Any]:
    """Generate Echidna configuration for a contract."""
    return {
        "testMode": "assertion",
        "testLimit": 50000,
        "shrinkLimit": 2000,
        "seqLen": 100,
        "coverage": True,
        "corpusDir": None,
        "workers": 1,
    }


def run_echidna_fuzzing(
    code: str,
    contract_name: str,
    timeout: int = 60
) -> Dict[str, Any]:
    """Run Echidna fuzzing on a contract.
    
    Note: Echidna requires the contract to have Echidna test functions
    or property tests. For general contracts, it can test for basic
    properties like reentrancy, gas exhaustion, etc.
    
    Args:
        code: Solidity source code
        contract_name: Name of the contract to test
        timeout: Fuzzing timeout in seconds
    
    Returns:
        {
            "success": bool,
            "findings": [...],
            "error": str (if failed),
            "coverage": float (0-100)
        }
    """
    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    # Create temp config file
    config = generate_echidna_config(contract_name)
    config["timeout"] = timeout
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        # Run Echidna
        cmd = [
            "echidna",
            temp_path,
            "--contract", contract_name,
            "--config", config_path,
            "--format", "json"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 10
        )
        
        # Parse output
        try:
            echidna_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Echidna might output text even with --format json
            return {
                "success": False,
                "findings": [],
                "error": f"Echidna output parsing failed: {result.stderr[:200]}",
                "coverage": 0
            }
        
        # Extract findings
        findings = []
        if "tests" in echidna_output:
            for test_name, test_result in echidna_output["tests"].items():
                if test_result.get("status") == "failed":
                    finding = {
                        "id": "ECHIDNA-FUZZ",
                        "severity": "High",
                        "category": "Fuzzing",
                        "description": f"Echidna found failing test: {test_name}",
                        "confidence": "High",
                        "test": test_name,
                        "result": test_result
                    }
                    findings.append(finding)
        
        coverage = echidna_output.get("coverage", {}).get("percent", 0)
        
        return {
            "success": True,
            "findings": findings,
            "error": None,
            "coverage": coverage
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "findings": [],
            "error": f"Echidna fuzzing timed out ({timeout}s)",
            "coverage": 0
        }
    except Exception as e:
        return {
            "success": False,
            "findings": [],
            "error": f"Echidna execution failed: {type(e).__name__}: {e}",
            "coverage": 0
        }
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
        Path(config_path).unlink(missing_ok=True)


def format_echidna_findings(findings: List[Dict], coverage: float) -> str:
    """Format Echidna findings as markdown report section."""
    report = f"### Echidna Fuzzing Analysis\n\n"
    report += f"**Coverage**: {coverage:.1f}%\n\n"
    
    if not findings:
        report += "✅ No failing tests found by Echidna fuzzing.\n"
        return report
    
    report += f"**Failed Tests**: {len(findings)}\n\n"
    for finding in findings:
        report += f"**{finding['test']}**\n"
        report += f"- Severity: {finding['severity']}\n"
        report += f"- Description: {finding['description']}\n"
        if 'result' in finding:
            report += f"- Details: {json.dumps(finding['result'], indent=2)[:200]}\n"
        report += "\n"
    
    return report


if __name__ == "__main__":
    # Note: Echidna requires contracts with test functions
    # This is a simplified example
    print("Echidna integration module loaded.")
    print("Note: Echidna requires contracts to have Echidna test functions.")
    print("For full fuzzing, add echidna_ prefixed test functions to your contract.")
