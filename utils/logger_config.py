import logging
import os
from datetime import datetime


def setup_logger(
    logger_name="app",
    log_dir="logs",
    log_level=logging.INFO,
):
    """
    Create and configure a reusable logger.
    All logs will be stored inside log_dir.
    """

    # 获取项目根目录（向上一级）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, log_dir)

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_path, f"{logger_name}_{timestamp}.log")

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # 防止重复添加 handler（非常重要）
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger