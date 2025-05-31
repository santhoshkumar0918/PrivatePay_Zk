from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import asyncio
import signal
import threading
from pathlib import Path
from src.cli import ZerePyCLI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server/app")

class ActionRequest(BaseModel):
    """Request model for agent actions"""
    connection: str
    action: str
    params: Optional[List[str]] = []

class ConfigureRequest(BaseModel):
    """Request model for configuring connections"""
    connection: str
    params: Optional[Dict[str, Any]] = {}

class PrivatePaymentRequest(BaseModel):
    """Request model for private payments"""
    recipient: str
    amount: float
    memo: Optional[str] = ""
    decoy_count: Optional[int] = 4

class FundsRequest(BaseModel):
    """Request model for fund operations"""
    amount: float

class PrivacyAnalysisRequest(BaseModel):
    """Request model for privacy analysis"""
    user_address: Optional[str] = None

class ServerState:
    """Simple state management for the server"""
    def __init__(self):
        self.cli = ZerePyCLI()
        self.agent_running = False
        self.agent_task = None
        self._stop_event = threading.Event()

    def _run_agent_loop(self):
        """Run agent loop in a separate thread"""
        try:
            log_once = False
            while not self._stop_event.is_set():
                if self.cli.agent:
                    try:
                        if not log_once:
                            logger.info("PrivatePay agent monitoring privacy patterns...")
                            log_once = True
                        # Add actual agent loop logic here if needed

                    except Exception as e:
                        logger.error(f"Error in agent action: {e}")
                        if self._stop_event.wait(timeout=30):
                            break
        except Exception as e:
            logger.error(f"Error in agent loop thread: {e}")
        finally:
            self.agent_running = False
            logger.info("PrivatePay agent loop stopped")

    async def start_agent_loop(self):
        """Start the agent loop in background thread"""
        if not self.cli.agent:
            raise ValueError("No agent loaded")
        
        if self.agent_running:
            raise ValueError("Agent already running")

        self.agent_running = True
        self._stop_event.clear()
        self.agent_task = threading.Thread(target=self._run_agent_loop)
        self.agent_task.start()

    async def stop_agent_loop(self):
        """Stop the agent loop"""
        if self.agent_running:
            self._stop_event.set()
            if self.agent_task:
                self.agent_task.join(timeout=5)
            self.agent_running = False

