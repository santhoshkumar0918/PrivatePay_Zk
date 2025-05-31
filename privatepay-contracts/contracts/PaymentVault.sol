// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title PaymentVault
 * @dev Secure vault for executing private payments on Monad
 * @notice Handles fund storage and execution for PrivatePay
 */
contract PaymentVault is ReentrancyGuard, Ownable, Pausable {
    using SafeERC20 for IERC20;
    
    // Core state
    mapping(address => uint256) public ethBalances;
    mapping(address => mapping(address => uint256)) public tokenBalances;
    mapping(address => bool) public authorizedCallers;
    
    // Payment execution tracking
    struct PaymentExecution {
        address from;
        address to;
        uint256 amount;
        address token; // address(0) for ETH
        uint256 timestamp;
        bytes32 executionHash;
    }
    
    mapping(bytes32 => PaymentExecution) public executedPayments;
    mapping(address => uint256) public userPaymentCount;
    
    uint256 public totalPaymentsExecuted;
    uint256 public totalVolumeProcessed;
    
    // Events
    event PaymentExecuted(
        address indexed from,
        address indexed to,
        uint256 amount,
        address indexed token,
        bytes32 executionHash,
        uint256 timestamp
    );
    
    event FundsDeposited(
        address indexed user,
        uint256 amount,
        address indexed token,
        uint256 timestamp
    );
    
    event FundsWithdrawn(
        address indexed user,
        uint256 amount,
        address indexed token,
        uint256 timestamp
    );
    
    event AuthorizedCallerAdded(
        address indexed caller,
        address indexed addedBy,
        uint256 timestamp
    );
    
    event AuthorizedCallerRemoved(
        address indexed caller,
        address indexed removedBy,
        uint256 timestamp
    );
    
    // Errors
    error UnauthorizedCaller();
    error InsufficientBalance();
    error InvalidAmount();
    error InvalidAddress();
    error PaymentAlreadyExecuted();
    error TransferFailed();
    
    modifier onlyAuthorized() {
        if (!authorizedCallers[msg.sender] && msg.sender != owner()) {
            revert UnauthorizedCaller();
        }
        _;
    }
    
    constructor() Ownable(msg.sender) {
        // Owner is automatically authorized
        authorizedCallers[msg.sender] = true;
    }
    
    /**
     * @dev Deposit ETH to the vault
     */
    function depositETH() external payable nonReentrant {
        if (msg.value == 0) revert InvalidAmount();
        
        ethBalances[msg.sender] += msg.value;
        
        emit FundsDeposited(msg.sender, msg.value, address(0), block.timestamp);
    }
    
    /**
     * @dev Deposit ERC20 tokens to the vault
     * @param token Token contract address
     * @param amount Amount to deposit
     */
    function depositToken(address token, uint256 amount) external nonReentrant {
        if (token == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        tokenBalances[msg.sender][token] += amount;
        
        emit FundsDeposited(msg.sender, amount, token, block.timestamp);
    }
    
    /**
     * @dev Execute a payment (only authorized callers)
     * @param from Sender address
     * @param to Recipient address
     * @param amount Amount to send
     */
    function executePayment(
        address from,
        address to,
        uint256 amount
    ) external onlyAuthorized nonReentrant whenNotPaused {
        if (to == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        if (ethBalances[from] < amount) revert InsufficientBalance();
        
        // Generate execution hash
        bytes32 executionHash = keccak256(abi.encodePacked(
            from,
            to,
            amount,
            address(0), // ETH
            block.timestamp,
            totalPaymentsExecuted
        ));
        
        // Check if payment already executed
        if (executedPayments[executionHash].timestamp != 0) {
            revert PaymentAlreadyExecuted();
        }
        
        // Update balances
        ethBalances[from] -= amount;
        
        // Execute transfer
        (bool success, ) = payable(to).call{value: amount}("");
        if (!success) revert TransferFailed();
        
        // Record execution
        executedPayments[executionHash] = PaymentExecution({
            from: from,
            to: to,
            amount: amount,
            token: address(0),
            timestamp: block.timestamp,
            executionHash: executionHash
        });
        
        // Update counters
        userPaymentCount[from]++;
        totalPaymentsExecuted++;
        totalVolumeProcessed += amount;
        
        emit PaymentExecuted(from, to, amount, address(0), executionHash, block.timestamp);
    }
    
    /**
     * @dev Execute a token payment (only authorized callers)
     * @param from Sender address
     * @param to Recipient address
     * @param amount Amount to send
     * @param token Token contract address
     */
    function executeTokenPayment(
        address from,
        address to,
        uint256 amount,
        address token
    ) external onlyAuthorized nonReentrant whenNotPaused {
        if (to == address(0) || token == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        if (tokenBalances[from][token] < amount) revert InsufficientBalance();
        
        // Generate execution hash
        bytes32 executionHash = keccak256(abi.encodePacked(
            from,
            to,
            amount,
            token,
            block.timestamp,
            totalPaymentsExecuted
        ));
        
        // Check if payment already executed
        if (executedPayments[executionHash].timestamp != 0) {
            revert PaymentAlreadyExecuted();
        }
        
        // Update balances
        tokenBalances[from][token] -= amount;
        
        // Execute transfer
        IERC20(token).safeTransfer(to, amount);
        
        // Record execution
        executedPayments[executionHash] = PaymentExecution({
            from: from,
            to: to,
            amount: amount,
            token: token,
            timestamp: block.timestamp,
            executionHash: executionHash
        });
        
        // Update counters
        userPaymentCount[from]++;
        totalPaymentsExecuted++;
        totalVolumeProcessed += amount;
        
        emit PaymentExecuted(from, to, amount, token, executionHash, block.timestamp);
    }
    
    /**
     * @dev Withdraw ETH from vault
     * @param user User to withdraw for
     * @param amount Amount to withdraw
     */
    function withdraw(address user, uint256 amount) external onlyAuthorized nonReentrant {
        if (user == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        if (ethBalances[user] < amount) revert InsufficientBalance();
        
        ethBalances[user] -= amount;
        
        (bool success, ) = payable(user).call{value: amount}("");
        if (!success) revert TransferFailed();
        
        emit FundsWithdrawn(user, amount, address(0), block.timestamp);
    }
    
    /**
     * @dev Withdraw tokens from vault
     * @param user User to withdraw for
     * @param token Token contract address
     * @param amount Amount to withdraw
     */
    function withdrawToken(
        address user,
        address token,
        uint256 amount
    ) external onlyAuthorized nonReentrant {
        if (user == address(0) || token == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        if (tokenBalances[user][token] < amount) revert InsufficientBalance();
        
        tokenBalances[user][token] -= amount;
        IERC20(token).safeTransfer(user, amount);
        
        emit FundsWithdrawn(user, amount, token, block.timestamp);
    }
    
    /**
     * @dev Get user's ETH balance
     * @param user User address
     * @return balance ETH balance
     */
    function getETHBalance(address user) external view returns (uint256 balance) {
        return ethBalances[user];
    }
    
    /**
     * @dev Get user's token balance
     * @param user User address
     * @param token Token contract address
     * @return balance Token balance
     */
    function getTokenBalance(address user, address token) external view returns (uint256 balance) {
        return tokenBalances[user][token];
    }
    
    /**
     * @dev Get payment execution details
     * @param executionHash Execution hash
     * @return execution Payment execution details
     */
    function getPaymentExecution(bytes32 executionHash) external view returns (PaymentExecution memory execution) {
        return executedPayments[executionHash];
    }
    
    /**
     * @dev Get user payment statistics
     * @param user User address
     * @return paymentCount Number of payments made
     * @return totalVolume Total volume processed
     */
    function getUserStats(address user) external view returns (
        uint256 paymentCount,
        uint256 totalVolume
    ) {
        paymentCount = userPaymentCount[user];
        // Simplified total volume calculation
        totalVolume = ethBalances[user] * paymentCount;
    }
    
    /**
     * @dev Get vault statistics
     * @return totalPayments Total payments executed
     * @return totalVolume Total volume processed
     * @return totalUsers Number of unique users
     */
    function getVaultStats() external view returns (
        uint256 totalPayments,
        uint256 totalVolume,
        uint256 totalUsers
    ) {
        totalPayments = totalPaymentsExecuted;
        totalVolume = totalVolumeProcessed;
        totalUsers = totalPaymentsExecuted; // Simplified
    }
    
    /**
     * @dev Batch execute multiple payments for efficiency
     * @param froms Array of sender addresses
     * @param tos Array of recipient addresses
     * @param amounts Array of amounts
     */
    function batchExecutePayments(
        address[] calldata froms,
        address[] calldata tos,
        uint256[] calldata amounts
    ) external onlyAuthorized nonReentrant whenNotPaused {
        require(froms.length == tos.length && tos.length == amounts.length, "Array length mismatch");
        
        for (uint256 i = 0; i < froms.length; i++) {
            if (tos[i] == address(0)) revert InvalidAddress();
            if (amounts[i] == 0) revert InvalidAmount();
            if (ethBalances[froms[i]] < amounts[i]) revert InsufficientBalance();
            
            // Update balance
            ethBalances[froms[i]] -= amounts[i];
            
            // Execute transfer
            (bool success, ) = payable(tos[i]).call{value: amounts[i]}("");
            if (!success) revert TransferFailed();
            
            // Generate execution hash
            bytes32 executionHash = keccak256(abi.encodePacked(
                froms[i],
                tos[i],
                amounts[i],
                address(0),
                block.timestamp,
                totalPaymentsExecuted + i
            ));
            
            // Record execution
            executedPayments[executionHash] = PaymentExecution({
                from: froms[i],
                to: tos[i],
                amount: amounts[i],
                token: address(0),
                timestamp: block.timestamp,
                executionHash: executionHash
            });
            
            // Update counters
            userPaymentCount[froms[i]]++;
            totalVolumeProcessed += amounts[i];
            
            emit PaymentExecuted(froms[i], tos[i], amounts[i], address(0), executionHash, block.timestamp);
        }
        
        totalPaymentsExecuted += froms.length;
    }
    
    // Admin functions
    
    /**
     * @dev Add authorized caller
     * @param caller Address to authorize
     */
    function addAuthorizedCaller(address caller) external onlyOwner {
        if (caller == address(0)) revert InvalidAddress();
        
        authorizedCallers[caller] = true;
        emit AuthorizedCallerAdded(caller, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Remove authorized caller
     * @param caller Address to remove authorization
     */
    function removeAuthorizedCaller(address caller) external onlyOwner {
        authorizedCallers[caller] = false;
        emit AuthorizedCallerRemoved(caller, msg.sender, block.timestamp);
    }
    
    /**
     * @dev Check if address is authorized caller
     * @param caller Address to check
     * @return isAuthorized Whether address is authorized
     */
    function isAuthorizedCaller(address caller) external view returns (bool isAuthorized) {
        return authorizedCallers[caller];
    }
    
    /**
     * @dev Pause contract
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Emergency withdraw (admin only)
     * @param token Token address (address(0) for ETH)
     * @param amount Amount to withdraw
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyOwner {
        if (amount == 0) revert InvalidAmount();
        
        if (token == address(0)) {
            // Withdraw ETH
            require(address(this).balance >= amount, "Insufficient contract balance");
            (bool success, ) = payable(owner()).call{value: amount}("");
            if (!success) revert TransferFailed();
        } else {
            // Withdraw token
            IERC20(token).safeTransfer(owner(), amount);
        }
    }
    
    /**
     * @dev Get contract ETH balance
     * @return balance Contract's ETH balance
     */
    function getContractBalance() external view returns (uint256 balance) {
        return address(this).balance;
    }
    
    /**
     * @dev Get contract token balance
     * @param token Token contract address
     * @return balance Contract's token balance
     */
    function getContractTokenBalance(address token) external view returns (uint256 balance) {
        return IERC20(token).balanceOf(address(this));
    }
    
    // Fallback functions
    receive() external payable {
        ethBalances[msg.sender] += msg.value;
        emit FundsDeposited(msg.sender, msg.value, address(0), block.timestamp);
    }
    
    fallback() external payable {
        revert("Function not found");
    }
}