from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container
from textual.screen import Screen
from textual.widgets import Header, Footer, RadioButton, RadioSet, Static, Input
from textual.events import Key
from textual.message import Message
from textual.css.query import NoMatches
from pydantic import BaseModel
from typing import Literal

Character = Literal["Warrior", "Mage", "Rogue"]
Environment = Literal["Forest", "Cave", "Castle"]


class GameState(BaseModel):
    character: Character | None = None
    environment: Environment | None = None


class StateChanged(Message):
    pass


class BaseScreen(Screen):
    app: "GameApp"

    def compose(self) -> ComposeResult:
        yield Header(name=self.get_title())
        with Container(id="screen_main_area"):
            yield from self.compose_main()
            yield Container(id="state_display_container")

    def get_title(self) -> str:
        return ""

    def compose_main(self) -> ComposeResult:
        pass

    def on_mount(self) -> None:
        self.update_state_display()

    def on_state_changed(self, event: StateChanged) -> None:
        self.update_state_display()

    def update_state_display(self) -> None:
        try:
            state_display_container = self.query_one(
                "#state_display_container", Container
            )
            state = self.app.state

            # Clear existing children
            state_display_container.remove_children()

            if state.character is None and state.environment is None:
                state_display_container.styles.visibility = "hidden"
            else:
                state_display_container.styles.visibility = "visible"
                display_text = ""
                if state.character:
                    display_text += f"You are a {state.character}"
                if state.environment:
                    if display_text:  # If character is already set
                        display_text += f" in the {state.environment}"
                    else:
                        display_text += (
                            f"In the {state.environment}"  # If only environment is set
                        )

                if display_text:  # Add full stop only if there is text
                    display_text += "."

                state_display_container.mount(Static(display_text, id="state_summary"))

        except NoMatches:
            pass


class SelectionScreen(BaseScreen):
    CSS = """
    
    #selection_container {
        padding: 1;
        width: 30;
    }
    
    """

    def __init__(
        self,
        title: str,
        prompt: str,
        options: list[str],
        next_screen_callable,
        on_select,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._title = title
        self._prompt = prompt
        self._options = options
        self._next_screen_callable = next_screen_callable
        self.on_select = on_select

    def get_title(self) -> str:
        return self._title

    def compose_main(self) -> ComposeResult:
        with Container(id="selection_container"):
            yield Static(self._prompt, id="selection_prompt")
            with RadioSet():
                for option in self._options:
                    yield RadioButton(option)

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.on_select(event.pressed.label.plain)
        if self._next_screen_callable:
            self.app.push_screen(self._next_screen_callable())


class GameScreen(BaseScreen):
    def get_title(self) -> str:
        return "textRPG"

    def compose_main(self) -> ComposeResult:
        yield Static(id="echoed_text")
        with Container(id="input_container"):
            yield Static(">", id="prompt")
            yield Input(placeholder="What next...", id="input_field")

    def on_input_changed(self, event: Input.Changed) -> None:
        self.query_one("#echoed_text", Static).update(f"You wrote: {event.value}")


class GameApp(App):
    CSS = """
    #screen_main_area {
        layout: horizontal;
        height: 1fr;
    }

    #echoed_text {
        width: 1fr;
        height: 100%;
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

    #state_display_container {
        dock: right;
        width: 30;
        border: round white;
        layout: vertical;
        height: auto;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = GameState()

    def on_mount(self) -> None:
        self.push_screen(self.create_character_selection_screen())

    def update_state(self, key: str, value: str):
        setattr(self.state, key, value)
        self.post_message(StateChanged())

    def create_character_selection_screen(self):
        return SelectionScreen(
            title="Character Selection",
            prompt="Who are you?",
            options=["Warrior", "Mage", "Rogue"],
            next_screen_callable=self.create_environment_selection_screen,
            on_select=lambda selection: self.update_state("character", selection),
        )

    def create_environment_selection_screen(self):
        return SelectionScreen(
            title="Environment Selection",
            prompt="Where are you going?",
            options=["Forest", "Cave", "Castle"],
            next_screen_callable=self.create_game_screen,
            on_select=lambda selection: self.update_state("environment", selection),
        )

    def create_game_screen(self):
        return GameScreen()


if __name__ == "__main__":
    app = GameApp()
    app.run()

