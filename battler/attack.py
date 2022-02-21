
from dataclasses import dataclass, field
from pet import Pet
from team import Team

@dataclass
class Attack:
    """A class that represents an attack in Super Auto Pets."""

    attacker: Pet
    attacker_team: Team
    targets: list[Pet]
    damage: int 
    is_main_attack: bool = field(default=True)
