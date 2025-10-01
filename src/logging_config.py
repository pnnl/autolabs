import logging
import os

# Get the log file path from the user
log_dir = os.environ["logging_dir"]
log_path = f"../evals/{log_dir}/main.log"

# Ensure the directory exists
# os.makedirs(os.path.dirname(log_path), exist_ok=True)

# Set up the logger
logger = logging.getLogger("main_logger")

if logger.hasHandlers():
    logger.handlers.clear()

logger.setLevel(logging.DEBUG)

# Create file handler with the user-specified path
handler = logging.FileHandler(log_path, mode="w")
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)
