from actions.action_test import Action
from actions.action_test import ContinueResult

class LoginAction(Action):
    def __init__(self):
        super().__init__()
        self.phase = "LOGIN"

    def execute(self):
        if self.phase == "LOGIN":
            res = self.start()

            if res == ContinueResult.SUCCESS:
                self.phase = "HANDLE_LOGIN_POPUPS"

            return res
        
        elif self.phase == "HANDLE_LOGIN_POPUPS":
            res = self.handle_login_popups()

            if res == ContinueResult.SUCCESS:
                self.phase = "FINISH"
            
            return res
        
        elif self.phase == "FINISH":
            return ContinueResult.STOP
    
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
    loginaction = LoginAction()
    loginaction.perform_loginaction_with_retries()