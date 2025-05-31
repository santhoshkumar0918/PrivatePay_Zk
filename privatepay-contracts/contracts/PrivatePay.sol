// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "../Interfaces/IZKVerifier.sol";
import "../Interfaces/IPaymentVault.sol";

/**
 * @title PrivatePay
 * @dev Main contract for private payments using ZK proofs and AI-generated decoys
 * @notice First consumer-grade private payment platform on Monad
 */
contract PrivatePay is ReentrancyGuard, Ownable, Pausable {
    
    // Core contracts
    IZKVerifier public immutable zkVerifier;
    IPaymentVault public immutable paymentVault;
    
    // Privacy tracking
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
    
    // State variables
    mapping(address => UserPrivacyData) public userPrivacyData;
    mapping(bytes32 => bool) public usedCommitments;
    mapping(address => uint256) public vaultBalances;
    
    // Privacy metrics
    uint256 public totalPrivatePayments;
    uint256 public totalDecoysGenerated;
    uint256 public constant MIN_DECOY_COUNT = 3;
    uint256 public constant MAX_DECOY_COUNT = 8;
    uint256 public constant MIN_PRIVACY_SCORE = 50;
    
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
    
    event FundsDeposited(
        address indexed user,
        uint256 amount,
        uint256 timestamp
    );
    
    event FundsWithdrawn(
        address indexed user,
        uint256 amount,
        uint256 timestamp
    );
    
    // Errors
    error InvalidDecoyCount();
    error InvalidAmount();
    error InsufficientBalance();
    error InvalidZKProof();
    error CommitmentAlreadyUsed();
    error PrivacyScoreTooLow();
    error InvalidRecipient();
    
    constructor(
        address _zkVerifier,
        address _paymentVault
    ) Ownable(msg.sender) {
        zkVerifier = IZKVerifier(_zkVerifier);
        paymentVault = IPaymentVault(_paymentVault);
    }
    
    /**
     * @dev Execute a private payment with ZK proofs and decoys
     * @param request The private payment request
     * @param decoys Array of decoy transactions
     */
    function executePrivatePayment(
        PrivatePaymentRequest calldata request,
        DecoyTransaction[] calldata decoys
    ) external payable nonReentrant whenNotPaused {
        // Validate inputs
        if (request.amount == 0) revert InvalidAmount();
        if (request.recipient == address(0)) revert InvalidRecipient();
        if (decoys.length < MIN_DECOY_COUNT || decoys.length > MAX_DECOY_COUNT) {
            revert InvalidDecoyCount();
        }
        if (usedCommitments[request.commitment]) revert CommitmentAlreadyUsed();
        
        // Check user balance
        if (vaultBalances[msg.sender] < request.amount) revert InsufficientBalance();
        
        // Verify ZK proof
        if (!_verifyZKProof(request, decoys)) revert InvalidZKProof();
        
        // Check privacy score requirement
        uint256 currentPrivacyScore = calculatePrivacyScore(msg.sender);
        if (currentPrivacyScore < MIN_PRIVACY_SCORE) revert PrivacyScoreTooLow();
        
        // Mark commitment as used
        usedCommitments[request.commitment] = true;
        
        // Process decoys (generate noise)
        _processDecoys(decoys);
        
        // Execute the real payment through vault
        vaultBalances[msg.sender] -= request.amount;
        paymentVault.executePayment(msg.sender, request.recipient, request.amount);
        
        // Update privacy data
        _updatePrivacyData(msg.sender, decoys.length);
        
        // Update global metrics
        totalPrivatePayments++;
        totalDecoysGenerated += decoys.length;
        
        emit PrivatePaymentExecuted(
            msg.sender,
            request.commitment,
            decoys.length,
            userPrivacyData[msg.sender].privacyScore,
            block.timestamp
        );
    }
    
    /**
     * @dev Deposit funds to PrivatePay vault
     */
    function depositFunds() external payable nonReentrant {
        if (msg.value == 0) revert InvalidAmount();
        
        vaultBalances[msg.sender] += msg.value;
        paymentVault.depositETH{value: msg.value}();
        
        emit FundsDeposited(msg.sender, msg.value, block.timestamp);
    }
    
    /**
     * @dev Withdraw funds from PrivatePay vault
     * @param amount Amount to withdraw
     */
    function withdrawFunds(uint256 amount) external nonReentrant {
        if (amount == 0) revert InvalidAmount();
        if (vaultBalances[msg.sender] < amount) revert InsufficientBalance();
        
        vaultBalances[msg.sender] -= amount;
        paymentVault.withdraw(msg.sender, amount);
        
        emit FundsWithdrawn(msg.sender, amount, block.timestamp);
    }
    
    /**
     * @dev Calculate privacy score for a user
     * @param user User address
     * @return Privacy score (0-100)
     */
    function calculatePrivacyScore(address user) public view returns (uint256) {
        UserPrivacyData memory userData = userPrivacyData[user];
        
        if (userData.totalTransactions == 0) {
            return 50; // Default score for new users
        }
        
        uint256 baseScore = 60;
        
        // Transaction volume bonus (up to 20 points)
        uint256 volumeBonus = userData.totalTransactions > 20 ? 20 : userData.totalTransactions;
        
        // Decoy effectiveness bonus (up to 25 points)
        uint256 decoyRatio = (userData.successfulDecoys * 100) / userData.totalTransactions;
        uint256 decoyBonus = (decoyRatio * 25) / 100;
        
        // Pattern complexity bonus (up to 15 points)
        uint256 complexityBonus = userData.patternComplexity > 15 ? 15 : userData.patternComplexity;
        
        uint256 totalScore = baseScore + volumeBonus + decoyBonus + complexityBonus;
        
        return totalScore > 100 ? 100 : totalScore;
    }
    
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
    ) {
        UserPrivacyData memory userData = userPrivacyData[user];
        totalPayments = userData.totalTransactions;
        totalDecoys = userData.successfulDecoys;
        
        if (totalPayments > 0) {
            trackingResistance = 75 + ((userData.patternComplexity * 25) / 100);
            trackingResistance = trackingResistance > 99 ? 99 : trackingResistance;
        } else {
            trackingResistance = 75;
        }
    }
    
    /**
     * @dev Get user's vault balance
     * @param user User address
     * @return balance User's vault balance
     */
    function getVaultBalance(address user) external view returns (uint256 balance) {
        return vaultBalances[user];
    }
    
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
    ) {
        totalPayments = totalPrivatePayments;
        totalDecoys = totalDecoysGenerated;
        
        // Calculate average privacy score (simplified)
        avgPrivacyScore = totalPayments > 0 ? 85 : 50; // Mock calculation
    }
    
    /**
     * @dev Verify ZK proof for private payment
     * @param request Payment request
     * @param decoys Decoy transactions
     * @return isValid Whether the proof is valid
     */
    function _verifyZKProof(
        PrivatePaymentRequest calldata request,
        DecoyTransaction[] calldata decoys
    ) internal returns (bool isValid) {
        // Prepare public inputs for ZK verification
        uint256[] memory publicInputs = new uint256[](3);
        publicInputs[0] = uint256(request.commitment);
        publicInputs[1] = request.amount;
        publicInputs[2] = decoys.length;
        
        // Call ZK verifier (this modifies state in verifier contract)
        return zkVerifier.verifyPaymentProof(request.zkProof, publicInputs);
    }
    
    /**
     * @dev Process decoy transactions to create noise
     * @param decoys Array of decoy transactions
     */
    function _processDecoys(DecoyTransaction[] calldata decoys) internal {
        for (uint256 i = 0; i < decoys.length; i++) {
            // Generate decoy hash and emit event to create blockchain noise
            bytes32 decoyHash = keccak256(abi.encodePacked(
                decoys[i].recipient,
                decoys[i].amount,
                decoys[i].timingOffset,
                block.timestamp,
                i
            ));
            
            emit DecoyGenerated(
                msg.sender,
                decoyHash,
                decoys[i].amount,
                block.timestamp
            );
        }
    }
    
    /**
     * @dev Update user privacy data
     * @param user User address
     * @param decoyCount Number of decoys used
     */
    function _updatePrivacyData(address user, uint256 decoyCount) internal {
        UserPrivacyData storage userData = userPrivacyData[user];
        
        uint256 oldScore = userData.privacyScore;
        
        userData.totalTransactions++;
        userData.successfulDecoys += decoyCount;
        userData.lastTransactionTime = block.timestamp;
        
        // Update pattern complexity based on transaction variety
        if (userData.totalTransactions > 1) {
            userData.patternComplexity = (userData.patternComplexity + decoyCount + 1) / 2;
        } else {
            userData.patternComplexity = decoyCount;
        }
        
        // Recalculate privacy score
        userData.privacyScore = calculatePrivacyScore(user);
        
        emit PrivacyScoreUpdated(user, oldScore, userData.privacyScore, block.timestamp);
    }
    
    // Admin functions
    function pause() external onlyOwner {
        _pause();
    }
    
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Emergency function to update privacy score manually
     * @param user User address
     * @param newScore New privacy score
     */
    function updatePrivacyScore(address user, uint256 newScore) external onlyOwner {
        require(newScore <= 100, "Score too high");
        
        uint256 oldScore = userPrivacyData[user].privacyScore;
        userPrivacyData[user].privacyScore = newScore;
        
        emit PrivacyScoreUpdated(user, oldScore, newScore, block.timestamp);
    }
}