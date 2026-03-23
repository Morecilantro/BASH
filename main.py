import logger_config
from configloader import ConfigLoader
from actions.action_test import ContinueResult
import time

logger = logger_config.setup_logging("mybot")

ACTION_MAP = [
    "full",
    "login",
    "shop",
    "task",
    "cafe"
]

def main(profile):
    loader = ConfigLoader()
    # print("test")
    actions = loader.load_actions(profile)

    for action in actions:
        # print("test")
        action.perform_action_with_retries()


if __name__ == "__main__":
    main(ACTION_MAP[2])
    # timeout=10
    # start_time = time.time()

    # while time.time() - start_time < timeout:
    #     print("test")