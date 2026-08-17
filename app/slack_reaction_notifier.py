import logging
import sys
from pathlib import Path

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from app.config import settings


def setup_logging() -> None:
    """Configure logging for the application."""
    log_level = settings.LOGGING_LEVEL.upper()
    third_party_level = settings.LOGGING_LEVEL_FOR_THIRD_PARTY_LIBS.upper()

    # Configure third-party loggers
    for logger_name in ["slack_bolt", "slack_sdk", "urllib3"]:
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
app = App(token=settings.SLACK_BOT_TOKEN, logger=app_logger)


@app.event("reaction_added")
def handle_reaction_events(event, say, l_logger=app_logger):
    """Handle reaction_added events from Slack."""
    l_logger.debug(f"Reaction event captured: {event}")

    user_who_reacted = event["user"]
    emoji_name = event["reaction"]
    item_user = event.get("item_user")

    # Debugging/Testing: Self-reaction
    if user_who_reacted == item_user:
        l_logger.debug("Self-reaction detected. Sending debug notification...")
        say(
            text=f"🧪 Debug test: you added a :{emoji_name}: reaction to your own message!",
            channel=user_who_reacted
        )
        return

    # Notification for the target user (configured via settings)
    if item_user == settings.MY_SLACK_ID:
        l_logger.debug(f"User {user_who_reacted} reacted to your message. Sending notification...")
        say(
            text=f"🔔 User <@{user_who_reacted}> added a :{emoji_name}: reaction to your message!",
            channel=settings.MY_SLACK_ID
        )


def main(l_logger=app_logger):
    """Main entry point for the application."""
    l_logger.info("Initializing Socket Mode Handler and starting the app...")
    try:
        handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
        handler.start()
    except KeyboardInterrupt:
        l_logger.info("Application interrupted by user.")
    except Exception as e:
        l_logger.critical(f"Unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    finally:
        l_logger.info("Slack Reaction Notifier service stopped.")


if __name__ == "__main__":
    main()
