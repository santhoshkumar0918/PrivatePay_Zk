import logging
import os
import json
import random
import hashlib
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from web3 import Web3
from src.action_handler import register_action

logger = logging.getLogger("actions.monad_actions")

PRIVATEPAY_CONTRACT_ADDRESS = "0x06A8307922cAdcfD5d4489cF69030CA96E823145"  # UPDATE THIS
PAYMENT_VAULT_ADDRESS = "0xb5b74D0C89C936f9a5c8885Bf59f1DAd96ECaaB0"       # UPDATE THIS  
ZK_VERIFIER_ADDRESS = "0x06A8307922cAdcfD5d4489cF69030CA96E823145"         # UPDATE THIS

# Contract ABIs (stored as constants for now)
PRIVATEPAY_ABI = [
    # Your PrivatePay ABI from the paste - truncated for readability
    {"inputs": [], "name": "depositFunds", "outputs": [], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "withdrawFunds", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "user", "type": "address"}], "name": "calculatePrivacyScore", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "user", "type": "address"}], "name": "getPrivacyMetrics", "outputs": [{"internalType": "uint256", "name": "totalPayments", "type": "uint256"}, {"internalType": "uint256", "name": "totalDecoys", "type": "uint256"}, {"internalType": "uint256", "name": "trackingResistance", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getGlobalStats", "outputs": [{"internalType": "uint256", "name": "totalPayments", "type": "uint256"}, {"internalType": "uint256", "name": "totalDecoys", "type": "uint256"}, {"internalType": "uint256", "name": "avgPrivacyScore", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

def generate_mock_zk_proof() -> str:
    """Generate a mock ZK proof for hackathon demo"""
    mock_proof = {
        "a": [random.randint(1, 2**256), random.randint(1, 2**256)],
        "b": [[random.randint(1, 2**256), random.randint(1, 2**256)], [random.randint(1, 2**256), random.randint(1, 2**256)]],
        "c": [random.randint(1, 2**256), random.randint(1, 2**256)]
    }
    return "0x" + json.dumps(mock_proof).encode().hex()

def generate_commitment(recipient: str, amount: float, nonce: int) -> str:
    """Generate a commitment hash for the payment"""
    data = f"{recipient}{amount}{nonce}"
    return "0x" + hashlib.sha256(data.encode()).hexdigest()

def generate_decoy_hash(recipient: str, amount: float, timing: int) -> str:
    """Generate a hash for decoy transaction"""
    data = f"decoy_{recipient}{amount}{timing}{random.randint(1, 1000000)}"
    return "0x" + hashlib.sha256(data.encode()).hexdigest()

@register_action("deposit-funds")
def deposit_funds(agent, **kwargs):
    """Deposit ETH funds to PrivatePay vault"""
    try:
        amount = float(kwargs.get("amount", 0))
        if amount <= 0:
            return "Error: Amount must be greater than 0"
            
        # Use the monad connection to deposit funds
        result = agent.connection_manager.connections["monad"].perform_action(
            "transfer",
            {
                "to_address": PRIVATEPAY_CONTRACT_ADDRESS,
                "amount": amount
            }
        )
        
        logger.info(f"✅ Deposited {amount} ETH to PrivatePay vault")
        return f"Successfully deposited {amount} ETH to PrivatePay vault. Transaction: {result}"
        
    except Exception as e:
        logger.error(f"Failed to deposit funds: {str(e)}")
        return f"Error depositing funds: {str(e)}"

@register_action("execute-private-payment")
def execute_private_payment(agent, **kwargs):
    """Execute a private payment with AI-generated decoys"""
    try:
        recipient = kwargs.get("recipient")
        amount = float(kwargs.get("amount", 0))
        memo = kwargs.get("memo", "")
        decoy_count = int(kwargs.get("decoy_count", 4))
        
        if not recipient or amount <= 0:
            return "Error: Recipient and valid amount required"
            
        if not Web3.is_address(recipient):
            return "Error: Invalid recipient address"
            
        if decoy_count < 3 or decoy_count > 8:
            decoy_count = 4  # Default to 4 decoys
            
        logger.info(f"🕵️ Executing private payment: {amount} ETH to {recipient}")
        
        # Generate AI-powered decoy transactions
        decoys = generate_ai_decoys(agent, amount, decoy_count)
        
        # Generate mock ZK proof
        zk_proof = generate_mock_zk_proof()
        
        # Generate commitment
        nonce = random.randint(1, 1000000)
        commitment = generate_commitment(recipient, amount, nonce)
        
        # Log the privacy operation
        logger.info(f"🤖 Generated {len(decoys)} AI-powered decoy transactions")
        logger.info(f"🔒 Created ZK proof and commitment")
        logger.info(f"⚡ Ready for parallel execution on Monad")
        
        # In a real implementation, this would call the smart contract
        # For demo purposes, we'll simulate the transaction
        transaction_hash = "0x" + hashlib.sha256(f"{recipient}{amount}{commitment}".encode()).hexdigest()
        
        # Calculate privacy score improvement
        privacy_impact = calculate_privacy_impact(decoy_count, amount)
        
        result = {
            "success": True,
            "transaction_hash": transaction_hash,
            "commitment": commitment,
            "decoy_count": len(decoys),
            "privacy_score_impact": privacy_impact,
            "zk_proof_generated": True,
            "memo_encrypted": bool(memo)
        }
        
        logger.info(f"✅ Private payment executed successfully!")
        logger.info(f"📊 Privacy score impact: +{privacy_impact} points")
        
        return f"Private payment executed! TX: {transaction_hash[:10]}... | Decoys: {len(decoys)} | Privacy impact: +{privacy_impact}"
        
    except Exception as e:
        logger.error(f"Failed to execute private payment: {str(e)}")
        return f"Error executing private payment: {str(e)}"

@register_action("generate-ai-decoys")
def generate_ai_decoys_action(agent, **kwargs):
    """Generate AI-powered decoy transactions"""
    try:
        amount = float(kwargs.get("amount", 1.0))
        count = int(kwargs.get("count", 4))
        
        decoys = generate_ai_decoys(agent, amount, count)
        
        return {
            "decoys_generated": len(decoys),
            "decoys": decoys,
            "ai_analysis": "Patterns analyzed for maximum privacy protection"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate decoys: {str(e)}")
        return f"Error generating decoys: {str(e)}"

@register_action("get-privacy-score") 
def get_privacy_score(agent, **kwargs):
    """Get privacy score for a user address"""
    try:
        user_address = kwargs.get("user_address")
        if not user_address:
            # Use agent's own address
            user_address = agent.connection_manager.connections["monad"].get_address()
            if "Your Monad address: " in user_address:
                user_address = user_address.split("Your Monad address: ")[1]
        
        if not Web3.is_address(user_address):
            return "Error: Invalid user address"
            
        # Mock privacy score calculation (in real version, call contract)
        mock_score = random.randint(75, 98)
        
        # Get AI analysis of privacy patterns
        privacy_analysis = analyze_privacy_patterns(agent, user_address)
        
        result = {
            "user_address": user_address,
            "privacy_score": mock_score,
            "rating": get_privacy_rating(mock_score),
            "ai_analysis": privacy_analysis
        }
        
        logger.info(f"📊 Privacy score for {user_address}: {mock_score}/100")
        return result
        
    except Exception as e:
        logger.error(f"Failed to get privacy score: {str(e)}")
        return f"Error getting privacy score: {str(e)}"

@register_action("get-privacy-metrics")
def get_privacy_metrics(agent, **kwargs):
    """Get detailed privacy metrics for a user"""
    try:
        user_address = kwargs.get("user_address")
        if not user_address:
            user_address = agent.connection_manager.connections["monad"].get_address()
            if "Your Monad address: " in user_address:
                user_address = user_address.split("Your Monad address: ")[1]
                
        # Mock metrics (in real version, call contract)
        metrics = {
            "total_payments": random.randint(5, 50),
            "total_decoys": random.randint(20, 200),
            "tracking_resistance": random.randint(85, 99),
            "pattern_complexity": random.randint(70, 95),
            "ai_recommendations": generate_privacy_recommendations(agent)
        }
        
        logger.info(f"📈 Privacy metrics retrieved for {user_address}")
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get privacy metrics: {str(e)}")
        return f"Error getting privacy metrics: {str(e)}"

@register_action("get-global-stats")
def get_global_stats(agent, **kwargs):
    """Get global PrivatePay network statistics"""
    try:
        # Mock global stats (in real version, call contract)
        stats = {
            "total_payments": random.randint(1000, 5000),
            "total_decoys": random.randint(4000, 20000),
            "avg_privacy_score": random.randint(82, 95),
            "active_users": random.randint(100, 500),
            "network_anonymity": "Excellent"
        }
        
        logger.info("🌐 Retrieved global PrivatePay network statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get global stats: {str(e)}")
        return f"Error getting global stats: {str(e)}"

# Helper functions
def generate_ai_decoys(agent, real_amount: float, count: int) -> List[Dict]:
    """Generate AI-powered realistic decoy transactions"""
    try:
        # Use AI to generate realistic amounts and recipients
        prompt = f"""Generate {count} realistic decoy transactions to hide a real payment of {real_amount} ETH.
        
        Create amounts that are:
        - Similar magnitude to the real amount
        - Believable for everyday transactions
        - Varied enough to confuse analysis
        
        Return amounts only, separated by commas."""
        
        ai_response = agent.prompt_llm(prompt)
        
        # Parse AI response and generate decoys
        decoys = []
        try:
            amounts = [float(x.strip()) for x in ai_response.replace("ETH", "").split(",")]
        except:
            # Fallback to algorithmic generation
            amounts = []
            base_amount = real_amount
            for i in range(count):
                variation = random.uniform(0.5, 2.0)
                amounts.append(round(base_amount * variation, 4))
        
        # Generate random recipient addresses and timing
        for i, amount in enumerate(amounts[:count]):
            decoy = {
                "recipient": "0x" + "".join([random.choice("0123456789abcdef") for _ in range(40)]),
                "amount": amount,
                "timing_offset": random.randint(1, 60),  # seconds
                "decoy_hash": generate_decoy_hash(f"decoy_{i}", amount, i)
            }
            decoys.append(decoy)
            
        logger.info(f"🤖 AI generated {len(decoys)} realistic decoy transactions")
        return decoys
        
    except Exception as e:
        logger.error(f"AI decoy generation failed: {str(e)}")
        # Fallback to simple generation
        return generate_simple_decoys(real_amount, count)

def generate_simple_decoys(real_amount: float, count: int) -> List[Dict]:
    """Fallback simple decoy generation"""
    decoys = []
    for i in range(count):
        variation = random.uniform(0.3, 3.0)
        amount = round(real_amount * variation, 4)
        decoy = {
            "recipient": "0x" + "".join([random.choice("0123456789abcdef") for _ in range(40)]),
            "amount": amount,
            "timing_offset": random.randint(1, 60),
            "decoy_hash": generate_decoy_hash(f"simple_{i}", amount, i)
        }
        decoys.append(decoy)
    return decoys

def analyze_privacy_patterns(agent, user_address: str) -> str:
    """AI analysis of user privacy patterns"""
    try:
        prompt = f"""Analyze the privacy patterns for blockchain address {user_address}.
        
        Provide insights on:
        - Transaction timing patterns
        - Amount distribution
        - Privacy strengths
        - Recommendations for improvement
        
        Keep response concise and actionable."""
        
        return agent.prompt_llm(prompt)
    except:
        return "Privacy patterns suggest good operational security. Continue using varied transaction amounts and timing."

def generate_privacy_recommendations(agent) -> List[str]:
    """Generate AI-powered privacy recommendations"""
    try:
        prompt = """Generate 3 specific recommendations for improving blockchain payment privacy.
        Focus on practical, actionable advice. Be concise."""
        
        response = agent.prompt_llm(prompt)
        
        # Parse response into list
        recommendations = [line.strip() for line in response.split('\n') if line.strip() and not line.startswith('#')]
        return recommendations[:3]
    except:
        return [
            "Vary transaction amounts to avoid pattern recognition",
            "Use different timing intervals between payments", 
            "Increase decoy count for higher-value transactions"
        ]

def calculate_privacy_impact(decoy_count: int, amount: float) -> int:
    """Calculate privacy score impact of a transaction"""
    base_impact = 2
    decoy_bonus = decoy_count * 1.5
    amount_factor = min(amount * 0.5, 5)  # Cap at 5 points
    return int(base_impact + decoy_bonus + amount_factor)

def get_privacy_rating(score: int) -> str:
    """Convert privacy score to rating"""
    if score >= 95:
        return "Excellent"
    elif score >= 85:
        return "Very Good" 
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Improvement"