class ZerePyServer:
    def __init__(self):
        self.app = FastAPI(title="PrivatePay ZerePy Server", version="1.0.0")
        self.state = ServerState()
        self.setup_routes()

    def setup_routes(self):
        @self.app.get("/")
        async def root():
            """Server status endpoint"""
            return {
                "status": "running",
                "service": "PrivatePay AI Agent",
                "agent": self.state.cli.agent.name if self.state.cli.agent else None,
                "agent_running": self.state.agent_running,
                "version": "1.0.0"
            }

        @self.app.get("/agents")
        async def list_agents():
            """List available agents"""
            try:
                agents = []
                agents_dir = Path("agents")
                if agents_dir.exists():
                    for agent_file in agents_dir.glob("*.json"):
                        if agent_file.stem != "general":
                            agents.append(agent_file.stem)
                return {"agents": agents}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/agents/{name}/load")
        async def load_agent(name: str):
            """Load a specific agent"""
            try:
                self.state.cli._load_agent_from_file(name)
                return {
                    "status": "success",
                    "agent": name,
                    "message": f"PrivatePay agent '{name}' loaded successfully"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/connections")
        async def list_connections():
            """List all available connections"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No agent loaded")
            
            try:
                connections = {}
                for name, conn in self.state.cli.agent.connection_manager.connections.items():
                    connections[name] = {
                        "configured": conn.is_configured(),
                        "is_llm_provider": getattr(conn, 'is_llm_provider', False)
                    }
                return {"connections": connections}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/agent/action")
        async def agent_action(action_request: ActionRequest):
            """Execute a single agent action"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No agent loaded")
            
            try:
                result = await asyncio.to_thread(
                    self.state.cli.agent.perform_action,
                    connection=action_request.connection,
                    action=action_request.action,
                    params=action_request.params
                )
                return {"status": "success", "result": result}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/agent/start")
        async def start_agent():
            """Start the agent loop"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No agent loaded")
            
            try:
                await self.state.start_agent_loop()
                return {"status": "success", "message": "PrivatePay agent loop started"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/agent/stop")
        async def stop_agent():
            """Stop the agent loop"""
            try:
                await self.state.stop_agent_loop()
                return {"status": "success", "message": "PrivatePay agent loop stopped"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/connections/{name}/configure")
        async def configure_connection(name: str, config: ConfigureRequest):
            """Configure a specific connection"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No agent loaded")
            
            try:
                connection = self.state.cli.agent.connection_manager.connections.get(name)
                if not connection:
                    raise HTTPException(status_code=404, detail=f"Connection {name} not found")
                
                success = connection.configure(**config.params)
                if success:
                    return {"status": "success", "message": f"Connection {name} configured successfully"}
                else:
                    raise HTTPException(status_code=400, detail=f"Failed to configure {name}")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/connections/{name}/status")
        async def connection_status(name: str):
            """Get configuration status of a connection"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No agent loaded")
                
            try:
                connection = self.state.cli.agent.connection_manager.connections.get(name)
                if not connection:
                    raise HTTPException(status_code=404, detail=f"Connection {name} not found")
                    
                return {
                    "name": name,
                    "configured": connection.is_configured(verbose=True),
                    "is_llm_provider": getattr(connection, 'is_llm_provider', False)
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # ========== PRIVATEPAY SPECIFIC ENDPOINTS ==========

        @self.app.post("/privatepay/deposit")
        async def deposit_funds(request: FundsRequest):
            """Deposit funds to PrivatePay vault"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                result = await asyncio.to_thread(
                    self.state.cli.agent.perform_action,
                    connection="monad",
                    action="deposit-funds", 
                    params=[str(request.amount)]
                )
                return {
                    "status": "success",
                    "message": f"Deposited {request.amount} ETH to PrivatePay vault",
                    "result": result
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/privatepay/execute-payment")
        async def execute_private_payment(request: PrivatePaymentRequest):
            """Execute a private payment with AI-generated decoys"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                result = await asyncio.to_thread(
                    self.state.cli.agent.perform_action,
                    connection="monad",
                    action="execute-private-payment",
                    params=[request.recipient, str(request.amount), request.memo, str(request.decoy_count)]
                )
                return {
                    "status": "success", 
                    "message": "Private payment executed successfully",
                    "result": result
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/privatepay/generate-decoys")
        async def generate_decoys(request: FundsRequest):
            """Generate AI-powered decoy transactions"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                result = await asyncio.to_thread(
                    self.state.cli.agent.perform_action,
                    connection="monad",
                    action="generate-ai-decoys",
                    params=[str(request.amount), "4"]
                )
                return {
                    "status": "success",
                    "message": "AI-powered decoys generated",
                    "result": result
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/privatepay/privacy-score")
        async def get_privacy_score(user_address: Optional[str] = None):
            """Get privacy score for user address"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                params = [user_address] if user_address else []
                result = await asyncio.to_thread(
                    self.state.cli.agent.perform_action,
                    connection="monad", 
                    action="get-privacy-score",
                    params=params
                )
                return {
                    "status": "success",
                    "privacy_score": result
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/privatepay/privacy-metrics")
        async def get_privacy_metrics(user_address: Optional[str] = None):
            """Get detailed privacy metrics for user"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                params = [user_address] if user_address else []
                result = await asyncio.to_thread(
                    self.state.cli.agent.perform_action,
                    connection="monad",
                    action="get-privacy-metrics", 
                    params=params
                )
                return {
                    "status": "success",
                    "metrics": result
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/privatepay/global-stats")
        async def get_global_stats():
            """Get global PrivatePay network statistics"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                result = await asyncio.to_thread(
                    self.state.cli.agent.perform_action,
                    connection="monad",
                    action="get-global-stats",
                    params=[]
                )
                return {
                    "status": "success",
                    "global_stats": result
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/privatepay/analyze-patterns")
        async def analyze_privacy_patterns(request: PrivacyAnalysisRequest):
            """AI analysis of user privacy patterns"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                # Use AI to analyze patterns
                prompt = f"""Analyze privacy patterns for user address: {request.user_address or 'current user'}
                
                Provide insights on:
                - Transaction privacy strengths
                - Pattern detection risks  
                - Improvement recommendations
                - Privacy score optimization
                
                Keep response professional and actionable."""
                
                analysis = await asyncio.to_thread(
                    self.state.cli.agent.prompt_llm,
                    prompt
                )
                
                return {
                    "status": "success",
                    "ai_analysis": analysis,
                    "user_address": request.user_address
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/privatepay/recommendations")
        async def get_privacy_recommendations():
            """Get AI-powered privacy recommendations"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                prompt = """Generate 5 specific, actionable recommendations for improving blockchain payment privacy using PrivatePay.
                
                Focus on:
                - Decoy optimization strategies
                - Transaction timing best practices  
                - Privacy score improvement tips
                - Advanced anonymity techniques
                
                Format as numbered list with brief explanations."""
                
                recommendations = await asyncio.to_thread(
                    self.state.cli.agent.prompt_llm,
                    prompt
                )
                
                return {
                    "status": "success",
                    "ai_recommendations": recommendations,
                    "generated_at": "now"
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/privatepay/status")
        async def privatepay_status():
            """Get PrivatePay system status"""
            if not self.state.cli.agent:
                raise HTTPException(status_code=400, detail="No PrivatePay agent loaded")
            
            try:
                # Check Monad connection
                monad_connection = self.state.cli.agent.connection_manager.connections.get("monad")
                monad_status = monad_connection.is_configured() if monad_connection else False
                
                # Check AI connections
                ai_connections = []
                for name in ["openai", "anthropic"]:
                    conn = self.state.cli.agent.connection_manager.connections.get(name)
                    if conn and conn.is_configured():
                        ai_connections.append(name)
                
                return {
                    "status": "operational",
                    "monad_connected": monad_status,
                    "ai_providers": ai_connections,
                    "agent_name": self.state.cli.agent.name,
                    "privacy_features": {
                        "ai_decoy_generation": True,
                        "zk_proof_support": True,
                        "pattern_analysis": True,
                        "privacy_scoring": True
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

def create_app():
    server = ZerePyServer()
    return server.app