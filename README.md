# telegrambot_anythingllm
Use telegrambot to create accounts in anythingllm

```
services:
  pgche_telegrambot:
    # --- Building directly from Git ---
    build:
      context: https://github.com/procrastinando/telegrambot_anythingllm.git#main
      # dockerfile: Dockerfile  # Optional: specify if your Dockerfile has a different name or path within the repo
    
    image: pgche_bot_image # Optional: You can tag the image built by compose
    container_name: pgche_bot_container
    
    environment:
      # These variables will be sourced from the .env file in the same directory
      # as this docker-compose.yml file, OR you can set them directly here (less secure for secrets).
      # The app.py script expects these to be set.
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - ANYTHINGLLM_SERVER_URL=${ANYTHINGLLM_SERVER_URL}
      - ANYTHINGLLM_ADMIN_API_KEY=${ANYTHINGLLM_ADMIN_API_KEY}
      - ANYTHINGLLM_WORKSPACE_SLUG=${ANYTHINGLLM_WORKSPACE_SLUG}
    
    # To explicitly use an .env file (docker-compose usually picks it up automatically
    # if it's in the same directory as the docker-compose.yml file):
    # env_file:
    #  - .env
      
    restart: unless-stopped
    
    # Optional: If you want to ensure the build happens every time you run `docker-compose up`
    # and not use a cached build if the remote repo hasn't changed significantly in Docker's view.
    # pull_policy: build

    # --- Networking (Example) ---
    # If your AnythingLLM instance is also a Docker container on the same host,
    # you might want them on the same network.
    # networks:
    #   - bot_network

# Optional: Define a network if needed
# networks:
#   bot_network:
#     driver: bridge
```