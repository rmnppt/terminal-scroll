from typing import Any

from textual.app import App

from components.messages import StateChanged
from components.screens import (
    GameScreen,
    SelectionScreen,
    WelcomeScreen,
)
from data import Character, Environment, GameState
from llm.characters import characters
from llm.environments import environments


class GameApp(App):
    CSS = """

    WelcomeScreen {
        align: center middle;
    }

    #welcome_container {
        text-align: center;
        width: 80%;
    }

    #title {
        text-style: bold;
        margin-bottom: 2;
    }

    #description {
        margin-bottom: 2;
    }

    #screen_main_area {
        layout: horizontal;
        height: 1fr;
    }

    #log_container {
        width: 1fr;
        overflow-y: auto;
    }

    #echoed_text {
        padding: 1;
        width: 100%;
    }

    #input_container {
        dock: bottom;
        layout: horizontal;
        width: 100%;
        height: 3;
        border: round white;
        background: transparent;
    }

    #prompt {
        width: auto;
        height: 100%;
        content-align: center middle;
        margin: 0 1;
    }

    #input_field {
        width: 1fr;
        border: none;
        background: transparent;
    }

    #character_status_container {
        width: 40;
        border: round white;
        layout: vertical;
        height: auto;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = GameState()

        self.characters = [Character(**c) for c in characters]
        self.environments = [Environment(**e) for e in environments]

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

    def update_state(self, key: str, value: Any):
        setattr(self.state, key, value)
        self.post_message(StateChanged())

    def handle_character_selection(self, selection: str):
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
            self.update_state("character", selected_character)

    def handle_environment_selection(self, selection: str):
        selected_environment = next(
            (env for env in self.environments if env.name == selection), None
        )
        if selected_environment:
            self.update_state("environment", selected_environment)

    def create_character_selection_screen(self):
        options = [char.name + " the " + char.class_name for char in self.characters]
        data = {char.name + " the " + char.class_name: char for char in self.characters}
        return SelectionScreen(
            title="Character Selection",
            prompt="Who are you?",
            options=options,
            next_screen_callable=self.create_environment_selection_screen,
            on_select=self.handle_character_selection,
            data=data,
        )

    def create_environment_selection_screen(self):
        options = [env.name for env in self.environments]
        data = {env.name: env for env in self.environments}
        return SelectionScreen(
            title="Environment Selection",
            prompt="Where are you going?",
            options=options,
            next_screen_callable=self.create_game_screen,
            on_select=self.handle_environment_selection,
            data=data,
            show_back_button=True,
        )

    def create_game_screen(self):
        # This is where the game actually starts
        # The GameScreen will handle generating the scene on its own.
        return GameScreen()


if __name__ == "__main__":
    app = GameApp()
    app.run()