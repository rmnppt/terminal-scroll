import os
import random
import json
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from typing import Optional
from data import GameState


@tool
def roll_dice(reason: str, sides: int = 20) -> str:
    """
    Rolls a dice to determine the outcome of an action. Use this for skill checks,
    attack rolls, or any situation where chance is involved.
    """
    roll = random.randint(1, sides)
    return json.dumps({"roll": roll, "reason": reason, "sides": sides})


@tool
def update_game_state(
    feeling: Optional[str] = None,
    new_item_name: Optional[str] = None,
    new_item_description: Optional[str] = None,
    embarrassment: Optional[int] = None,
) -> str:
    """
    Updates the character's state. Use this to change the character's feeling,
    add a new item to their inventory, or update their embarrassment level.
    Embarrassment is an integer that should be increased, not set.
    """
    update_data = {
        "feeling": feeling,
        "new_item": (
            {"name": new_item_name, "description": new_item_description}
            if new_item_name and new_item_description
            else None
        ),
        "embarrassment": embarrassment,
    }
    # Filter out None values
    update_data = {k: v for k, v in update_data.items() if v is not None}
    return json.dumps(update_data)


@tool
def end_game(win: bool, reason: str) -> str:
    """
    Ends the game. Call this tool when the player has either won by completing the
    mission or lost by reaching an embarrassment level of 10.
    """
    return json.dumps({"win": win, "reason": reason})


