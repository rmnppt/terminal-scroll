from pydantic import BaseModel
from typing import List, Optional


class Item(BaseModel):
    name: str = ""
    description: str = ""
    property: str = ""


class Character(BaseModel):
    name: str = ""
    class_name: str = ""
    backstory: str = ""
    strengths: list[str] = [""]
    weaknesses: list[str] = [""]
    items: List[Item] = [Item()]
    feeling: str = ""
    embarrassment: int = 0


class Environment(BaseModel):
    name: str = ""
    type: str = ""
    description: str = ""
    challenge: str = ""
    reward: str = ""


class GameState(BaseModel):
    character: Character = Character()
    environment: Environment = Environment()
    mission_description: Optional[str] = None
    mission_summary: Optional[str] = None
    game_over: bool = False
