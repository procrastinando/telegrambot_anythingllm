# Telegram bot to sign up AnythingLLM accounts

This project provides a Telegram bot that interacts with an AnythingLLM instance to manage user accounts and provide access to a specified workspace. It's designed to be deployed using Docker and Docker Compose.

## Features

*   User registration for a PGCertHE 2025 (AnythingLLM) account via Telegram.
*   Automatic assignment of users to a predefined AnythingLLM workspace.
*   Password reset functionality.
*   User bio generation based on Telegram profile information.

## Prerequisites

*   **Docker and Docker Compose:** Ensure you have Docker and Docker Compose installed on your system.
    *   Docker: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)
    *   Docker Compose: [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)
*   **AnythingLLM Instance:** A running instance of AnythingLLM accessible from where you run this bot.
*   **Telegram Bot Token:** A token for your Telegram bot, obtained from BotFather.
*   **AnythingLLM Admin API Key:** An Admin API key from your AnythingLLM instance.

## Project Structure (in the Git Repository)

The bot's functionality relies on the following files within the [procrastinando/telegrambot_anythingllm](https://github.com/procrastinando/telegrambot_anythingllm) repository:

*   `app.py`: The main Python script for the Telegram bot.
*   `Dockerfile`: Instructions to build the Docker image for the bot.
*   `requirements.txt`: Python dependencies for the bot.

## Setup and Configuration

1.  **Clone this deployment repository (Optional):**
    If you want to manage this `docker-compose.yml` and `.env` file locally in a version-controlled way (separate from the bot's main code repository).
    ```bash
    # git clone <your-deployment-repo-url>
    # cd <your-deployment-repo-directory>
    ```
    Alternatively, you can just create the `docker-compose.yml` and `.env` files directly.

2.  **Create a `.env` file:**
    In the same directory where you will place the `docker-compose.yml` file, create a file named `.env`. This file will store your sensitive credentials and configuration. **Do NOT commit this file to Git.**

    Add the following content to your `.env` file, replacing the placeholder values with your actual information:

    ```env
    TELEGRAM_BOT_TOKEN=your_actual_telegram_bot_token
    ANYTHINGLLM_SERVER_URL=http://your_anythingllm_ip_or_hostname:3001
    ANYTHINGLLM_SERVER_EXTERNAL=https://chat.domain.com
    ANYTHINGLLM_ADMIN_API_KEY=your_actual_admin_api_key
    ANYTHINGLLM_WORKSPACE_SLUG=your_target_workspace_slug
    WELCOME_MESSAGE="Welcome to the PGCertHE 2025 Assistant! Type /start to begin."
    ```
    *   `WELCOME_MESSAGE`: (Optional) A custom welcome message. The bot script would need to be updated to use this if it's not already.

3.  **Create `docker-compose.yml`:**
    Create a file named `docker-compose.yml` in the same directory with the following content:

    ```yaml
    services:
      pgche_telegrambot:
        build:
          context: https://github.com/procrastinando/telegrambot_anythingllm.git#main 
        image: procrastinando/pgche_bot:latest # Example image name and tag
        container_name: pgche_bot_container
        environment:
          - PYTHONUNBUFFERED="1" # <--- ADD THIS LINE
          # These variables will be sourced from a .env file in the same directory
          # as this docker-compose.yml file, OR you can set them directly here.
          # The app.py script expects these to be set.
          - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
          - ANYTHINGLLM_SERVER_URL=${ANYTHINGLLM_SERVER_EXTERNAL}
          - ANYTHINGLLM_SERVER_EXTERNAL=${ANYTHINGLLM_SERVER_EXTERNAL}
          - ANYTHINGLLM_ADMIN_API_KEY=${ANYTHINGLLM_ADMIN_API_KEY}
          - ANYTHINGLLM_WORKSPACE_SLUG=${ANYTHINGLLM_WORKSPACE_SLUG}
        # env_file:
        #   - .env
        restart: unless-stopped

    # Define the named volume if you use it.
    # This ensures the volume is created by Docker if it doesn't exist.
    volumes:
      pgche_data: # Corresponds to 'pgche_data' used in the service volume mount
    ```
    **Note on `volumes`:**
    *   The original `volumes: - pgche:/app` is a bit ambiguous. If `app.py` is fetched from Git during the build, mounting a volume over `/app` might overwrite the application code unless `app.py` is also placed in the local `./pgche_data` directory on the host (which defeats the purpose of building from Git for the app code).
    *   I've changed it to `pgche_data:/app/data` as an example, assuming your bot might need to store some persistent data *inside* a subdirectory of `/app`. If your bot is stateless and doesn't write any files it needs to persist, you can remove the `volumes` section entirely from the `pgche_telegrambot` service and the top-level `volumes` definition.

## Running the Bot

1.  **Navigate to the Directory:**
    Open your terminal and change to the directory where your `docker-compose.yml` and `.env` files are located.

2.  **Build and Start:**
    The first time you run it, or if you've made changes to the bot's code in the GitHub repository (and thus need a new image), use:
    ```bash
    docker-compose up -d --build
    ```
    *   `up`: Creates and starts the container(s).
    *   `-d`: Runs in detached mode (in the background).
    *   `--build`: Forces Docker Compose to build the image using the `Dockerfile` from the specified Git repository.

3.  **Start (without rebuilding):**
    If the image is already built and you only changed environment variables in your `.env` file, or you're just restarting the bot:
    ```bash
    docker-compose up -d
    ```

4.  **View Logs:**
    To see the output and logs from your running bot:
    ```bash
    docker-compose logs -f pgche_telegrambot
    ```
    (Or use `docker logs pgche_bot_container`)

## Stopping the Bot

To stop and remove the containers defined in your `docker-compose.yml`:
```bash
docker-compose down
```

## Updating the Bot

If the bot's source code (`app.py`, `requirements.txt`, or `Dockerfile`) in the [procrastinando/telegrambot_anythingllm](https://github.com/procrastinando/telegrambot_anythingllm) repository has been updated:

1.  Pull the latest changes if you have a local clone of that repository (not strictly necessary for this Docker Compose setup, as it builds from the remote).
2.  Navigate to your `docker-compose.yml` directory.
3.  Run the following command to rebuild the image with the latest changes and restart the container:
    ```bash
    docker-compose up -d --build
    ```

## Customization

*   **Environment Variables:** Modify the `.env` file to change API keys, server URLs, workspace slugs, or other configurations. Remember to run `docker-compose up -d` after changing `.env` for the running container to pick up new values (this will recreate the container).
*   **Bot Logic:** To change the bot's behavior, commands, or interaction with AnythingLLM, you'll need to modify the `app.py` script (and potentially `requirements.txt` or `Dockerfile`) in the [procrastinando/telegrambot_anythingllm](https://github.com/procrastinando/telegrambot_anythingllm) GitHub repository. After pushing changes to the repository, run `docker-compose up -d --build` to deploy the updates.

## Troubleshooting

*   **"Environment variable not set" errors:** Ensure all required variables are defined in your `.env` file and that `app.py` is correctly reading them using `os.environ.get()`.
*   **Connection issues to AnythingLLM:** Verify `ANYTHINGLLM_SERVER_URL` is correct and that your Docker container can reach this URL (check firewalls, Docker networking).
*   **Telegram API errors:** Double-check your `TELEGRAM_BOT_TOKEN`. View bot logs for specific error messages from the Telegram API.
*   **Build failures:** Check the output of `docker-compose up --build`. Errors might be related to the `Dockerfile` syntax, inability to fetch files from GitHub, or issues installing Python dependencies.
