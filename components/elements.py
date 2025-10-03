import random

from rich.text import Text
from textual.widgets import ListItem, Static


class DetailListItem(ListItem):
    def __init__(self, item_name: str):
        super().__init__(Static(item_name))
        self.item_name = item_name


def roll_d6() -> int:
    """Rolls a 6-sided die."""
    return random.randint(1, 6)


def get_dice_face(roll: int) -> Text:
    """Returns a rich Text object for a dice face."""
    faces = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅",
    }
    face = faces.get(roll, "🎲")
    return Text(f"\nYou rolled a {roll}: {face}\n", justify="center")
