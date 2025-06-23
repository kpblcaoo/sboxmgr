from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, Any

class ErrorType(Enum):
    VALIDATION = "validation"
    FETCH = "fetch"
    PARSE = "parse"
    PLUGIN = "plugin"
    INTERNAL = "internal"

@dataclass
class PipelineError:
    type: ErrorType
    stage: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow) 