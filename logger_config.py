import logging

# def setup_logging(name="mybot"):
#     logging.basicConfig(
#         level=logging.DEBUG,
#         format="%(asctime)s [%(levelname)s] %(message)s",
#         datefmt="%H:%M:%S",
#     )

#     file_handler = logging.FileHandler(f"logs\\{name}.log", encoding="utf-8")
#     formatter = logging.Formatter(
#         "%(asctime)s [%(levelname)s] %(message)s",
#         datefmt="%H:%M:%S"
#     )
#     file_handler.setFormatter(formatter)

#     logging.getLogger().addHandler(file_handler)

#     return logging.getLogger(name)
import os
import sys

def setup_logging(name="mybot"):
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )

    # 文件输出
    file_handler = logging.FileHandler(f"logs/{name}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 终端输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger
