# --- Ensure 'requests' library is installed ---
try:
    import requests
except (ImportError, ModuleNotFoundError): # ModuleNotFoundError is Python 3.6+
    print("Module 'requests' not found. Trying to install it...")
    import subprocess
    import sys
    try:
        # Use sys.executable to ensure pip is called for the correct Python environment
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        # Try to import it again after installation
        import requests
        print("'requests' installed successfully.")
    except subprocess.CalledProcessError as e_pip:
        print(f"Error: Failed to install 'requests' using pip. {e_pip}")
        print("Please install 'requests' manually (e.g., 'pip install requests') and re-run the script.")
        sys.exit(1) # Exit if installation fails
    except ImportError as e_import_after_install:
        # This might happen if pip install succeeds but the module is still not found in path
        print(f"Error: Could not import 'requests' even after attempting installation. {e_import_after_install}")
        print("Please check your Python environment or install 'requests' manually.")
        sys.exit(1) # Exit if import still fails

# --- Standard Library Imports ---
import sys
import json
import time
import random
import string
import os # For environment variables (was implicitly used, now explicitly imported)

# --- Configuration from Environment Variables ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANYTHINGLLM_SERVER_URL = os.environ.get("ANYTHINGLLM_SERVER_URL")
ANYTHINGLLM_SERVER_EXTERNAL = os.environ.get("ANYTHINGLLM_SERVER_EXTERNAL")
ANYTHINGLLM_ADMIN_API_KEY = os.environ.get("ANYTHINGLLM_ADMIN_API_KEY")
ANYTHINGLLM_WORKSPACE_SLUG = os.environ.get("ANYTHINGLLM_WORKSPACE_SLUG")
WELCOME_MESSAGE = os.environ.get("WELCOME_MESSAGE")

# --- Validate Essential Configuration ---
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")
if not ANYTHINGLLM_SERVER_URL:
    raise ValueError("ANYTHINGLLM_SERVER_URL environment variable not set.")
if not ANYTHINGLLM_SERVER_EXTERNAL:
    raise ValueError("ANYTHINGLLM_SERVER_EXTERNAL environment variable not set.")
if not ANYTHINGLLM_ADMIN_API_KEY:
    raise ValueError("ANYTHINGLLM_ADMIN_API_KEY environment variable not set.")
if not ANYTHINGLLM_WORKSPACE_SLUG:
    raise ValueError("ANYTHINGLLM_WORKSPACE_SLUG environment variable not set.")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

known_users_anythingllm_ids = {} # Local cache for PGCertHE user IDs

# --- Helper Functions ---

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    # It's important to escape backslashes themselves first, if they are part of the text.
    # However, the problem is usually about escaping the markdown special characters.
    # Let's refine this to ensure order doesn't create issues.
    # For simplicity, we'll assume text doesn't contain '\' unless it's part of an already escaped sequence we want to preserve (which is rare).
    # Or, if we must escape '\', it should be done first: text = text.replace('\\', '\\\\')
    temp_text = str(text) # Ensure it's a string
    for char in escape_chars:
        if char in temp_text:
            temp_text = temp_text.replace(char, '\\' + char)
    return temp_text

def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    print(f"Generated password (before any Markdown escaping): {password}")
    return password

def get_anythingllm_headers():
    return {
        "Authorization": f"Bearer {ANYTHINGLLM_ADMIN_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def send_telegram_message(chat_id, text, parse_mode=None):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if parse_mode == "MarkdownV2":
        print(f"Sending to Telegram with MarkdownV2: >>>{text}<<<")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Sent message to {chat_id}: {str(text)[:70]}...")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message to {chat_id}: {e}")
        if e.response is not None:
            print(f"Telegram API Error ({e.response.status_code}): {e.response.text}")
        return None

def get_anythingllm_user_by_telegram_id(telegram_id_str):
    """Checks if a user with the given Telegram ID (as username) exists in PGCertHE."""
    url = f"{ANYTHINGLLM_SERVER_URL}/api/v1/admin/users"
    print(f"Checking PGCertHE for user with username (Telegram ID): {telegram_id_str}")
    try:
        response = requests.get(url, headers=get_anythingllm_headers())
        response.raise_for_status()
        data = response.json()
        if data.get("users"):
            for user in data["users"]:
                if user.get("username") == telegram_id_str:
                    print(f"Found existing PGCertHE user '{telegram_id_str}' with PGCertHE ID {user['id']}")
                    return user["id"]
        print(f"PGCertHE user with username '{telegram_id_str}' not found in PGCertHE.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching PGCertHE users: {e}")
        if e.response is not None:
            print(f"PGCertHE API Error while fetching users: {e.response.text}")
        return None

