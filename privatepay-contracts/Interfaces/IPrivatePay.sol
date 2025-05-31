// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IPrivatePay
 * @dev Interface for PrivatePay main contract
 */
interface IPrivatePay {
    
    // Structs
    struct UserPrivacyData {
        uint256 totalTransactions;
        uint256 successfulDecoys;
        uint256 patternComplexity;
        uint256 privacyScore;
        uint256 lastTransactionTime;
    }
    
    struct PrivatePaymentRequest {
        address recipient;
        uint256 amount;
        bytes32 commitment; // ZK commitment
        uint256 decoyCount;
        bytes zkProof;
        string memo; // Encrypted memo
    }
    
    struct DecoyTransaction {
        address recipient;
        uint256 amount;
        uint256 timingOffset;
        bytes32 decoyHash;
    }
    
    // Events
    event PrivatePaymentExecuted(
        address indexed sender,
        bytes32 indexed commitment,
        uint256 decoyCount,
        uint256 privacyScore,
        uint256 timestamp
    );
    
    event DecoyGenerated(
        address indexed sender,
        bytes32 decoyHash,
        uint256 amount,
        uint256 timestamp
    );
    
    event PrivacyScoreUpdated(
        address indexed user,
        uint256 oldScore,
        uint256 newScore,
        uint256 timestamp
    );
    
    // Core Functions
    
    /**
     * @dev Execute a private payment with ZK proofs and decoys
     * @param request The private payment request
     * @param decoys Array of decoy transactions
     */
    function executePrivatePayment(
        PrivatePaymentRequest calldata request,
        DecoyTransaction[] calldata decoys
    ) external payable;
    
    /**
     * @dev Deposit funds to PrivatePay vault
     */
    function depositFunds() external payable;
    
    /**
     * @dev Withdraw funds from PrivatePay vault
     * @param amount Amount to withdraw
     */
    function withdrawFunds(uint256 amount) external;
    
    /**
     * @dev Calculate privacy score for a user
     * @param user User address
     * @return Privacy score (0-100)
     */
    function calculatePrivacyScore(address user) external view returns (uint256);
    
    /**
     * @dev Get user privacy metrics
     * @param user User address
     * @return totalPayments Total payments made
     * @return totalDecoys Total decoys generated
     * @return trackingResistance Tracking resistance percentage
     */
    function getPrivacyMetrics(address user) external view returns (
        uint256 totalPayments,
        uint256 totalDecoys,
        uint256 trackingResistance
    );
    
    /**
     * @dev Get user's vault balance
     * @param user User address
     * @return balance User's vault balance
     */
    function getVaultBalance(address user) external view returns (uint256 balance);
    
    /**
     * @dev Get global privacy statistics
     * @return totalPayments Total private payments
     * @return totalDecoys Total decoys generated
     * @return avgPrivacyScore Average privacy score
     */
    function getGlobalStats() external view returns (
        uint256 totalPayments,
        uint256 totalDecoys,
        uint256 avgPrivacyScore
    );
    
    /**
     * @dev Get user privacy data
     * @param user User address
     * @return userData Complete user privacy data struct
     */
    function userPrivacyData(address user) external view returns (UserPrivacyData memory userData);
    
    /**
     * @dev Check if commitment has been used
     * @param commitment ZK commitment hash
     * @return isUsed Whether commitment has been used
     */
    function usedCommitments(bytes32 commitment) external view returns (bool isUsed);
    
    /**
     * @dev Get vault balances for a user
     * @param user User address
     * @return balance User's vault balance
     */
    function vaultBalances(address user) external view returns (uint256 balance);
}
