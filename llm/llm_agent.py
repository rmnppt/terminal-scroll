import os
from openai import OpenAI
from typing import Dict, Any
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from data import Character, Environment


def generate_opening_scene(character: Character, environment: Environment) -> str:
    """
    Generates the opening scene of the game using OpenAI's LLM.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

    client = OpenAI(api_key=api_key)

    # Define prompt templates
    system_template = SystemMessagePromptTemplate.from_template(
        "You are a whimsical and humorous text-based adventure game master. "
        "Your task is to generate the opening scene of an RPG. "
        "Keep the tone lighthearted, satirical, and funny. "
        "The scene should be vivid and engaging, hinting at the character's personality "
        "and the environment's quirks. "
        "Do not ask questions or offer choices in this initial scene. "
        "Just describe the beginning of the adventure."
    )

    character_context_template = HumanMessagePromptTemplate.from_template(
        "The character is {character_name} the {character_class}. "
        "They are currently feeling {character_feeling}. "
        "Their backstory: {character_backstory} "
        "Their strengths include: {character_strengths}. "
        "Their weaknesses include: {character_weaknesses}. "
        "They possess a unique item: {item_name} - {item_description}."
    )

    environment_context_template = HumanMessagePromptTemplate.from_template(
        "The environment is {environment_name}. "
        "Description: {environment_description} "
        "Challenges hinted: {environment_challenge} "
        "Rewards hinted: {environment_reward}. "
    )

    # Combine templates into a chat prompt
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            system_template,
            character_context_template,
            environment_context_template,
            HumanMessagePromptTemplate.from_template("Opening Scene:"),
        ]
    )

    # Prepare input variables for the prompt
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

    # Format the prompt
    formatted_prompt = chat_prompt.format_messages(**input_variables)

    # Extract instructions and input for the Responses API
    system_instructions = formatted_prompt[0].content  # System message
    user_input = "\n\n".join(
        [msg.content for msg in formatted_prompt[1:]]
    )  # Combine user messages

    try:
        response = client.responses.create(
            model="gpt-4o",
            instructions=system_instructions,
            input=user_input,
            max_output_tokens=300,
            temperature=0.7,
        )
        return response.output_text
    except Exception as e:
        return f"Error generating scene: {e}"
