"""Database models for the Bio-Age Coach."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserData:
    """User data model."""
    
    user_id: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime
    metrics: Dict[str, Any]
    health_data: Dict[str, Any]
    bio_age_scores: List[Dict[str, Any]]
    settings: Dict[str, Any]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserData':
        """Create a UserData instance from a dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            UserData instance
        """
        return cls(
            user_id=data.get('user_id', ''),
            name=data.get('name', ''),
            email=data.get('email', ''),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            metrics=data.get('metrics', {}),
            health_data=data.get('health_data', {}),
            bio_age_scores=data.get('bio_age_scores', []),
            settings=data.get('settings', {})
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the UserData instance to a dictionary.
        
        Returns:
            Dictionary representation of the user data
        """
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metrics': self.metrics,
            'health_data': self.health_data,
            'bio_age_scores': self.bio_age_scores,
            'settings': self.settings
        } 