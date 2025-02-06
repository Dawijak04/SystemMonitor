import logging
from colorlog import ColoredFormatter


def setup_logging(config):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console Handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config.get("logging", {}).get("console_level", "INFO"))
    
    # Color formatter
    color_formatter = ColoredFormatter(
        "%(log_color)s" + config.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s") + "%(reset)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(color_formatter)
    
    # File Handler
    file_handler = logging.FileHandler(config.get("logging", {}).get("log_file", "app.log"))
    file_handler.setLevel(config.get("logging", {}).get("file_level", "INFO"))
    formatter = logging.Formatter(config.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger



