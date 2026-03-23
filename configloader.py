import json
import logger_config
from pathlib import Path
from actions.login import LoginAction
from actions.claim import (
    ClaimAction,
    ClaimGroupStrategy,
    ClaimMailboxStrategy,
    ClaimTasksStrategy,
    ClaimCafeStrategy
)
from actions.sweep import (
    SweepAction,
    BountySweepStrategy,
    QuestSweepStrategy,
    ScrimmageSweepStrategy
)
from actions.shopping import ShoppingAction

logger = logger_config.setup_logging("configloader")

STRATEGY_MAP = {
    "bounty": BountySweepStrategy,
    "quest": QuestSweepStrategy,
    "scrimmage": ScrimmageSweepStrategy,
    "group": ClaimGroupStrategy,
    "mailbox": ClaimMailboxStrategy,
    "tasks": ClaimTasksStrategy,
    "shop": ShoppingAction
}


# ACTION_FACTORY = {
#     "login": create_login_action,
#     "sweep": create_sweep_action,
#     "shop": create_shop_action,
# }


class ConfigLoader:
    def __init__(self, path="config/config.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def load_actions(self, profile: str):
        profiles = self.config["profiles"]
        actions_cfg = self.config["actions"]

        if profile not in profiles:
            raise ValueError(f"Unknown profile: {profile}")

        action_ids = profiles[profile]
        actions = []

        for action_id in action_ids:
            cfg = actions_cfg[action_id]
            action = self._create_action(cfg)
            
            for act in action:
                actions.append(act)

        return actions

    # def _validate(self):
    #     if "actions" not in self.config:
    #         raise ValueError("config missing 'actions'")

    #     if "plans" not in self.config:
    #         raise ValueError("config missing 'plans'")

    #     for act in self.config["actions"]:
    #         if act["type"] == "sweep":
    #             mode = act["mode"]
    #             plan = act["plan"]

    #             if mode not in self.config["plans"]:
    #                 raise ValueError(f"unknown mode: {mode}")

    #             if plan not in self.config["plans"][mode]:
    #                 raise ValueError(f"unknown plan: {mode}.{plan}")

    #             if mode not in STRATEGY_MAP:
    #                 raise ValueError(f"no strategy for mode: {mode}")
                
    #         if act["type"] == "login":
    #             pass

    def _create_action(self, cfg: dict):
        action_type = cfg["type"]

        if action_type == "login":
            return [LoginAction()]

        elif action_type == "sweep":
            return self._create_sweep_action(cfg)

        elif action_type == "claim":
            return self._create_claim_action(cfg)
        
        elif action_type == "shop":
            return self._create_shop_action(cfg)

        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _create_sweep_action(self, cfg: dict):
        mode = cfg["mode"]
        plan_name = cfg["plan"]

        plans = self._load_plan(mode, plan_name)

        strategy = {
            "bounty": BountySweepStrategy(),
            "quest": QuestSweepStrategy(),
            "scrimmage": ScrimmageSweepStrategy()
        }[mode]

        return [
            SweepAction(
            name=plan["location"],
            stage=plan["stage"],
            runs=plan["runs"],
            strategy=strategy,
        )for plan in plans
        ]

    def _create_claim_action(self, cfg: dict):
        mode = cfg["mode"]

        strategy = {
            "group": ClaimGroupStrategy(),
            "mailbox": ClaimMailboxStrategy(),
            "tasks": ClaimTasksStrategy(),
            "cafe": ClaimCafeStrategy()
        }[mode]

        return [ClaimAction(strategy=strategy)]
    
    def _create_shop_action(self, cfg:dict):
        plan_name = cfg["plan"]
        plans = self._load_plan("shop", plan_name)

        return [ShoppingAction(
            location=plan["location"],
            slots=plan["slots"],
            refresh=plan["refresh"]
        )for plan in plans
        ]
    
    def _load_plan(self, mode: str, plan_name: str):
        return self.config["plans"][f"{mode}"][plan_name]


if __name__ == "__main__":
    config = ConfigLoader()
    actions = config.load_actions("full")
    print(actions)