// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// INTENTIONALLY VULNERABLE CONTRACT FOR TESTING
// DO NOT USE IN PRODUCTION

contract VulnerableBank {
    mapping(address => uint256) public balances;

    // Vulnerability 1: Reentrancy (Critical)
    // No reentrancy guard, external call before state update
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0; // State update AFTER external call!
    }

    // Vulnerability 2: Missing access control (High)
    // Anyone can call selfdestruct
    function destroy() external {
        selfdestruct(payable(msg.sender));
    }

    // Vulnerability 3: Unchecked external call (Medium)
    function sendFunds(address to, uint256 amount) external {
        (bool success, ) = to.call{value: amount}("");
        // Return value NOT checked!
    }

    // Vulnerability 4: No input validation (Low)
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    receive() external payable {
        deposit();
    }
}
