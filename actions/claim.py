from actions.action_test import Action
from actions.action_test import ContinueResult


PHASE_FLOW = {
    "ENTER": ("do_enter", "CLAIM"),
    "CLAIM": ("do_claim", "BACK_HOME"),
    "BACK_HOME": ("do_back_home", "FINISH"),
    "FINISH": (None, None),
}


class ClaimStrategy:
    def enter(self, action):...

    def claim(self, action):...

    def back_home(self, action):
        return action.back_to_home()
    

class ClaimGroupStrategy(ClaimStrategy):
    def enter(self, action):
        return action.enter_group()
    
    def claim(self, action):
        return action.claim_group_rewards()
    

class ClaimMailboxStrategy(ClaimStrategy):
    def enter(self, action):
        return action.enter_mailbox()
    
    def claim(self, action):
        return action.claim_mailbox_rewards()
    

class ClaimTasksStrategy(ClaimStrategy):
    def enter(self, action):
        return action.enter_tasks()
    
    def claim(self, action):
        return action.claim_tasks()


class ClaimCafeStrategy(ClaimStrategy):
    def enter(self, action):
        return action.enter_cafe()
    
    def claim(self, action):
        return action.claim_cafe_energy()
    

class ClaimAction(Action):
    def __init__(self, strategy):
        super().__init__()
        self.strategy = strategy
        self.phase = "ENTER"

    def do_enter(self):
        return self.strategy.enter(self)
    
    def do_claim(self):
        return self.strategy.claim(self)
    
    def do_back_home(self):
        return self.strategy.back_home(self)
    
    def execute(self):
        method_name, next_phase = PHASE_FLOW[self.phase]

        if method_name is None:
            return ContinueResult.STOP

        res = getattr(self, method_name)()

        if res == ContinueResult.SUCCESS:
            self.phase = next_phase

        return res
    
    def perform_action_with_retries(self, max_retries=10):
        retry_count = 0
        result = ContinueResult.RETRY

        while result != ContinueResult.STOP and retry_count < max_retries:
            result = self.execute()

            if result == ContinueResult.SUCCESS:
                self.logger.info("Enter next stage.")

            elif result == ContinueResult.RETRY:
                self.logger.info(f"attempt {retry_count + 1}/{max_retries}")
                retry_count += 1
                continue

            elif result == ContinueResult.STOP and self.phase == "FINISH":
                self.logger.info("Action completed successfully.")
                return ContinueResult.SUCCESS
            
            else:
                self.logger.error(f"Action failed with result: {result} and phase: {self.phase}.")
                return ContinueResult.STOP

        self.logger.error("Exceeded maximum retries.")
        return ContinueResult.STOP
    
if __name__ == "__main__":
    # claim = ClaimAction(ClaimMailboxStrategy())
    claim = ClaimAction(ClaimTasksStrategy())
    claim.perform_claimaction_with_retries()