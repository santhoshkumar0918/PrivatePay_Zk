// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IPaymentVault
 * @dev Interface for secure payment vault operations
 */
interface IPaymentVault {
    
    /**
     * @dev Execute a payment (ETH)
     * @param from Sender address
     * @param to Recipient address
     * @param amount Amount to send
     */
    function executePayment(
        address from,
        address to,
        uint256 amount
    ) external;
    
    /**
     * @dev Execute a token payment
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
    ) external;
    
    /**
     * @dev Deposit ETH to the vault
     */
    function depositETH() external payable;
    
    /**
     * @dev Deposit ERC20 tokens to the vault
     * @param token Token contract address
     * @param amount Amount to deposit
     */
    function depositToken(address token, uint256 amount) external;
    
    /**
     * @dev Withdraw ETH from vault
     * @param user User to withdraw for
     * @param amount Amount to withdraw
     */
    function withdraw(address user, uint256 amount) external;
    
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
    ) external;
    
    /**
     * @dev Get user's ETH balance
     * @param user User address
     * @return balance ETH balance
     */
    function getETHBalance(address user) external view returns (uint256 balance);
    
    /**
     * @dev Get user's token balance
     * @param user User address
     * @param token Token contract address
     * @return balance Token balance
     */
    function getTokenBalance(address user, address token) external view returns (uint256 balance);
    
    /**
     * @dev Check if address is authorized caller
     * @param caller Address to check
     * @return isAuthorized Whether address is authorized
     */
    function isAuthorizedCaller(address caller) external view returns (bool isAuthorized);
    
    /**
     * @dev Get user payment statistics
     * @param user User address
     * @return paymentCount Number of payments made
     * @return totalVolume Total volume processed
     */
    function getUserStats(address user) external view returns (
        uint256 paymentCount,
        uint256 totalVolume
    );
    
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
    ) external;
}