from pydantic import BaseModel
from typing import List


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


class Environment(BaseModel):
    name: str = ""
    type: str = ""
    description: str = ""
    challenge: str = ""
    reward: str = ""


class GameState(BaseModel):
    character: Character = Character()
    environment: Environment = Environment()
