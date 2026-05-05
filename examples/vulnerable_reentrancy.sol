// SPDX-License-Identifier: MIT
// This contract contains INTENTIONAL vulnerabilities for testing
pragma solidity ^0.8.0;

contract VulnerableReentrancy {
    mapping(address => uint) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // VULNERABILITY: Reentrancy - external call before state update
    function withdraw() public {
        uint amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0; // State update AFTER external call
    }
    
    // VULNERABILITY: No access control
    function emergencyWithdraw() public {
        (bool success, ) = msg.sender.call{value: address(this).balance}("");
        require(success, "Transfer failed");
    }
    
    receive() external payable {}
}
