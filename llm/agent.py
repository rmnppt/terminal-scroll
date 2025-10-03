import os
import random
import json
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from data import GameState


@tool
def roll_dice(reason: str, sides: int = 20) -> str:
    """
    Rolls a dice to determine the outcome of an action. Use this for skill checks,
    attack rolls, or any situation where chance is involved.
    """
    roll = random.randint(1, sides)
    return json.dumps({"roll": roll, "reason": reason, "sides": sides})


class GameAgent:
    def __init__(self, state: GameState):
        self.state = state
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = [roll_dice]
        self.chat_history = []

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a whimsical and humorous text-based adventure game master. "
                    "Your task is to guide the player through a story, responding to their actions "
                    "with vivid descriptions, engaging challenges, and funny dialogue. "
                    "Keep the tone lighthearted, satirical, and creative. "
                    "Use the roll_dice tool for any action where the outcome is uncertain.",
                ),
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
        Generates the opening scene and adds it to the chat history.
        """
        character = self.state.character
        environment = self.state.environment

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a whimsical and humorous text-based adventure game master. "
                    "Your task is to generate the opening scene of an RPG. "
                    "Keep the tone lighthearted, satirical, and funny. "
                    "The scene should be vivid and engaging, hinting at the character's personality "
                    "and the environment's quirks. "
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
                ("user", "Opening Scene:"),
            ]
        )

        chain = prompt | self.llm

        input_variables = {
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
        }

        full_response = ""
        try:
            for chunk in chain.stream(input_variables):
                content = chunk.content
                full_response += content
                yield content

            # Add the user prompts and the final AI response to the history
            formatted_prompt = prompt.invoke(input_variables)
            messages = formatted_prompt.to_messages()
            user_prompts = [msg for msg in messages if isinstance(msg, HumanMessage)]
            self.chat_history.extend(user_prompts)
            self.chat_history.append(AIMessage(content=full_response))

        except Exception as e:
            yield f"Error generating scene: {e}"

    def process_user_action(self, user_input: str):
        """
        Processes the user's action using the LangChain agent and yields the response.
        """
        try:
            response = self.agent_executor.invoke(
                {"input": user_input, "chat_history": self.chat_history}
            )
            output = response.get("output", "No output from agent.")
            self.chat_history.extend(
                [
                    HumanMessage(content=user_input),
                    AIMessage(content=output),
                ]
            )
            yield output
        except Exception as e:
            yield f"Error processing action: {e}"
