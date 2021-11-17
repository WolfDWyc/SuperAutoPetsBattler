
from dataclasses import dataclass, field
from pet import Pet

@dataclass
class Attack:
    """A class that represents an attack in Super Auto Pets."""

    attacker: Pet
    targets: list[Pet]
    damage: int 
    trigger_own_events: bool = field(default=True)
