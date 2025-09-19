from rich.console import Console
from datetime import datetime

class SingletonMeta(type):
    """
    A metaclass that creates a Singleton instance.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        # If an instance does not exist, create one
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        # Return the existing instance
        return cls._instances[cls]


class ColorLogger(metaclass=SingletonMeta):
    """
    A simple color logger using the rich library for different log levels.
    """

    def __init__(self, show_time: bool = True):
        """
        Initialize the ColorLogger.

        :param show_time: Whether to prefix log messages with a timestamp.
        """
        self.console = Console()
        self.show_time = show_time
        # Mapping of log levels to rich styles
        self.styles = {
            "debug": "dim",
            "info": "green",
            "warning": "yellow",
            "error": "bold red",
            "critical": "red on white"
        }

    def _get_time_prefix(self) -> str:
        """
        Returns the current time as a formatted string if show_time is enabled.

        :return: Time prefix string.
        """
        return datetime.now().strftime("[%Y-%m-%d %H:%M:%S]") if self.show_time else ""

    def _log(self, level: str, message: str):
        """
        Internal method to format and print log messages based on the level.

        :param level: Log level string.
        :param message: The log message.
        """
        style = self.styles.get(level.lower(), "white")
        time_prefix = self._get_time_prefix()
        # Format the log message; adjust the format as needed
        log_message = f"{time_prefix} [{level.upper()}] {message}"
        # Use rich markup to apply color styles
        self.console.print(f"[{style}]{log_message}[/]")

    def debug(self, message: str):
        """
        Log a message with the DEBUG level.

        :param message: Debug message.
        """
        self._log("debug", message)

    def info(self, message: str):
        """
        Log a message with the INFO level.

        :param message: Information message.
        """
        self._log("info", message)

    def warning(self, message: str):
        """
        Log a message with the WARNING level.

        :param message: Warning message.
        """
        self._log("warning", message)

    def error(self, message: str):
        """
        Log a message with the ERROR level.

        :param message: Error message.
        """
        self._log("error", message)

    def critical(self, message: str):
        """
        Log a message with the CRITICAL level.

        :param message: Critical error message.
        """
        self._log("critical", message)

logger = ColorLogger(show_time=True)

if __name__ == '__main__':
    # Create a singleton instance of ColorLogger
    logger = ColorLogger(show_time=True)

    logger.debug("This is a debug message.")
    logger.info("Program is running.")
    logger.warning("A warning has occurred.")
    logger.error("An error has occurred.")
    logger.critical("Critical error! Program terminated.")