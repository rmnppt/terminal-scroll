import questionary
from rich.console import Console
from rich.panel import Panel

from data import Character, Environment, GameState
from llm.characters import characters
from llm.environments import environments
from llm.agent import GameAgent
from llm.intro import INTRODUCTION_TEXT


from rich.live import Live
from rich.text import Text


class Game:
    def __init__(self):
        self.state = GameState()
        self.console = Console(width=120)
        self.characters = [Character(**c) for c in characters]
        self.environments = [Environment(**e) for e in environments]
        self.agent = None

    def run(self):
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

        # Generate and print the opening scene
        scene_text = Text()
        with Live(
            Panel(
                scene_text,
                border_style="yellow",
                title="Your Adventure Begins",
                title_align="left",
            ),
            console=self.console,
            refresh_per_second=12,
        ) as live:
            scene_generator = self.agent.generate_opening_scene()
            for chunk in scene_generator:
                scene_text.append(chunk)

        # Main game loop
        while True:
            self.console.print(self.get_status_text())
            user_input = questionary.text(">", qmark="").ask()

            if user_input is None or user_input.lower() in ["quit", "exit"]:
                break

            response_text = Text()
            with Live(
                Panel(
                    response_text,
                    border_style="yellow",
                    title="Story",
                    title_align="left",
                ),
                console=self.console,
                refresh_per_second=12,
            ) as live:
                response_generator = self.agent.process_user_action(user_input)
                for chunk in response_generator:
                    response_text.append(chunk)

    def get_status_text(self):
        char_name = (
            f"{self.state.character.name} the {self.state.character.class_name}"
            if self.state.character
            else "N/A"
        )
        env_name = self.state.environment.name if self.state.environment else "N/A"
        feeling = self.state.character.feeling if self.state.character else "N/A"
        status_text = f"[bold green]Character:[/] [cyan]{char_name}[/] | [bold green]Environment:[/] [cyan]{env_name}[/] | [bold green]Feeling:[/] [cyan]{feeling}[/]"
        return Panel(
            status_text,
            border_style="yellow",
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
