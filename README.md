# Terminal Scroll

Terminal Scroll is a procedural text-based RPG.

## Getting Started

### Prerequisites

- [uv](https://astral.sh/docs/uv)

### 1. Clone the Repository

Clone this repository to your local machine.

### 2. Install Dependencies

Install the required Python packages using `uv`:

```bash
uv sync
```

### 3. Configure Your Environment

Create a `.env` file in the root of the project and add your OpenAI API key:

```
OPENAI_API_KEY="your-api-key-here"
```

### 4. Run the Game

Launch the game using the following command:

```bash
uv run --env-file=.env python main.py
```

# Project Tech Stack & Notes

## Core Development

- **Language: Python**
  - Chosen for its simplicity, rapid prototyping capabilities, and extensive ecosystem.

- **Rendering Library: Rich**
  - Used by Textual for rendering.
  - Provides capabilities for beautiful output in the terminal, including colors, styles, tables, and support for the Unicode characters we'll use for sprites and animations (like dice rolls).

## AI & Procedural Generation

- **Orchestration Framework: LangGraph**
  - Used to build the agentic layer of the application.
  - It helps in creating and managing the flow of information between different components of the AI system.

- **LLM Provider: OpenAI**
  - The primary provider for the large language models that will generate the procedural content of the game.

## Deployment & CI/CD (TODO)

- **Hosting Platform: Fly.io**
  - A modern platform for deploying containerized applications.
  - Chosen because it can host any TCP-based service, making it perfect for our SSH-based application, unlike traditional web-focused platforms.

- **Containerization: Docker**
  - We will create a `Dockerfile` to define the application's environment.
  - This ensures our application runs in a consistent, reproducible environment from development to production. The Docker image will include Python, our code, all dependencies, and the SSH server.

- **CI/CD: GitHub Actions**
  - We will set up a workflow to automate testing and deployment.
  - When code is pushed to the main branch, GitHub Actions will automatically run tests and, if they pass, deploy the new version of the application to Fly.io using the `fly deploy` command.

