from dataclasses import dataclass, field
from typing import Optional, List
from uuid import uuid4


@dataclass
class InspectionItem:
    inspection_id: str
    name: str
    category: str
    status: str = "pending"
    observation: Optional[str] = None
    score: Optional[int] = None
    is_pass: Optional[bool] = None
    position: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def approve(self, observation: Optional[str] = None) -> None:
        self.status = "approved"
        self.is_pass = True
        if observation:
            self.observation = observation

    def reject(self, observation: str) -> None:
        self.status = "rejected"
        self.is_pass = False
        self.observation = observation

    def set_score(self, score: int) -> None:
        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100")
        self.score = score
        self.is_pass = score >= 60
        self.status = "approved" if self.is_pass else "rejected"
