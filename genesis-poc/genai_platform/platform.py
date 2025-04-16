import functools
import json
import os
import uvicorn
import asyncio
import aiohttp
from fastapi import FastAPI, Request
from typing import Dict, Type

from .base import Action, Agent

class GenAIPlatform:
    """Central platform for managing agents, actions, and models."""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(GenAIPlatform, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.app = FastAPI()
        self.agents: Dict[str, Type['Agent']] = {}
        self.actions: Dict[str, Type['Action']] = {}
        self.models: Dict[str, Type['Model']] = {}
        self._register_routes()
    
    def _register_routes(self):
        @self.app.post("/agents/{agent_name}/invoke")
        async def invoke_agent(agent_name: str, request: Request):
            try:
                data = await request.json()
                if agent_name not in self.agents:
                    return {"error": f"Agent {agent_name} not found"}
                return await self.agents[agent_name].invoke_remote(data)
            except ValueError as e:
                return {"error": f"Invalid JSON in request: {str(e)}"}
            except Exception as e:
                return {"error": f"Error processing request: {str(e)}"}
            
        @self.app.post("/actions/{action_name}/invoke_action")
        async def invoke_action(action_name: str, request: Request):
            try:
                data = await request.json()
                if action_name not in self.actions:
                    return {"error": f"Action {action_name} not found"}
                config = {
                    "configurable": {
                        "passenger_id": "3442 587242",
                        "thread_id": "9339db9c-872a-4b20-9c49-908fe5056e32",
                    }
                }
                results = self.actions[action_name].invoke(data, config=config)
                return results
            except Exception as e:
                return {"error": f"Failed to decode JSON response: {str(e)}"}
            
        @self.app.post("/models/{model_name}/invoke_model")
        async def invoke_model(model_name: str, request: Request):
            data = await request.json()
            if model_name not in self.models:
                return {"error": f"Model {model_name} not found"}
            return await self.models[model_name].invoke_model(data)

    def register_agent(self, name: str, agent_cls: Type['Agent']):
        """Register an agent with the platform."""
        self.agents[name] = agent_cls()
        
    def register_action(self, name: str, action_cls: Type['Action']):
        """Register an action with the platform."""
        self.actions[name] = action_cls
        
    def register_model(self, name: str, model_cls: Type['Model']):
        """Register a model with the platform."""
        self.models[name] = model_cls()

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Starts the FastAPI server."""
        uvicorn.run(self.app, host=host, port=port)

# Platform instance
platform = GenAIPlatform()

def platform_agent(name: str):
    """Decorator to register an agent with the platform."""
    def decorator(cls):
        platform.register_agent(name, cls)
        return cls
    return decorator

def platform_action(name: str):
    """Decorator to register an action with the platform."""
    def decorator(cls):
        platform.register_action(name, cls)
        return cls
    return decorator

def platform_model(name: str):
    """Decorator to register a model with the platform."""
    def decorator(cls):
        platform.register_model(name, cls)
        return cls
    return decorator

def platform_agent_route_async(name: str):
    """Decorator to route method calls through the platform."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Route the call through the platform
            if os.environ.get('GENESIS_ENABLED') == "True":
                url = f"http://localhost:8000/agents/{name}/invoke"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=args[0]) as response:
                        if response.status == 200:
                            return json.loads(await response.text())
                        else:
                            return f"Error: {response.status}"
            else:
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator

def platform_agent_route_sync(name: str):
    """Decorator to route method calls through the platform."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Route the call through the platform
            if os.environ.get('GENESIS_ENABLED') == "True":
                url = f"http://localhost:8000/agents/{name}/invoke"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=args[0]) as response:
                        if response.status == 200:
                            return await response.json()
                        return f"Error: {response.status}"
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


def platform_action_route_sync(name: str):
    """Decorator to route method calls through the platform."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Route the call through the platform
            if os.environ.get('GENESIS_ENABLED') == "True":
                url = f"http://localhost:8000/actions/{args[0]['name']}/invoke_action"
                async def async_post_request():
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=args[0]["args"]) as response:
                            if response.status == 200:
                                return await response.text()  # Return the response text if OK
                            else:
                                return f"Error: {response.status}"  # Return error status
                response = asyncio.run(async_post_request())
                return response
            else:
                return func(self, *args, **kwargs)
        return wrapper
    return decorator