import os
from openai import OpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from data import Character, Environment


def generate_opening_scene(
    character: Character, environment: Environment, fake_llm_call: bool = False
):
    """
    Generates the opening scene of the game using OpenAI's LLM, streaming the response.
    """
    if fake_llm_call:
        yield "This is a faked opening scene for testing the dice mechanic."
        return

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
        "Just describe the beginning of the adventure, making sure to complete your sentences."
        "Write no more than 300 words or three paragraphs."
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

    # Convert to format for client.chat.completions.create
    messages = []
    for msg in formatted_prompt:
        if msg.type == "system":
            messages.append({"role": "system", "content": msg.content})
        elif msg.type == "human":
            messages.append({"role": "user", "content": msg.content})
        elif msg.type == "ai":
            messages.append({"role": "assistant", "content": msg.content})

    try:
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=400,
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception as e:
        yield f"Error generating scene: {e}"
