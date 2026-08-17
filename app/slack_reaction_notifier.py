import os
import sys
import logging
from pathlib import Path
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ==========================================
# 1. ENVIRONMENT VARIABLES CHECK
# ==========================================
bot_token = os.environ.get("SLACK_BOT_TOKEN")
app_token = os.environ.get("SLACK_APP_TOKEN")

if not bot_token or not app_token:
    print("CRITICAL WARNING: Missing required environment variables!", file=sys.stderr)
    print("Please ensure SLACK_BOT_TOKEN and SLACK_APP_TOKEN are set.", file=sys.stderr)
    sys.exit(1)

# ==========================================
# 2. LOGGING CONFIGURATION
# ==========================================
# Get the directory where the script is located and create /logs subdirectory
script_dir = Path(__file__).resolve().parent
logs_dir = script_dir / "logs"
logs_dir.mkdir(exist_ok=True)
log_file_path = logs_dir / "slack_notifier.log"

# Define your custom formatters
fmt_screen = logging.Formatter("%(asctime)s  %(levelname)s \t%(name)s \t%(message)s")
fmt_file = logging.Formatter(
    "pid: %(process)d \tapp: %(name)s \tline: %(lineno)d \tlvl: %(levelname)s \ttime: %(asctime)s \tmsg: %(message)s"
)

# Stream (Screen) Handler
screen_handler = logging.StreamHandler(sys.stdout)
screen_handler.setLevel(logging.INFO)
screen_handler.setFormatter(fmt_screen)

# File Handler
file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(fmt_file)

# Root Logger Setup
logger = logging.getLogger("SlackNotifier")
logger.setLevel(logging.INFO)
logger.addHandler(screen_handler)
logger.addHandler(file_handler)

# ==========================================
# 3. SLACK APPLICATION SETUP
# ==========================================
# Pass our custom logger directly to the Bolt App
app = App(token=bot_token, logger=logger)


@app.event("reaction_added")
def handle_reaction_events(event, say, logger):
    logger.info(f"Reaction event captured: {event}")

    user_who_reacted = event["user"]
    emoji_name = event["reaction"]
    item_user = event.get("item_user")

    # --- DEBUGGING / TESTING ZONE ---
    # Triggered if you react to your own message
    if user_who_reacted == item_user:
        logger.info("Self-reaction detected. Sending debug notification...")
        say(
            text=f"🧪 Debug test: you added a :{emoji_name}: reaction to your own message!",
            channel=user_who_reacted
        )
        return

    # --- PRODUCTION MODE (FOR COLLEAGUES) ---
    # Replace "YOUR_USER_ID" with your real Slack Member ID
    MY_SLACK_ID = "YOUR_USER_ID"

    if item_user == MY_SLACK_ID:
        logger.info(f"User {user_who_reacted} reacted to your message. Sending notification...")
        say(
            text=f"🔔 User <@{user_who_reacted}> added a :{emoji_name}: reaction to your message!",
            channel=MY_SLACK_ID
        )


if __name__ == "__main__":
    logger.info("Initializing Socket Mode Handler...")
    handler = SocketModeHandler(app, app_token)
    handler.start()
