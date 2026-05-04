"""Tests for audit tools"""
import sys
sys.path.insert(0, 'src')
from tools.audit_tools import analyze_contract_code, check_reentrancy, check_access_control

def test_analyze_contract_code():
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

def test_reentrancy_check():
    code = "function withdraw() { msg.sender.call{value: 1}(''); }"
    result = check_reentrancy(code)
    assert not result["safe"]

def test_access_control():
    code = "function mint() { _mint(msg.sender, 100); }"
    result = check_access_control(code)
    assert len(result["access_control_issues"]) >= 1
