from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Optional

class Agent(ABC):
    """Base class for all agents."""
    
    @abstractmethod
    async def invoke(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming request."""
        pass

class Action(ABC):
    """Base class for all actions."""
    
    @abstractmethod
    async def invoke_action(self, input_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the action."""
        pass

class Model(ABC):
    """Base class for all models."""
    
    @abstractmethod
    async def invoke_model(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the model."""
        pass