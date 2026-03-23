from actions.action_test import Action
from actions.action_test import ContinueResult


PHASE_FLOW = {
    "UPDATE_RESOURCE": ("do_update_resource", "ENTER_STAGE"),
    "ENTER_STAGE": ("do_enter_stage", "ENTER_SWEEP_PAGE"),
    "ENTER_SWEEP_PAGE": ("do_enter_sweep_page", "EXECUTE_SWEEP"),
    "EXECUTE_SWEEP": ("do_execute_sweep", "HANDLE_RESULT"),
    "HANDLE_RESULT": ("do_handle_result", "FINISH"),
    "FINISH": (None, None),
}


class SweepStrategy:
    def update_resource(self, action): ...
    
    def enter_stage(self, action): ...
       
    def enter_sweep_page(self, action):
        return action.enter_sweep_page(action.stage)
    
    def execute_sweep(self, action): ...

    def handle_result(self, action):
        return action.handle_sweep_result()


class QuestSweepStrategy(SweepStrategy):
    def update_resource(self, action):
        return action.update_energy()
    
    def enter_stage(self, action):
        return action.enter_missions_area(action.location, action.stage)
    
    def execute_sweep(self, action):
        return action.sweep_missions(action.location, action.stage, action.runs)


class BountySweepStrategy(SweepStrategy):
    def update_resource(self, action):
        return action.update_bounty_ticket()
    
    def enter_stage(self, action):
        return action.enter_bounty_location(action.location)
    
    def execute_sweep(self, action):
        return action.execute_sweep_with_ticket(action.bounty_ticket, action.runs)


class ScrimmageSweepStrategy(SweepStrategy):
    def update_resource(self, action):
        return action.update_scrimmage_ticket_and_energy()
    
    def enter_stage(self, action):
        return action.enter_scrimmage_location(action.location)
    
    def execute_sweep(self, action):
        return action.sweep_scrimmage(action.location, action.stage, action.runs)


class SweepAction(Action):
    def __init__(self, name, stage, runs, strategy):
        super().__init__()
        self.location = name
        self.stage = stage
        self.runs = runs
        self.strategy = strategy
        self.phase = "UPDATE_RESOURCE"

    def do_update_resource(self):
        return self.strategy.update_resource(self)
    
    def do_enter_stage(self):
        return self.strategy.enter_stage(self)
    
    def do_enter_sweep_page(self):
        return self.strategy.enter_sweep_page(self)
    
    def do_execute_sweep(self):
        return self.strategy.execute_sweep(self)
    
    def do_handle_result(self):
        return self.strategy.handle_result(self)

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
    sweep = SweepAction("classroom", 10, 6, strategy=BountySweepStrategy())
    sweep = SweepAction("hard", 293, 3, strategy=QuestSweepStrategy())
    sweep = SweepAction("Trinity", 4, 2, strategy=ScrimmageSweepStrategy())
    sweep = SweepAction("Gehenna", 4, 2, strategy=ScrimmageSweepStrategy())
    sweep = SweepAction("Millennium", 4, 2, strategy=ScrimmageSweepStrategy())
    # sweep.perform_sweepaction_with_retries()