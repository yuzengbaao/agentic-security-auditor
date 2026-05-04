"""Slither integration for production-grade static analysis.

Uses Trail of Bits Slither to detect vulnerabilities via control flow
and data flow analysis, not just pattern matching.

Requires: slither-analyzer, crytic-compile, solc
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional


def run_slither_analysis(code: str, output_format: str = "json") -> Dict[str, Any]:
    """Run Slither analysis on Solidity code.
    
    Args:
        code: Solidity source code
        output_format: "json" or "text"
    
    Returns:
        {
            "success": bool,
            "findings": [...],
            "error": str (if failed),
            "raw_output": dict
        }
    """
    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        # Run Slither with JSON output
        cmd = ["slither", temp_path, "--json", "-"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse JSON output from stdout
        try:
            slither_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "success": False,
                "findings": [],
                "error": f"Failed to parse Slither output: {result.stderr[:200]}",
                "raw_output": None
            }
        
        # Extract findings
        findings = []
        if "results" in slither_output and "detectors" in slither_output["results"]:
            for detector in slither_output["results"]["detectors"]:
                finding = {
                    "id": detector.get("check", "UNKNOWN"),
                    "severity": _map_impact_to_severity(detector.get("impact", "Informational")),
                    "category": detector.get("check", "General"),
                    "description": detector.get("description", ""),
                    "confidence": detector.get("confidence", "Medium"),
                    "lines": _extract_lines(detector),
                    "reference": detector.get("wiki_url", ""),
                }
                findings.append(finding)
        
        return {
            "success": True,
            "findings": findings,
            "error": None,
            "raw_output": slither_output,
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "findings": [],
            "error": "Slither analysis timed out (60s)",
            "raw_output": None
        }
    except Exception as e:
        return {
            "success": False,
            "findings": [],
            "error": f"Slither execution failed: {type(e).__name__}: {e}",
            "raw_output": None
        }
    finally:
        # Cleanup temp file
        Path(temp_path).unlink(missing_ok=True)


def _map_impact_to_severity(impact: str) -> str:
    """Map Slither impact to our severity scale."""
    mapping = {
        "High": "High",
        "Medium": "Medium", 
        "Low": "Low",
        "Informational": "Informational",
        "Optimization": "Low",
    }
    return mapping.get(impact, "Low")


def _extract_lines(detector: Dict) -> List[int]:
    """Extract line numbers from detector elements."""
    lines = []
    if "elements" in detector:
        for element in detector["elements"]:
            if "source_mapping" in element and "lines" in element["source_mapping"]:
                lines.extend(element["source_mapping"]["lines"])
    return sorted(list(set(lines)))


def format_slither_findings(findings: List[Dict]) -> str:
    """Format Slither findings as markdown report section."""
    if not findings:
        return "### Slither Analysis\n\n✅ No issues detected by Slither."
    
    report = "### Slither Analysis\n\n"
    report += f"**Total Findings**: {len(findings)}\n\n"
    
    severity_order = ["High", "Medium", "Low", "Informational"]
    for severity in severity_order:
        severity_findings = [f for f in findings if f["severity"] == severity]
        if severity_findings:
            report += f"#### {severity} Findings ({len(severity_findings)})\n\n"
            for finding in severity_findings:
                report += f"**{finding['id']}** (Confidence: {finding['confidence']})\n"
                report += f"- {finding['description'][:200]}\n"
                if finding['lines']:
                    report += f"- Lines: {', '.join(map(str, finding['lines'][:5]))}\n"
                if finding['reference']:
                    report += f"- Reference: {finding['reference']}\n"
                report += "\n"
    
    return report


if __name__ == "__main__":
    # Test with vulnerable contract
    test_code = Path("examples/vulnerable.sol").read_text()
    result = run_slither_analysis(test_code)
    
    if result["success"]:
        print(f"✅ Slither found {len(result['findings'])} issues")
        for f in result["findings"][:5]:
            print(f"  [{f['severity']}] {f['id']}: {f['description'][:60]}...")
    else:
        print(f"❌ {result['error']}")