def create_anythingllm_user(telegram_id, telegram_first_name, telegram_language_code):
    """Creates a new PGCertHE user and sets their bio."""
    username = str(telegram_id)
    password = generate_random_password()
    
    bio_text = (
        f"{telegram_first_name} that speaks {telegram_language_code} is a distinguished educator "
        f"currently enrolled in the Postgraduate Certificate program in Higher Education"
    )

    url = f"{ANYTHINGLLM_SERVER_URL}/api/v1/admin/users/new"
    payload = {
        "username": username,
        "password": password,
        "role": "default",
        "bio": bio_text
    }
    print(f"Attempting to create PGCertHE user: {username} with bio.")
    try:
        response = requests.post(url, headers=get_anythingllm_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("user") and data["user"].get("id"):
            print(f"Successfully created PGCertHE user '{username}' with PGCertHE ID {data['user']['id']} and bio.")
            return data["user"]["id"], password
        else:
            print(f"Error in PGCertHE user creation response (missing user/id): {data}")
            return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error creating PGCertHE user '{username}' with bio: {e}")
        if e.response is not None:
            print(f"PGCertHE API Error during user creation: {e.response.text}")
        return None, None

def add_user_to_anythingllm_workspace(pgcerthe_user_id, workspace_slug):
    if not pgcerthe_user_id: return False
    url = f"{ANYTHINGLLM_SERVER_URL}/api/v1/admin/workspaces/{workspace_slug}/manage-users"
    payload = {"userIds": [pgcerthe_user_id], "reset": False}
    print(f"Attempting to add/ensure PGCertHE user ID {pgcerthe_user_id} is in workspace '{workspace_slug}'")
    try:
        response = requests.post(url, headers=get_anythingllm_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            print(f"Successfully ensured PGCertHE user ID {pgcerthe_user_id} is in workspace '{workspace_slug}'")
            return True
        else:
            print(f"Failed to add PGCertHE user to workspace or confirm membership, response: {data}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error adding PGCertHE user ID {pgcerthe_user_id} to workspace '{workspace_slug}': {e}")
        if e.response is not None:
            print(f"PGCertHE API Error during workspace management: {e.response.text}")
        return False

def reset_anythingllm_password(pgcerthe_user_id):
    if not pgcerthe_user_id: return None
    new_password = generate_random_password()
    url = f"{ANYTHINGLLM_SERVER_URL}/api/v1/admin/users/{pgcerthe_user_id}"
    payload = {"password": new_password}
    print(f"Attempting to reset password for PGCertHE user ID: {pgcerthe_user_id}")
    try:
        response = requests.post(url, headers=get_anythingllm_headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            print(f"Successfully reset password for PGCertHE user ID {pgcerthe_user_id}")
            return new_password
        else:
            print(f"Password reset failed for PGCertHE user ID {pgcerthe_user_id}, response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error resetting password for PGCertHE user ID {pgcerthe_user_id}: {e}")
        if e.response is not None:
            print(f"PGCertHE API Error during password reset: {e.response.text}")
        return None

def handle_update(update):
    if "message" not in update: return

    message = update["message"]
    chat_id = message["chat"]["id"]
    telegram_id_str = str(chat_id)
    
    telegram_user_obj = message.get("from", {})
    first_name = telegram_user_obj.get("first_name", "User")
    language_code = telegram_user_obj.get("language_code", "en")

    text = message.get("text", "")

    print(f"\nReceived message from {chat_id} ({first_name}, lang: {language_code}): {text}")

    # Always check PGCertHE for user status on key commands
    current_pgcerthe_user_id = None
    if text in ["/start", "/reset_password"]:
        current_pgcerthe_user_id = get_anythingllm_user_by_telegram_id(telegram_id_str)
        if current_pgcerthe_user_id:
            known_users_anythingllm_ids[chat_id] = current_pgcerthe_user_id
        else:
            # If user not found in PGCertHE, remove from local cache if present
            known_users_anythingllm_ids.pop(chat_id, None)
    else:
        # For other commands, we can rely on the cache first, but this example focuses on /start & /reset
        current_pgcerthe_user_id = known_users_anythingllm_ids.get(chat_id)


    if text == "/start":
        if current_pgcerthe_user_id:
            send_telegram_message(chat_id, "It looks like you already have a PGCertHE 2025 account!")
            add_user_to_anythingllm_workspace(current_pgcerthe_user_id, ANYTHINGLLM_WORKSPACE_SLUG)
            workspace_link = f"{ANYTHINGLLM_SERVER_EXTERNAL}"
            
            parts = [
                escape_markdown_v2(f"Your PGCertHE 2025 username is: {telegram_id_str}"),
                "\n",
                escape_markdown_v2(f"You can log in and access the '{ANYTHINGLLM_WORKSPACE_SLUG}' workspace at: ") + \
                escape_markdown_v2(workspace_link),
                "\n",
                escape_markdown_v2("If you forgot your password, use /reset_password.")
            ]
            response_text = "".join(parts)
            send_telegram_message(chat_id, response_text, parse_mode="MarkdownV2")
        else:
            send_telegram_message(chat_id, "Welcome! Creating your PGCertHE 2025 account...")
            send_telegram_message(chat_id, str(WELCOME_MESSAGE))
            new_llm_id, password = create_anythingllm_user(chat_id, first_name, language_code)

            if new_llm_id and password:
                known_users_anythingllm_ids[chat_id] = new_llm_id # Update cache
                current_pgcerthe_user_id = new_llm_id # For consistency if needed later in this block
                added_to_workspace = add_user_to_anythingllm_workspace(current_pgcerthe_user_id, ANYTHINGLLM_WORKSPACE_SLUG)
                workspace_link = f"{ANYTHINGLLM_SERVER_EXTERNAL}"
                
                escaped_password = escape_markdown_v2(password)

                parts = [
                    escape_markdown_v2("Your PGCertHE 2025 account has been created!"),
                    "\n\n",
                    escape_markdown_v2(f"Username: {telegram_id_str}"),
                    "\n",
                    f"Password: `{escaped_password}`", # Password in backticks for MarkdownV2
                    "\n\n",
                    escape_markdown_v2(f"You can log in and access the '{ANYTHINGLLM_WORKSPACE_SLUG}' workspace at: ") + \
                    escape_markdown_v2(workspace_link)
                ]

                if not added_to_workspace:
                    parts.append(escape_markdown_v2("\n\nWarning: There was an issue adding you to the workspace. Please contact an admin."))
                
                response_text = "".join(parts)
                send_telegram_message(chat_id, response_text, parse_mode="MarkdownV2")
            else:
                send_telegram_message(chat_id, "Sorry, there was an error creating your PGCertHE 2025 account. Please try again later or contact an admin.")

    elif text == "/reset_password":
        if not current_pgcerthe_user_id: # This check now uses the freshly fetched ID
            send_telegram_message(chat_id, "It seems you don't have a PGCertHE 2025 account yet. Use /start to create one.")
            return
        
        send_telegram_message(chat_id, "Resetting your PGCertHE 2025 password...")
        new_password = reset_anythingllm_password(current_pgcerthe_user_id)
        if new_password:
            escaped_new_password = escape_markdown_v2(new_password)
            
            parts = [
                escape_markdown_v2("Your PGCertHE 2025 password has been reset."),
                "\n",
                escape_markdown_v2("New Password: "), # Added space for readability
                f"`{escaped_new_password}`" # Password in backticks
            ]
            response_text = "".join(parts)
            send_telegram_message(chat_id, response_text, parse_mode="MarkdownV2")
        else:
            send_telegram_message(chat_id, "Sorry, there was an error resetting your password. Please try again later or contact an admin.")

    elif text == "/my_id":
        send_telegram_message(chat_id, escape_markdown_v2(f"Your Telegram ID (and PGCertHE 2025 username) is: {telegram_id_str}"), parse_mode="MarkdownV2")

if __name__ == "__main__":
    print("Bot starting...")
    print("Please set the bot's description/welcome message manually in BotFather on Telegram with the following text:")
    print("---")

    last_update_id = 0
    while True:
        url = f"{TELEGRAM_API_URL}/getUpdates?offset={last_update_id + 1}&timeout=10"
        try:
            response = requests.get(url, timeout=15) # Added timeout to the request itself
            response.raise_for_status()
            updates = response.json()
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    last_update_id = update["update_id"]
                    try:
                        handle_update(update)
                    except Exception as e_handler:
                        print(f"Error handling update {last_update_id}: {e_handler}")
                        # Optionally, send a generic error message to the user if appropriate
                        # if "message" in update and "chat" in update["message"]:
                        #    send_telegram_message(update["message"]["chat"]["id"], "Sorry, an internal error occurred.")
            # No sleep needed here if using long polling with timeout on getUpdates
        except requests.exceptions.Timeout:
            print("Telegram getUpdates request timed out. Retrying...") # server did not send a response in time
        except requests.exceptions.ConnectionError:
            print("Telegram connection error. Retrying in 5 seconds...")
            time.sleep(5)
        except requests.exceptions.RequestException as e:
            print(f"Error polling Telegram: {e}")
            if e.response is not None:
                print(f"Telegram API Error on getUpdates ({e.response.status_code}): {e.response.text}")
            time.sleep(5)
        except Exception as e_main_loop:
            print(f"An unexpected error occurred in the main loop: {e_main_loop}")
            time.sleep(5)
        # time.sleep(0.5) # This sleep might be too short or unnecessary if using long polling effectively.
                          # Telegram recommends not polling more than once every few seconds if not using long polling.
                          # Since timeout=10 is used, this sleep is likely fine or can be removed.