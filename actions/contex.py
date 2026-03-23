from adb_client import ADBClient
from detector import Detector
import logger_config

logger = logger_config.setup_logging("action")

class GameContext:
    def __init__(self):
        self.adb = ADBClient()
        self.detector = Detector()
        self.logger = logger

        self.last_action_time = 0
        self.energy = 0
        self.bounty_ticket = 0
        self.scrimmage_ticket = 0

    
