"""Tests for audit tools"""
import sys
sys.path.insert(0, 'src')
from tools.audit_tools import (
    analyze_contract_code,
    check_reentrancy,
    check_access_control,
    check_erc_compliance,
    calculate_risk_score,
    generate_report
)

def test_analyze_contract_code():
    """Test static analysis of contract code."""
    code = """
    contract Test {
        function withdraw() public {
            msg.sender.call{value: 1 ether}("");
        }
    }
    """
    result = analyze_contract_code(code)
    assert result["lines_of_code"] > 0
    assert len(result["findings"]) >= 1
    reentrancy_findings = [f for f in result["findings"] if f["category"] == "Reentrancy"]
    assert len(reentrancy_findings) >= 1

def test_reentrancy_check():
    """Test reentrancy detection."""
    code = "function withdraw() { msg.sender.call{value: 1}(''); }"
    result = check_reentrancy(code)
    assert not result["safe"]
    assert result["external_calls_found"] >= 1

def test_access_control():
    """Test access control detection."""
    code = "function mint() { _mint(msg.sender, 100); }"
    result = check_access_control(code)
    assert len(result["access_control_issues"]) >= 1
    mint_issues = [i for i in result["access_control_issues"] if "mint" in i["description"]]
    assert len(mint_issues) >= 1

def test_erc_compliance_incomplete():
    """Test ERC20 compliance detects missing functions."""
    # NOTE: Do not put function names in comments — check_erc_compliance
    # does simple string matching and comments count!
    incomplete_erc20 = """
    contract BadERC20 {
        function totalSupply() public view returns (uint) { return 0; }
        function balanceOf(address) public view returns (uint) { return 0; }
        function transfer(address, uint) public returns (bool) { return true; }
        // some functions intentionally left out
    }
    """
    result = check_erc_compliance(incomplete_erc20, "ERC20")
    assert len(result["erc_issues"]) >= 1
    missing_functions = [i for i in result["erc_issues"] if "Missing required" in i["description"]]
    assert len(missing_functions) >= 1

def test_risk_score_calculation():
    """Test risk score calculation."""
    findings = [
        {"severity": "Critical", "description": "Reentrancy"},
        {"severity": "High", "description": "Access control"},
        {"severity": "Medium", "description": "Timestamp"},
        {"severity": "Low", "description": "Pragma"},
    ]
    score = calculate_risk_score(findings)
    assert score > 0
    assert score <= 100
    # Critical=25, High=10, Medium=5, Low=1 = 41
    assert score == 41
    assert calculate_risk_score([]) == 0

def test_generate_report():
    """Test report generation."""
    findings = [
        {"id": "C-01", "severity": "Critical", "category": "Reentrancy",
         "description": "External call without guard", "confidence": "Confirmed"},
        {"id": "H-01", "severity": "High", "category": "Access Control",
         "description": "No owner check", "confidence": "Confirmed"},
    ]
    report = generate_report(findings, "TestContract")
    assert "Security Audit Report: TestContract" in report
    assert "- **Critical**: 1" in report
    assert "- **High**: 1" in report
    assert "- **Medium**: 0" in report
    assert "C-01" in report
    assert "Reentrancy" in report
    assert "35/100" in report

def test_full_pipeline():
    """Test complete audit pipeline on vulnerable contract."""
    vulnerable_code = """
    pragma solidity ^0.7.0;
    
    contract VulnerableBank {
        mapping(address => uint256) public balances;
        
        function withdraw() external {
            uint256 amount = balances[msg.sender];
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success, "Transfer failed");
            balances[msg.sender] = 0;
        }
        
        function destroy() external {
            selfdestruct(payable(msg.sender));
        }
        
        function deposit() external payable {
            balances[msg.sender] += msg.value;
        }
    }
    """
    
    result = analyze_contract_code(vulnerable_code)
    assert result["lines_of_code"] > 10
    assert result["risk_score"] > 20
    
    severities = [f["severity"] for f in result["findings"]]
    assert "Critical" in severities
    assert "Low" in severities
