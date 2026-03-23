from actions.action_test import Action
from actions.action_test import ContinueResult
from actions.action_test import FlowResult


PHASE_FLOW = {
    "ENTER": ("do_enter", "SELECT_SLOT"),
    "SELECT_SLOT": ("do_select_slot", "BUY_CONFIRM"),
    "BUY_CONFIRM": ("do_buy_confirm", "REFRESH"),
    # "REFRESH": ("do_refresh", "BACK_HOME"),
    "REFRESH": ("do_refresh", "FINISH"),
    # "BACK_HOME": ("do_back_home", "FINISH"),
    "FINISH": (None, None),
}


class ShoppingStrategy:
    def enter(self, action):...

    def claim(self, action):...

    # def back_home(self, action):
    #     return action.back_to_home()


class ShoppingAction(Action):
    def __init__(self, location, slots, refresh):
        super().__init__()
        self.loaction = location
        self.slots = slots
        self.refresh = refresh
        self.cur_page = 0
        self.phase = "ENTER"

    def do_enter(self):
        return self.enter_shop(self.loaction)
    
    def do_select_slot(self):
        return self.select_slots(self.slots)
    
    def do_buy_confirm(self):
        return self.buy_confirm()
    
    def do_refresh(self):
        return self.refresh_slot()
    
    # def do_back_home(self):
    #     return self.back_to_home()
    
    def execute(self):
        method_name, next_phase = PHASE_FLOW[self.phase]

        if method_name is None:
            return ContinueResult.STOP

        res = getattr(self, method_name)()

        if res.signal == ContinueResult.SUCCESS:
            self.phase = next_phase

        elif res.signal == ContinueResult.GO_TO:
            self.phase = res.target

        return res.signal
    
    def perform_action_with_retries(self, max_retries=10):
        retry_count = 0
        result = ContinueResult.RETRY

        while result != ContinueResult.STOP and retry_count < max_retries:
            result = self.execute()

            if result == ContinueResult.SUCCESS:
                self.logger.info("Enter next stage.")

            elif result == ContinueResult.GO_TO:
                self.logger.info("Jumping to 'SELECT_SLOT'.")

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