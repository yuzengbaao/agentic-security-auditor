// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title VulnerableBank
 * @dev Intentionally vulnerable contract for security testing
 * WARNING: DO NOT USE IN PRODUCTION
 */
contract VulnerableBank {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        require(msg.value > 0, "Must send ETH");
        balances[msg.sender] += msg.value;
    }
    
    // Vulnerability 1: Reentrancy - external call before state update
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0;
    }
    
    // Vulnerability 2: Anyone can destroy the contract
    function destroy() external {
        selfdestruct(payable(msg.sender));
    }
    
    // Vulnerability 3: tx.origin authorization
    function transferTo(address payable recipient, uint256 amount) external {
        require(tx.origin == msg.sender, "Not authorized");
        require(balances[tx.origin] >= amount, "Insufficient balance");
        balances[tx.origin] -= amount;
        recipient.transfer(amount);
    }
    
    // Vulnerability 4: Integer overflow (pre-0.8, but bad practice)
    function batchTransfer(address[] calldata recipients, uint256 amount) external {
        uint256 total = recipients.length * amount;
        require(balances[msg.sender] >= total, "Insufficient balance");
        
        for (uint i = 0; i < recipients.length; i++) {
            balances[msg.sender] -= amount;
            balances[recipients[i]] += amount;
        }
    }
    
    // Vulnerability 5: Unchecked return value
    function sendEther(address payable recipient, uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        recipient.send(amount);
    }
    
    receive() external payable {
        balances[msg.sender] += msg.value;
    }
}
