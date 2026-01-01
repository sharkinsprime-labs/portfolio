from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .set import Set

@dataclass
class Game:
    id: str
    name: str
    sets_by_code: Dict[str, Set] = field(default_factory=dict)

    def add_set(self, s: Set) -> None:
        self.sets_by_code[s.code] = s

    def get_set(self, code: str) -> Optional[Set]:
        return self.sets_by_code.get(code)

    def sets_sorted(self) -> List[Set]:
        return sorted(self.sets_by_code.values(), key=lambda s: (s.name or "").lower())
