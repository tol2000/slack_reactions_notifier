import logging
import sys
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from app.config import settings

UNKNOWN_LINK_STR = "Unknown Link"


def setup_logging() -> None:
    """Configure logging for the application."""
    log_level = settings.LOGGING_LEVEL.upper()
    third_party_level = settings.LOGGING_LEVEL_FOR_THIRD_PARTY_LIBS.upper()

    # Configure third-party loggers
    for logger_name in ["slack_bolt", "slack_sdk", "urllib3", "websocket"]:
        logging.getLogger(logger_name).setLevel(third_party_level)
    
    script_dir = Path(__file__).resolve().parent
    logs_dir = script_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file_path = logs_dir / "slack_notifier.log"

    # Define custom formatters
    fmt_screen = logging.Formatter("%(asctime)s  %(levelname)s \t%(name)s \t%(message)s")
    fmt_file = logging.Formatter(
        "pid: %(process)d \tapp: %(name)s \tline: %(lineno)d \tlvl: %(levelname)s \ttime: %(asctime)s \tmsg: %(message)s"
    )

    # Stream (Screen) Handler
    screen_handler = logging.StreamHandler(sys.stdout)
    screen_handler.setLevel(log_level)
    screen_handler.setFormatter(fmt_screen)

    # File Handler
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(fmt_file)

    # App-level logger setup (serves as a base for children)
    base_logger = logging.getLogger("SlackNotifier")
    base_logger.setLevel(log_level)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not base_logger.handlers:
        base_logger.addHandler(screen_handler)
        base_logger.addHandler(file_handler)


# Initialize logging and Slack app
setup_logging()
app_logger = logging.getLogger("SlackNotifier.main")

# Hybrid Token Setup:
# - app uses SLACK_USER_TOKEN to monitor events and read channels as the user
# - bot_client uses SLACK_BOT_TOKEN to send notifications as the bot
app = App(token=settings.SLACK_USER_TOKEN)
bot_client = WebClient(token=settings.SLACK_BOT_TOKEN)


def send_bot_notification(channel: str, text: str):
    """Send a notification message using the bot token."""
    bot_client.chat_postMessage(
        channel=channel,
        text=text
    )


@app.event("reaction_added")
def handle_reaction_events(event):
    """Handle reaction_added events from Slack."""
    app_logger.debug(f"Reaction event captured: {event}")

    user_who_reacted = event["user"]
    emoji_name = event["reaction"]
    item_user = event.get("item_user")
    item = event.get("item", {})
    channel_id = item.get("channel")
    message_ts = item.get("ts")

    if item_user == settings.MY_SLACK_ID or not settings.NOTIFY_REACT_ONLY_ON_MY_MESSAGES:
        # Fetch permalink for the message
        permalink = UNKNOWN_LINK_STR
        if channel_id and message_ts:
            try:
                response = app.client.chat_getPermalink(channel=channel_id, message_ts=message_ts)
                if response.get("ok"):
                    permalink = response.get("permalink", UNKNOWN_LINK_STR)
            except Exception as e:
                app_logger.warning(f"Could not fetch permalink: {e}")

        # Generic notification for all captured reactions
        app_logger.debug(f"Reaction by {user_who_reacted} detected. Sending notification...")
        send_bot_notification(
            channel=settings.MY_SLACK_ID,
            text=(
                f"📢 User <@{user_who_reacted}> added a :{emoji_name}: reaction to a message "
                f"🔗 {permalink}"
            )
        )
    else:
        app_logger.debug(f"Reaction to someone else's message ({item_user}) skipped.")


def main():
    """Main entry point for the application."""
    app_logger.info("Initializing Socket Mode Handler and starting the app...")
    try:
        handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
        handler.start()
    except KeyboardInterrupt:
        app_logger.info("Application interrupted by user.")
    except Exception as e:
        app_logger.critical(f"Unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        app_logger.info("Slack Reaction Notifier service stopped.")


if __name__ == "__main__":
    main()
