# Project Tech Stack & Notes

This document summarizes the technology choices for the procedural text-based RPG.

## Core Development

*   **Language: Python**
    *   Chosen for its simplicity, rapid prototyping capabilities, and extensive ecosystem.

*   **TUI Framework: Textual**
    *   A powerful framework for building interactive and modern terminal applications.
    *   It's built on top of Rich and provides a full application model with widgets, layouts, and an animation system.
    *   We'll use it to manage the entire UI, from character display to input handling.

*   **Rendering Library: Rich**
    *   Used by Textual for rendering.
    *   Provides capabilities for beautiful output in the terminal, including colors, styles, tables, and support for the Unicode characters we'll use for sprites and animations (like dice rolls).

## Deployment & CI/CD

*   **Hosting Platform: Fly.io**
    *   A modern platform for deploying containerized applications.
    *   Chosen because it can host any TCP-based service, making it perfect for our SSH-based application, unlike traditional web-focused platforms.

*   **Containerization: Docker**
    *   We will create a `Dockerfile` to define the application's environment.
    *   This ensures our application runs in a consistent, reproducible environment from development to production. The Docker image will include Python, our code, all dependencies, and the SSH server.

*   **CI/CD: GitHub Actions**
    *   We will set up a workflow to automate testing and deployment.
    *   When code is pushed to the main branch, GitHub Actions will automatically run tests and, if they pass, deploy the new version of the application to Fly.io using the `fly deploy` command.