class GameAgent:
    def __init__(self, state: GameState):
        self.state = state
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = [roll_dice, update_game_state, end_game]
        self.chat_history = []

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a whimsical and humorous text-based adventure game master. "
                    "Your task is to guide the player through a story, responding to their actions "
                    "with vivid descriptions, engaging challenges, and funny dialogue. "
                    "Keep the tone lighthearted, satirical, and creative. "
                    "Use the roll_dice tool for any action where the outcome is uncertain. "
                    "As the story progresses, use the update_game_state tool to modify the character's "
                    "feeling, inventory, or embarrassment level. Add embarrassment points for failed rolls or bad decisions. "
                    "The game ends in one of two ways: the player loses if their embarrassment level reaches 10, "
                    "or the player wins if they complete their mission. "
                    "When one of these conditions is met, you MUST use the end_game tool.",
                ),
                ("system", "Current Game State:\n{game_state}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, tools=self.tools, verbose=False
        )

    def generate_opening_scene(self):
        """
        Generates a mission, adds it to the state, and then generates the opening scene.
        """
        character = self.state.character
        environment = self.state.environment

        # 1. Generate the mission
        mission_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a creative writer. Your task is to generate a whimsical RPG mission objective as a JSON object. "
                    "The JSON object should have two keys: 'description' (a single sentence) and 'summary' (a concise version, max 25 characters). "
                    "The mission should fit the character and environment.",
                ),
                (
                    "user",
                    "Character: {character_name} the {character_class}\n" 
                    "Environment: {environment_name}\n"
                    "Mission:"
                ),
            ]
        )
        # Add JSON output mode to the LLM for this chain
        mission_chain = mission_prompt | self.llm.with_structured_output(
            method="json_mode"
        )
        mission_input = {
            "character_name": character.name,
            "character_class": character.class_name,
            "environment_name": environment.name,
        }
        mission_response = mission_chain.invoke(mission_input)

        mission_description = mission_response.get("description", "Survive.")
        mission_summary = mission_response.get("summary", "Survive.")

        # Update state and yield event
        self.state.mission_description = mission_description
        self.state.mission_summary = mission_summary
        yield {"type": "mission_set", "data": mission_description}

        # 2. Generate the opening scene
        scene_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a whimsical and humorous text-based adventure game master. "
                    "Your task is to generate the opening scene of an RPG based on the character, environment, and mission. "
                    "Keep the tone lighthearted, satirical, and funny. "
                    "The scene should be vivid and engaging, hinting at the character's personality and the environment's quirks. "
                    "Do not ask questions or offer choices in this initial scene. "
                    "Just describe the beginning of the adventure, making sure to complete your sentences."
                    "Write no more than 200 words or two paragraphs.",
                ),
                (
                    "user",
                    "The character is {character_name} the {character_class}. "
                    "They are currently feeling {character_feeling}. "
                    "Their backstory: {character_backstory} "
                    "Their strengths include: {character_strengths}. "
                    "Their weaknesses include: {character_weaknesses}. "
                    "They possess a unique item: {item_name} - {item_description}.",
                ),
                (
                    "user",
                    "The environment is {environment_name}. "
                    "Description: {environment_description} "
                    "Challenges hinted: {environment_challenge} "
                    "Rewards hinted: {environment_reward}. ",
                ),
                ("user", "Their mission is to: {mission}"),
                ("user", "Opening Scene:"),
            ]
        )

        scene_chain = scene_prompt | self.llm
        scene_input = {
            "character_name": character.name,
            "character_class": character.class_name,
            "character_feeling": character.feeling,
            "character_backstory": character.backstory,
            "character_strengths": ", ".join(character.strengths),
            "character_weaknesses": ", ".join(character.weaknesses),
            "item_name": character.items[0].name,
            "item_description": character.items[0].description,
            "environment_name": environment.name,
            "environment_description": environment.description,
            "environment_challenge": environment.challenge,
            "environment_reward": environment.reward,
            "mission": mission_description,
        }

        full_response = ""
        try:
            # Invoke the chain to get the full response at once
            response = scene_chain.invoke(scene_input)
            full_response = response.content

            # Yield a single event for the full text
            yield {"type": "text", "content": full_response}

            # Add the user prompts and the final AI response to the history
            formatted_prompt = scene_prompt.invoke(scene_input)
            messages = formatted_prompt.to_messages()
            user_prompts = [msg for msg in messages if isinstance(msg, HumanMessage)]
            self.chat_history.extend(user_prompts)
            self.chat_history.append(AIMessage(content=full_response))

        except Exception as e:
            yield {"type": "error", "content": f"Error generating scene: {e}"}

    def process_user_action(self, user_input: str, game_state: GameState):
        """
        Processes the user's action using the LangChain agent and yields structured events.
        """
        try:
            self.chat_history.append(HumanMessage(content=user_input))
            full_response = ""
            game_state_json = game_state.model_dump_json(indent=2)

            stream_params = {
                "input": user_input,
                "chat_history": self.chat_history,
                "game_state": game_state_json,
            }

            for event in self.agent_executor.stream(stream_params):
                match event:
                    case {"log": _}:
                        yield from self._handle_log_event(event)
                    case {"actions": _}:
                        yield from self._handle_actions_event(event)
                    case {"steps": _}:
                        yield from self._handle_steps_event(event)
                    case {"output": output}:
                        full_response += output
                        yield {"type": "text", "content": output}

            self.chat_history.append(AIMessage(content=full_response))

        except Exception as e:
            yield {"type": "error", "content": f"Error processing action: {e}"}

    def _handle_log_event(self, event):
        """Handles 'log' events from the stream, yielding 'thought' events."""
        log_data = event.get("log", {})
        if log_data.get("runnable_name") == "ChatOpenAI":
            output = log_data.get("output")
            thought = getattr(output, "content", "")
            if thought:
                yield {"type": "thought", "content": thought}

    def _handle_actions_event(self, event):
        """Handles 'actions' events, yielding events for tool calls."""
        for action in event.get("actions", []):
            if action.tool == "roll_dice":
                yield {"type": "dice_roll", "data": action.tool_input}

    def _handle_steps_event(self, event):
        """Handles 'steps' events, dispatching to tool-specific handlers."""
        for step in event.get("steps", []):
            if step.action.tool == "roll_dice":
                yield from self._handle_roll_dice_step(step)
            elif step.action.tool == "update_game_state":
                yield from self._handle_update_game_state_step(step)
            elif step.action.tool == "end_game":
                yield from self._handle_end_game_step(step)

    def _handle_roll_dice_step(self, step):
        """Handles the result of a 'roll_dice' tool call."""
        try:
            observation_data = json.loads(step.observation)
            yield {
                "type": "dice_roll_result",
                "data": {
                    "reason": observation_data.get("reason"),
                    "roll": observation_data.get("roll"),
                    "sides": observation_data.get("sides"),
                },
            }
        except json.JSONDecodeError:
            yield {
                "type": "text",
                "content": f"\n> Dice roll result: {step.observation}\n",
            }

    def _handle_update_game_state_step(self, step):
        """Handles the result of an 'update_game_state' tool call."""
        try:
            update_data = json.loads(step.observation)
            yield {"type": "game_state_update", "data": update_data}
        except json.JSONDecodeError:
            yield {
                "type": "error",
                "content": f"Invalid state update: {step.observation}",
            }

    def _handle_end_game_step(self, step):
        """Handles the result of an 'end_game' tool call."""
        try:
            end_data = json.loads(step.observation)
            yield {"type": "end_game", "data": end_data}
        except json.JSONDecodeError:
            yield {
                "type": "error",
                "content": f"Invalid end_game data: {step.observation}",
            }
