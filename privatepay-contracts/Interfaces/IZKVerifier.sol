// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IZKVerifier
 * @dev Interface for ZK proof verification contract
 */
interface IZKVerifier {
    /**
     * @dev Verify a ZK proof for private payment
     * @param proofData Encoded proof data
     * @param publicInputs Public inputs for verification
     * @return isValid Whether the proof is valid
     */
    function verifyPaymentProof(
        bytes calldata proofData,
        uint256[] calldata publicInputs
    ) external returns (bool isValid);
    
    /**
     * @dev Verify a batch of ZK proofs
     * @param proofsData Array of encoded proof data
     * @param publicInputsArray Array of public inputs
     * @return results Array of verification results
     */
    function verifyBatchProofs(
        bytes[] calldata proofsData,
        uint256[][] calldata publicInputsArray
    ) external returns (bool[] memory results);
    
    /**
     * @dev Verify proof for decoy transaction generation
     * @param decoyCommitment Commitment for decoy
     * @param realCommitment Commitment for real transaction
     * @param proofData ZK proof data
     * @return isValid Whether the decoy proof is valid
     */
    function verifyDecoyProof(
        bytes32 decoyCommitment,
        bytes32 realCommitment,
        bytes calldata proofData
    ) external view returns (bool isValid);
    
    /**
     * @dev Get verification statistics
     * @return totalVerified Total proofs verified successfully
     * @return totalFailed Total proofs that failed verification
     * @return successRate Success rate percentage
     */
    function getVerificationStats() external view returns (
        uint256 totalVerified,
        uint256 totalFailed,
        uint256 successRate
    );
    
    /**
     * @dev Check if a proof has been verified before
     * @param proofData Proof data
     * @param publicInputs Public inputs
     * @return isVerified Whether proof was previously verified
     */
    function isProofVerified(
        bytes calldata proofData,
        uint256[] calldata publicInputs
    ) external view returns (bool isVerified);
}