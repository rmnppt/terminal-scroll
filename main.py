from textual.app import App, ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Header, Static, Input, ListView, ListItem, Button
from textual.message import Message
from textual.css.query import NoMatches
from pydantic import BaseModel
from typing import Literal, Any, Dict, List
from rich.text import Text


CharacterClass = Literal["Valiant", "Mystic", "Shadow"]
EnvironmentType = Literal["Forest", "Cave", "Castle"]


class Item(BaseModel):
    name: str
    description: str
    property: str


class Character(BaseModel):
    name: str
    class_name: CharacterClass
    backstory: str
    strengths: list[str]
    weaknesses: list[str]
    items: List[Item]
    feeling: str


class Environment(BaseModel):
    name: str
    type: EnvironmentType


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
            with Container(id="character_status_container"):
                yield Static(id="character_status")

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
        details_data: Dict[str, Dict[str, Any]],
        details_key_map: Dict[str, str],
        show_back_button: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._title = title
        self._prompt = prompt
        self._options = options
        self._next_screen_callable = next_screen_callable
        self.on_select = on_select
        self.details_data = details_data
        self.details_key_map = details_key_map
        self.show_back_button = show_back_button

    def get_title(self) -> str:
        return self._title

    def compose_main(self) -> ComposeResult:
        with Container(id="selection_container"):
            with Container(id="options_container"):
                yield Static(self._prompt, id="selection_prompt")
                yield ListView()
                if self.show_back_button:
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
        details = self.details_data.get(item_name)
        panel = self.query_one("#details_panel")
        panel.remove_children()
        if details:
            widgets = []
            for key, label in self.details_key_map.items():
                value = details[key]
                widgets.append(Static(f"{label}:", classes="detail-label"))
                if isinstance(value, list):
                    for v in value:
                        widgets.append(Static(f"- {v}", classes="detail-value-list"))
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
            self.on_select(event.item.item_name)
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

    #character_status_container {
        dock: right;
        width: 40;
        border: round white;
        layout: vertical;
        height: auto;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from llm.backstories import backstories
        from llm.environments import environments
        from llm.items import items

        self.state = GameState()

        character_definitions = [
            {"name": "Kaelen", "class_name": "Valiant", "feeling": "heroic"},
            {"name": "Elara", "class_name": "Mystic", "feeling": "peckish"},
            {"name": "Silas", "class_name": "Shadow", "feeling": "conspicuous"},
        ]

        self.characters = []
        for char_def in character_definitions:
            full_name = f"{char_def['name']} the {char_def['class_name']}"
            backstory_details = backstories[full_name]
            item_details = items[full_name]
            self.characters.append(
                Character(
                    name=char_def["name"],
                    class_name=char_def["class_name"],
                    backstory=backstory_details["backstory"],
                    strengths=backstory_details["strengths"],
                    weaknesses=backstory_details["weaknesses"],
                    items=[
                        Item(
                            name=item_details["name"],
                            description=item_details["description"],
                            property=item_details["property"],
                        )
                    ],
                    feeling=char_def["feeling"],
                )
            )

        self.environments_data = environments
        self.environments = [
            Environment(name="The Forest of Unlikely Encounters", type="Forest"),
            Environment(name="The Cave of Convenient Plot-Holes", type="Cave"),
            Environment(name="The Castle of Mild Discomfort", type="Castle"),
        ]

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
        details_data = {}
        for char in self.characters:
            full_name = f"{char.name} the {char.class_name}"
            details_data[full_name] = {
                "backstory": char.backstory,
                "strengths": char.strengths,
                "weaknesses": char.weaknesses,
                "starter_item": f"{char.items[0].name}: {char.items[0].description}",
            }

        return SelectionScreen(
            title="Character Selection",
            prompt="Who are you?",
            options=[
                f"{char.name} the {char.class_name}" for char in self.characters
            ],
            next_screen_callable=self.create_environment_selection_screen,
            on_select=self.handle_character_selection,
            details_data=details_data,
            details_key_map={
                "backstory": "Backstory",
                "strengths": "Strengths",
                "weaknesses": "Weaknesses",
                "starter_item": "Starter Item",
            },
        )

    def create_environment_selection_screen(self):
        return SelectionScreen(
            title="Environment Selection",
            prompt="Where are you going?",
            options=[env.name for env in self.environments],
            next_screen_callable=self.create_game_screen,
            on_select=self.handle_environment_selection,
            details_data=self.environments_data,
            details_key_map={
                "description": "Description",
                "challenge": "Challenge",
                "reward": "Reward",
            },
            show_back_button=True,
        )

    def create_game_screen(self):
        return GameScreen()


if __name__ == "__main__":
    app = GameApp()
    app.run()
