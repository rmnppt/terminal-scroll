from typing import Any, Dict, Union
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header, Static, Input, ListView, ListItem, Button
from textual.message import Message
from textual.css.query import NoMatches
from rich.text import Text
from data import Character, Environment, GameState
from llm.llm_agent import generate_opening_scene


class StateChanged(Message):
    pass


class BaseScreen(Screen):
    app: "GameApp"

    def compose(self) -> ComposeResult:
        yield Header(name=self.get_title())
        with Container(id="screen_main_area"):
            yield from self.compose_main()
            with Container(id="character_status_container"):
                yield Static(id="character_status")

    def get_title(self) -> str:
        return ""

    def compose_main(self) -> ComposeResult:
        raise NotImplementedError

    def on_mount(self) -> None:
        self.update_state_display()

    def on_state_changed(self, event: StateChanged) -> None:
        self.update_state_display()

    def update_state_display(self) -> None:
        try:
            character_status_container = self.query_one("#character_status_container")
            character_status_widget = self.query_one("#character_status", Static)
            state = self.app.state

            if state.character is None and state.environment is None:
                character_status_container.styles.visibility = "hidden"
            else:
                character_status_container.styles.visibility = "visible"

                secondary_color = self.app.get_css_variables()["secondary"]
                accent_color = self.app.get_css_variables()["accent"]

                parts = []
                if state.character:
                    parts.append("You are ")
                    parts.append(
                        (
                            f"{state.character.name} the {state.character.class_name}",
                            f"bold {secondary_color}",
                        )
                    )
                    parts.append(" (feeling ")
                    parts.append((state.character.feeling, "italic"))
                    parts.append(")")
                if state.environment:
                    if parts:
                        parts.append(" in the ")
                    else:
                        parts.append("In the ")
                    parts.append((state.environment.name, f"bold {accent_color}"))

                if parts:
                    parts.append(".")

                text = Text.assemble(*parts)
                character_status_widget.update(text)

        except NoMatches:
            pass


class DetailListItem(ListItem):
    def __init__(self, item_name: str):
        super().__init__(Static(item_name))
        self.item_name = item_name


class SelectionScreen(BaseScreen):
    CSS = """
    #selection_container {
        layout: horizontal;
        padding: 1;
        height: 1fr;
    }
    #options_container {
        width: 30;
    }
    #details_panel {
        width: 1fr;
        padding: 0 1;
        border: round white;
    }
    #back_button {
        width: 100%;
        margin-top: 1;
    }
    .detail-label {
        text-style: bold;
        color: $primary;
    }
    .detail-value {
        margin-bottom: 1;
    }
    .detail-value-list {
        margin-left: 2;
    }
    """

    def __init__(
        self,
        title: str,
        prompt: str,
        options: list[str],
        next_screen_callable,
        on_select,
        data: Dict[str, Environment | Character],
        show_back_button: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._title = title
        self._prompt = prompt
        self._options = options
        self._next_screen_callable = next_screen_callable
        self._on_select = on_select
        self._details_data = data
        self._show_back_button = show_back_button

    def get_title(self) -> str:
        return self._title

    def compose_main(self) -> ComposeResult:
        with Container(id="selection_container"):
            with Container(id="options_container"):
                yield Static(self._prompt, id="selection_prompt")
                yield ListView()
                if self._show_back_button:
                    yield Button("Back", id="back_button")
            yield Container(id="details_panel")

    def on_mount(self) -> None:
        super().on_mount()
        if self._options:
            lv = self.query_one(ListView)
            for option in self._options:
                lv.append(DetailListItem(option))
            self.update_details(self._options[0])
            lv.focus()

    def update_details(self, item_name: str):
        details = self._details_data.get(item_name)
        panel = self.query_one("#details_panel")
        panel.remove_children()
        if details:
            widgets = []
            for field_name, _ in details.model_fields.items():
                value = getattr(details, field_name, None)
                # Skip 'items' field for now, or handle it separately if needed
                # if field_name == "items":
                #     continue
                widgets.append(
                    Static(
                        f"[b]{field_name.replace('_', ' ').title()}:[/b]",
                        classes="detail-label",
                    )
                )
                if isinstance(value, list):
                    if isinstance(value[0], str):
                        for v in value:
                            widgets.append(
                                Static(f"- {v}", classes="detail-value-list")
                            )
                    # if isinstance(value[0], Item):
                    #     item = value[0]

                else:
                    widgets.append(Static(str(value), classes="detail-value"))
            panel.mount_all(widgets)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back_button":
            self.dismiss()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item:
            self.update_details(event.item.item_name)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item:
            self._on_select(event.item.item_name)
            if self._next_screen_callable:
                self.app.push_screen(self._next_screen_callable())


class WelcomeScreen(Screen):
    def compose(self) -> ComposeResult:
        with Container(id="welcome_container"):
            yield Static("Terminal Scroll", id="title")
            yield Static(
                "Welcome to Terminal Scroll, a text-based RPG where the only thing more "
                "unpredictable than the story is your character's questionable life choices. "
                "Prepare for a journey of mild peril, moderate inconvenience, and a whole "
                "lot of absurdity. Your adventure is about to be written, one ridiculous "
                "command at a time.",
                id="description",
            )
            yield Button("Let's Begin", id="begin_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "begin_button":
            self.app.push_screen(self.app.create_character_selection_screen())


class GameScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.full_text = ""

    def get_title(self) -> str:
        return "textRPG"

    def compose(self) -> ComposeResult:
        yield Header(name=self.get_title())
        with Container(id="screen_main_area"):
            with Container(id="log_container"):
                yield Static(id="echoed_text")
            with Container(id="character_status_container"):
                yield Static(id="character_status")
        with Container(id="input_container"):
            yield Static(">", id="prompt")
            yield Input(placeholder="What next...", id="input_field")

    def on_mount(self) -> None:
        super().on_mount()
        self.run_worker(self.get_opening_scene, thread=True)

    def get_opening_scene(self) -> None:
        selected_character = self.app.state.character
        selected_environment = self.app.state.environment

        if selected_character and selected_environment:
            for chunk in generate_opening_scene(
                selected_character, selected_environment
            ):
                self.app.call_from_thread(self.append_text, chunk)
        else:
            error_message = "Error: Character or environment not selected."
            self.app.call_from_thread(self.append_text, error_message)

    def append_text(self, text_chunk: str) -> None:
        self.full_text += text_chunk
        text_widget = self.query_one("#echoed_text", Static)
        text_widget.update(self.full_text)
        scrollable_container = self.query_one("#log_container")
        scrollable_container.scroll_end(animate=False)

    def on_input_changed(self, event: Input.Changed) -> None:
        pass


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
        from llm.characters import characters
        from llm.environments import environments

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
