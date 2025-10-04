import questionary
from rich.console import Console, Group
from rich.panel import Panel

from data import Character, Environment, GameState, Item
from llm.characters import characters
from llm.environments import environments
from llm.agent import GameAgent
from llm.intro import INTRODUCTION_TEXT


import time
from rich.text import Text


class Game:
    def __init__(self):
        self.state = GameState()
        self.console = Console(width=120)
        self.characters = [Character(**c) for c in characters]
        self.environments = [Environment(**e) for e in environments]
        self.agent = None

    def run(self):
        self._setup_game()
        self._display_opening_scene()
        self._main_game_loop()

    def _setup_game(self):
        """Handles the initial game setup and character/environment selection."""
        self.console.print(
            Panel(
                "[bold green]TERMINAL SCROLL[/bold green]",
                expand=False,
                border_style="yellow",
            ),
        )
        self.console.print(INTRODUCTION_TEXT)
        questionary.press_any_key_to_continue("Press any key to begin...").ask()

        self.select_character()
        self.select_environment()

        self.agent = GameAgent(self.state)
        self.console.print("\n[bold]Generating your adventure...[/bold]\n")

    def _display_opening_scene(self):
        """Generates and displays the opening scene."""
        scene_text = Text()
        scene_generator = self.agent.generate_opening_scene()

        for event in scene_generator:
            match event.get("type"):
                case "mission_set":
                    # The agent has already updated its internal state
                    self.state.mission_description = event.get("data")
                    self.state.mission_summary = self.agent.state.mission_summary
                    self.console.print(
                        Panel(
                            f"[bold]Your Mission:[/] {self.state.mission_description}",
                            title="[bold green]New Mission[/bold green]",
                            border_style="green",
                            expand=False,
                            title_align="left",
                        )
                    )
                case "text":
                    scene_text.append(event.get("content", ""))

        # Render the final scene panel
        self.console.print(
            Panel(
                scene_text,
                border_style="yellow",
                title="Your Adventure Begins",
                title_align="left",
            )
        )

    def _main_game_loop(self):
        """Runs the main game loop where the player interacts with the game."""
        while not self.state.game_over:
            self.console.print(self.get_status_text())

            user_input = questionary.text(">", qmark="").ask()

            if user_input is None or user_input.lower() in ["quit", "exit"]:
                break

            story_text = Text()
            response_generator = self.agent.process_user_action(
                user_input, self.state
            )

            for event in response_generator:
                match event.get("type"):
                    case "game_state_update":
                        self._handle_game_state_update(event)
                    case "dice_roll_result":
                        self._handle_dice_roll_result(event)
                    case "end_game":
                        self._handle_end_game(event)
                    case "text":
                        self._handle_text(event, story_text)

            # Render the final story panel after the stream is complete
            if story_text:
                self.console.print(
                    Panel(
                        story_text,
                        border_style="yellow",
                        title="Story",
                        title_align="left",
                    )
                )

        self.console.print(
            Panel(
                "[bold green]The End[/bold green]",
                border_style="yellow",
                expand=False,
                title_align="center",
            )
        )

    def _handle_end_game(self, event):
        """Handles the end of the game."""
        self.state.game_over = True
        data = event.get("data", {})
        win = data.get("win", False)
        reason = data.get("reason", "The story has concluded.")

        title = "[bold green]You Won![/bold green]" if win else "[bold red]You Lost...[/bold red]"
        border_style = "green" if win else "red"

        self.console.print(
            Panel(
                reason,
                title=title,
                border_style=border_style,
                expand=False,
                title_align="left",
            )
        )


    def _handle_game_state_update(self, event):
        """Handles and displays game state updates."""
        update_data = event.get("data", {})
        update_messages = []
        if "feeling" in update_data:
            new_feeling = update_data["feeling"]
            if new_feeling:
                self.state.character.feeling = new_feeling
                update_messages.append(f"[bold]New Feeling:[/] {new_feeling}")
        if "new_item" in update_data:
            item_data = update_data["new_item"]
            if item_data:
                self.state.character.items.append(
                    Item(
                        name=item_data.get("name"),
                        description=item_data.get("description"),
                    )
                )
                update_messages.append(
                    f"[bold]Item Acquired:[/] {item_data.get('name')}"
                )
        if "embarrassment" in update_data:
            points = update_data["embarrassment"]
            if points:
                self.state.character.embarrassment += points
                update_messages.append(
                    f"[bold]Embarrassment +{points}![/]"
                )

        if update_messages:
            self.console.print(
                Panel(
                    "\n".join(update_messages),
                    title="[bold magenta]State Change[/bold magenta]",
                    border_style="magenta",
                    expand=False,
                    title_align="left",
                )
            )

    def _handle_dice_roll_result(self, event):
        """Displays the result of a dice roll."""
        data = event.get("data", {})
        reason = data.get("reason", "N/A")
        roll = data.get("roll", "N/A")
        sides = data.get("sides", "N/A")
        self.console.print(
            Panel(
                f"[bold]Reason:[/] {reason}\n[bold]Roll:[/] {roll} (d{sides})",
                title="[bold cyan]Dice Roll[/bold cyan]",
                border_style="cyan",
                expand=False,
                title_align="left",
            )
        )

    def _handle_text(self, event, story_text):
        """Appends text to the story."""
        story_text.append(event.get("content", ""))

    def get_status_text(self):
        char_name = (
            f"{self.state.character.name} the {self.state.character.class_name}"
            if self.state.character
            else "N/A"
        )
        env_name = self.state.environment.name if self.state.environment else "N/A"
        feeling = self.state.character.feeling if self.state.character else "N/A"
        embarrassment = self.state.character.embarrassment if self.state.character else "N/A"
        mission = self.state.mission_summary if self.state.mission_summary else "N/A"
        status_text = f"""[bold blue]Character:[/] [cyan]{char_name}[/]
[bold blue]Environment:[/] [cyan]{env_name}[/]
[bold blue]Feeling:[/] [cyan]{feeling}[/]
[bold red]Embarrassment:[/] [cyan]{embarrassment}/10[/]
[bold green]Mission:[/] [cyan]{mission}[/]"""
        return Panel(
            status_text,
            border_style="blue",
            title="You",
            title_align="left",
            expand=False,
        )

    def select_character(self):
        self.console.print()
        choices = [f"{char.name} the {char.class_name}" for char in self.characters]
        selection = questionary.select("Choose your character:", choices=choices).ask()

        if selection:
            name, _, class_name = selection.partition(" the ")
            selected_character = next(
                (
                    char
                    for char in self.characters
                    if char.name == name and char.class_name == class_name
                ),
                None,
            )
            if selected_character:
                self.state.character = selected_character

    def select_environment(self):
        self.console.print()
        choices = [env.name for env in self.environments]
        selection = questionary.select(
            "Choose your environment:", choices=choices
        ).ask()

        if selection:
            selected_environment = next(
                (env for env in self.environments if env.name == selection), None
            )
            if selected_environment:
                self.state.environment = selected_environment


if __name__ == "__main__":
    game = Game()
    game.run()
