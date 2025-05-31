import requests
from typing import Optional, List, Dict, Any

class ZerePyClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    # ========== EXISTING METHODS ==========
    def get_status(self) -> Dict[str, Any]:
        """Get server status"""
        return self._make_request("GET", "/")

    def list_agents(self) -> List[str]:
        """List available agents"""
        response = self._make_request("GET", "/agents")
        return response.get("agents", [])

    def load_agent(self, agent_name: str) -> Dict[str, Any]:
        """Load a specific agent"""
        return self._make_request("POST", f"/agents/{agent_name}/load")

    def list_connections(self) -> Dict[str, Any]:
        """List available connections"""
        return self._make_request("GET", "/connections")

    def perform_action(self, connection: str, action: str, params: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute an agent action"""
        data = {
            "connection": connection,
            "action": action,
            "params": params or []
        }
        return self._make_request("POST", "/agent/action", json=data)

    def start_agent(self) -> Dict[str, Any]:
        """Start the agent loop"""
        return self._make_request("POST", "/agent/start")

    def stop_agent(self) -> Dict[str, Any]:
        """Stop the agent loop"""
        return self._make_request("POST", "/agent/stop")

    # ========== PRIVATEPAY SPECIFIC METHODS ==========

    def deposit_funds(self, amount: float) -> Dict[str, Any]:
        """Deposit funds to PrivatePay vault"""
        data = {"amount": amount}
        return self._make_request("POST", "/privatepay/deposit", json=data)

    def execute_private_payment(
        self, 
        recipient: str, 
        amount: float, 
        memo: str = "", 
        decoy_count: int = 4
    ) -> Dict[str, Any]:
        """Execute a private payment with AI-generated decoys"""
        data = {
            "recipient": recipient,
            "amount": amount,
            "memo": memo,
            "decoy_count": decoy_count
        }
        return self._make_request("POST", "/privatepay/execute-payment", json=data)

    def generate_decoys(self, amount: float) -> Dict[str, Any]:
        """Generate AI-powered decoy transactions"""
        data = {"amount": amount}
        return self._make_request("POST", "/privatepay/generate-decoys", json=data)

    def get_privacy_score(self, user_address: Optional[str] = None) -> Dict[str, Any]:
        """Get privacy score for user address"""
        params = {"user_address": user_address} if user_address else {}
        return self._make_request("GET", "/privatepay/privacy-score", params=params)

    def get_privacy_metrics(self, user_address: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed privacy metrics for user"""
        params = {"user_address": user_address} if user_address else {}
        return self._make_request("GET", "/privatepay/privacy-metrics", params=params)

    def get_global_stats(self) -> Dict[str, Any]:
        """Get global PrivatePay network statistics"""
        return self._make_request("GET", "/privatepay/global-stats")

    def analyze_privacy_patterns(self, user_address: Optional[str] = None) -> Dict[str, Any]:
        """AI analysis of user privacy patterns"""
        data = {"user_address": user_address} if user_address else {}
        return self._make_request("POST", "/privatepay/analyze-patterns", json=data)

    def get_privacy_recommendations(self) -> Dict[str, Any]:
        """Get AI-powered privacy recommendations"""
        return self._make_request("GET", "/privatepay/recommendations")

    def get_privatepay_status(self) -> Dict[str, Any]:
        """Get PrivatePay system status"""
        return self._make_request("GET", "/privatepay/status")

    # ========== CONVENIENCE METHODS ==========

    def quick_private_payment(self, recipient: str, amount: float) -> Dict[str, Any]:
        """Quick private payment with default settings"""
        return self.execute_private_payment(recipient, amount)

    def privacy_dashboard(self, user_address: Optional[str] = None) -> Dict[str, Any]:
        """Get complete privacy dashboard data"""
        try:
            score = self.get_privacy_score(user_address)
            metrics = self.get_privacy_metrics(user_address)
            recommendations = self.get_privacy_recommendations()
            
            return {
                "status": "success",
                "dashboard": {
                    "privacy_score": score.get("privacy_score", {}),
                    "metrics": metrics.get("metrics", {}),
                    "recommendations": recommendations.get("ai_recommendations", ""),
                    "user_address": user_address
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def network_overview(self) -> Dict[str, Any]:
        """Get complete network overview"""
        try:
            global_stats = self.get_global_stats()
            system_status = self.get_privatepay_status()
            
            return {
                "status": "success",
                "network": {
                    "global_stats": global_stats.get("global_stats", {}),
                    "system_status": system_status,
                    "timestamp": "now"
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ========== EXAMPLE USAGE ==========

if __name__ == "__main__":
    # Example usage of the PrivatePay client
    client = ZerePyClient()
    
    try:
        # Load PrivatePay agent
        print("Loading PrivatePay agent...")
        load_result = client.load_agent("privatepay")
        print(f"Agent loaded: {load_result}")
        
        # Get system status
        print("\nChecking PrivatePay status...")
        status = client.get_privatepay_status()
        print(f"System status: {status}")
        
        # Get privacy dashboard
        print("\nFetching privacy dashboard...")
        dashboard = client.privacy_dashboard()
        print(f"Dashboard: {dashboard}")
        
        # Execute a test private payment
        print("\nExecuting test private payment...")
        test_payment = client.execute_private_payment(
            recipient="0x742d35Cc6663C4532C5cc9a6C3d9C4D5A5e1234A",
            amount=0.1,
            memo="Test private payment",
            decoy_count=4
        )
        print(f"Payment result: {test_payment}")
        
        # Get network overview
        print("\nFetching network overview...")
        overview = client.network_overview()
        print(f"Network overview: {overview}")
        
    except Exception as e:
        print(f"Error: {e}")