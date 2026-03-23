from detector import Detector
import logger_config
from adb_client import ADBClient
from enum import Enum
import time
import os
import cv2
# import re
from dataclasses import dataclass

logger = logger_config.setup_logging("action")

#1600*900
empty_pos = (400, 40)
social_pos = (700, 800)
group_pos = (400, 500)
mailbox_pos = (1420, 70)
task_pos = (80, 300)
claim_all_pos = (1420, 840)
claim_diamond_pos = (1200, 840)
shop_pos = (1000, 800)
missions_pos = (1000, 300)
bounty_pos = (900, 500)
commissions_pos = (900, 625)
scrimmage_pos = (900, 750)
highway_pos = (1000, 250)
railway_pos = (1000, 400)
classroom_pos = (1000, 550)
Trinity_pos = (1000, 250)
Gehenna_pos = (1000, 400)
Millennium_pos = (1000, 550)
bounty_sweep_max_pos = (1350, 380)
bounty_sweep_add_pos = (1270, 380)
bounty_sweep_sub_pos = (1070, 380)
sweep_max_pos = (1350, 390)
sweep_add_pos = (1270, 390)
sweep_sub_pos = (1070, 390)
sweep_start_pos = (1165, 530)
missions_select_left_arrow_pos = (50, 450)
missions_select_right_arrow_pos = (1550, 450)
shop_currency_1_pos = (100, 170)
shop_currency_4_pos = (100, 470)
shop_slot_0_pops = (875, 300)
slot_dx = 187
slot_dy = 320
buy_button_pos = (1455, 825)
buy_confirm_pos = (960, 720)
refresh_confirm_pos = (960, 600)
# shop_slot_1_pos = (1060, 300)
# shop_slot_2_pos = (1250, 300)
# shop_slot_3_pos = (1435, 300)
# shop_slot_4_pos = (875, 620)
# shop_slot_5_pos = (1060, 620)
# shop_slot_6_pos = (1250, 620)
# shop_slot_7_pos = (1435, 620)
cafe_pos = (120, 820)
cafe_rewards_pos = (1450, 820)
cafe_claim_pos = (800, 660)

energy_box_home = (610, 30, 720, 65)
energy_box_not_home = (660, 17, 780, 50)
bounty_ticket_box = (210, 110, 270, 150)
scrimmage_ticket_box = (210, 110, 270, 150)
bounty_stage_box = (880, 200, 930, 820)
bounty_entrance_box = (1320, 180, 1470, 840)
bounty_sweep_times_box = (1140, 350, 1200, 395)
stage_box = (860, 200, 940, 810)
entrance_box = (1320, 200, 1470, 840)
sweep_times_box = (1140, 360, 1200, 390)
mission_sweep_times_box = (1140, 400, 1200, 430)
shop_slot_box = (765, 145, 1535, 766)


class ContinueResult(Enum):
    STOP = 0
    SUCCESS = 1
    RETRY = 2
    GO_TO = 4


@dataclass
class FlowResult:
    signal: ContinueResult
    target: str | None = None


class Action:
    def __init__(self):
        self.detector = Detector()
        self.adb_client = ADBClient()
        self.logger = logger
        self.screenshot_path = os.path.join("screenshot", "cur.png")
        self.last_action_time = 0
        self.energy = 0
        self.bounty_ticket = 0
        self.scrimmage_ticket = 0
        # self.refresh = 0

    # def adjust_resolution_to_present_device(self, x, y, width=1600, height=900):
    #     x_ratio = x / width
    #     y_ratio = y / height
    #     return int(self.adb_client.screen_width * x_ratio), int(self.adb_client.screen_height * y_ratio)

    def time_wait(self, action_interval = 0.5):
        current_time = time.time()
        if current_time - self.last_action_time < action_interval:
            time.sleep(action_interval - (current_time - self.last_action_time))
        self.last_action_time = time.time()

    def tap_screen(self, x, y, interval = 0.5):
        self.time_wait(interval)

        # if adjust:
        #     x, y = self.adjust_resolution_to_present_device(x, y)

        self.adb_client.tap_screen(x, y)
        self.last_action_time = time.time()

    def back_screen(self, interval = 0.5):
        self.time_wait(interval)
        self.adb_client.keyevent("4")
        self.last_action_time = time.time()

    def swipe_screen(self, start, end, dur, interval = 0.5):
        self.time_wait(interval)

        # if adjust:
        #     start = self.adjust_resolution_to_present_device(*start)
        #     end = self.adjust_resolution_to_present_device(*end)

        self.adb_client.swipe_screen(start[0], start[1], end[0], end[1], dur)
        self.last_action_time = time.time()

    def wait_loading(self, time=1):
        if self.detector.is_loading():
                logger.info("Loading...")
                self.time_wait(time)
                self.update_screenshot(0)

    def read_pre_screenshot(self):
        return cv2.imread(self.screenshot_path, cv2.IMREAD_GRAYSCALE)

    def update_screenshot(self, interval = 1):
        self.time_wait(interval)
        self.adb_client.get_current_screenshot("cur")
        self.last_action_time = time.time()

    def update_energy(self, timeout=10):
        logger.info("Attempting to update energy.")
        star_time = time.time()

        while time.time() - star_time < timeout:
            self.handle_popups_and_updatescreen()
            self.wait_loading()

            if self.detector.is_task_popup():
                logger.info("Task popup detected, waiting...")
                self.time_wait(1)
                continue

            if self.detector.is_in_home_screen():
                number = self.detector.get_energy(home=True)

            else:
                number = self.detector.get_energy(home=False)

            if number == None:
                logger.warning("Fail to update energy, retrying...")
                self.tap_screen(*empty_pos)
            
            else:
                self.energy = number
                logger.info("Update energy successfully.")
                return ContinueResult.SUCCESS
        
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def update_bounty_ticket(self, timeout=30):
        logger.info("Attempting to update bounty tickets.")
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            self.wait_loading()

            if not self.detector.is_in_bounty_screen():
                logger.info("Not in bounty screen yet, attempting to enter.")
                
                # back = self.detector.find_back_button()
                # if back != None:
                #     self.tap_screen(*back)
                #     self.time_wait(1)
                
                self.enter_bounty()

            logger.info("Attempting to update bounty ticket number.")
            res = self.detector.get_bounty_ticket()
            
            if res  != None:
                if res <= 0:
                    logger.error("Insufficient ticket.")
                    return ContinueResult.STOP
            
                self.bounty_ticket = res
                return ContinueResult.SUCCESS
            
            logger.warning("Fail to update bounty ticket number, retrying...")

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY
    
    def update_scrimmage_ticket_and_energy(self, timeout=30):
        logger.info("Attempting to update scrimmage tickets.")
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            self.wait_loading()

            if not self.detector.is_in_scrimmage_screen():
                logger.info("Not in scrimmage screen yet, attempting to enter.")
                
                # back = self.detector.find_back_button()
                # if back != None:
                #     self.tap_screen(*back)
                #     self.time_wait(1)
                
                self.enter_scrimmage()
            
            logger.info("Attempting to update scrimmage ticket number.")
            res = self.detector.get_scrimmage_ticket()

            if res  != None:
                if res <= 0:
                    logger.error("Insufficient ticket.")
                    return ContinueResult.STOP
     
                self.scrimmage_ticket = res
                self.update_energy()

                if self.energy < 15:
                    logger.error("Insufficient energy.")
                    return ContinueResult.STOP
                
                return ContinueResult.SUCCESS
            
            logger.warning("Fail to update scrimmage ticket number, retrying...")

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def start(self, timeout=60):
        logger.info("Getting start...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            # self.time_wait(5)
            # self.wait_loading(2)

            res = self.detector.find_BA_icon()

            if res:
                logger.info("In simulator screen, attemping to start.")
                self.tap_screen(*res)

            if self.detector.is_in_login_screen():
                logger.info("In login screen, attempting to login.")
                self.tap_screen(*empty_pos)

            res = self.detector.is_everyday_login_popup()

            if res:
                logger.info("Everyday login popup detected, attempting to close it.")
                self.tap_screen(*empty_pos)
                self.time_wait(2)

            res = self.detector.is_login_event_popup()

            if res:
                logger.info("Login event popup detected, attempting to close it.")
                self.handle_event_popup()
                # self.time_wait()

            if self.detector.is_in_home_screen() or self.detector.is_other_popup() or self.detector.find_home_button():
                logger.info("Successfully reached game screen.")
                return ContinueResult.SUCCESS
            
            # logger.info("Detected nothing, retrying...")
            logger.info("Wait loading...")
            self.time_wait(1)

        logger.warning("Failed to complete action within timeout.")
        return ContinueResult.RETRY
    
    def handle_popups_and_updatescreen(self, interval=0.5, off_notice=False):
        self.update_screenshot(interval)

        if self.detector.is_reconnect_popup():
            self.handle_reconnect_popup()
            self.update_screenshot(2.5)

        if self.detector.is_login_from_store_popup():
            self.handle_login_from_store_popup()
            self.update_screenshot()

        if self.detector.is_notice_popup() and not off_notice:
            self.handle_notice_popups()
            self.update_screenshot()

    def handle_login_popups(self, stable=5, timeout=15):
        logger.info("Attempting to clear home screen.")
        start_time = time.time()
        last_popup_time = time.time()

        while time.time() - start_time < timeout and time.time() - last_popup_time < stable:
            self.update_screenshot()

            if self.detector.is_reconnect_popup():
                self.handle_reconnect_popup()
                # self.update_screenshot(3)
                last_popup_time = time.time()
                continue

            if self.detector.is_other_popup():
                self.handle_other_popups()
                # self.update_screenshot(1)
                last_popup_time = time.time()
                continue

            if self.detector.is_login_from_store_popup():
                self.handle_login_from_store_popup()
                # self.update_screenshot()
                last_popup_time = time.time()
                continue

            if self.detector.is_notice_popup():
                self.handle_notice_popups()
                # self.update_screenshot()
                last_popup_time = time.time()
                continue

        if time.time() - last_popup_time >= stable and (self.detector.is_in_home_screen() or self.detector.find_home_button()):
            logger.info("All popups closed.")
            return ContinueResult.SUCCESS

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def handle_reconnect_popup(self):
        logger.info("Reconnect popup detected, attempting to reconnect.")
        pos = self.detector.is_reconnect_popup()
        self.tap_screen(*pos)

    def handle_event_popup(self):
        logger.info(f"Event popup detected, attempting to close it.")
        pos = self.detector.is_login_event_popup()
        self.tap_screen(*pos)

    def handle_login_from_store_popup(self):
        logger.info(f"Login from store popup detected, attempting to close it.")
        self.tap_screen((800, 450), 0.1)
        pos = self.detector.is_login_from_store_popup()

        for i in range(3):
            self.tap_screen(*pos, 0.1)

        confirm_pos = self.detector.find_confirm_button()
        
        if confirm_pos:
            self.tap_screen(*confirm_pos)
        
        else:
            logger.error("Confirm button not found.")

    def handle_notice_popups(self):
        logger.info(f"Notice popup detected, attempting to close it.")
        pos = self.detector.find_confirm_button()

        if pos:
            self.tap_screen(*pos)

        else:
            logger.error("Confirm button not found.")

    def handle_other_popups(self):
        logger.info(f"Other popup detected, attempting to close it.")
        pos = self.detector.is_other_popup()
        self.tap_screen(*pos)

    def handle_sweep_result(self, timeout=10):
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            self.wait_loading()

            if self.detector.is_in_sweep_settlement_page():
                logger.info("In settlement page ,attempting to close it.")
                pos = self.detector.find_close_button()

                if pos:
                    self.tap_screen(*pos, 0)
                    self.adb_client.keyevent(4)
                    return ContinueResult.SUCCESS

                logger.info("Fail to close settlement page.")

        logger.error("Sweep result handling timeout.")
        return ContinueResult.RETRY

    def back_to_home(self, timeout=10):
        logger.info("Attempting to return to home screen.")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_home_screen():
                logger.info("Successfully returned to home screen.")
                return ContinueResult.SUCCESS

            pos = self.detector.find_home_button()

            if pos:
                logger.info("Home button detected, tapping it.")
                self.tap_screen(*pos)
                tapped = True

            elif not tapped:
                logger.error("Home button not found, retrying.")
                self.adb_client.keyevent(4)
            
            else:
                logger.info("Wait loading...")
            
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_cafe(self, timeout=15):
        logger.info("Attempting to enter cafe.")
        self.tap_screen(*empty_pos, 0)
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_cafe_screen():
                logger.info("Successfully entered group.")
                return ContinueResult.SUCCESS
            
            if self.detector.is_in_home_screen():
                logger.info("In home screen, attempting to enter group.")
                self.tap_screen(*cafe_pos)
                tapped = True

            elif not tapped:
                logger.info("Not in home screen, attemptimg to enter.")
                self.back_to_home()

            else:
                logger.info("Wait loading...")
                # self.tap_screen(*empty_pos)

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_group(self, timeout=20):
        logger.info("Attempting to enter group.")
        self.tap_screen(*empty_pos, 0)
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_group_screen():
                logger.info("Successfully entered group.")
                return ContinueResult.SUCCESS

            if self.detector.is_in_home_screen():
                logger.info("In home screen, attempting to enter group.")
                self.tap_screen(*social_pos)
                self.tap_screen(*group_pos)
                tapped = True
            
            elif not tapped:
                logger.info("Not in home screen, attemptimg to enter.")
                self.back_to_home()
            
            else:
                logger.info("Wait loading...")

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_mailbox(self, timeout=20):
        logger.info("Attempting to enter mailbox.")
        self.tap_screen(*empty_pos, 0)
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_mailbox_screen():
                logger.info("Successfully entered mailbox.")
                return ContinueResult.SUCCESS

            if self.detector.is_in_home_screen():
                logger.info("In home screen, attempting to enter mailbox.")
                self.tap_screen(*mailbox_pos)
                tapped = True
            
            elif not tapped:
                logger.info("Not in home screen, attemptimg to enter.")
                self.back_to_home()
            
            else:
                logger.info("Wait loading...")

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_tasks(self, timeout=20):
        logger.info("Attempting to enter task.")
        self.tap_screen(*empty_pos, 0)
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_task_screen():
                logger.info("Successfully entered tasks screen.")
                return ContinueResult.SUCCESS

            if self.detector.is_in_home_screen():
                logger.info("In home screen, attempting to enter task.")
                self.tap_screen(*task_pos)
                tapped = True
    
            elif not tapped:
                logger.info("Not in home screen, attemptimg to enter.")
                self.back_to_home()
    
            else:
                logger.info("Wait loading...")

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_shop(self, currency:str, timeout=20): #健壮性不强
        logger.info(f"Attempting to enter shop: {currency}.")
        self.tap_screen(*empty_pos, 0)
        tapped = False  
        start = (100, 200)
        end = (100, 500)
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_shop_screen():
                logger.info("Successfully entered shop.")

                if currency == "credits":
                    if self.detector.is_in_shop_credits():
                        logger.info("Successfully entered shop: credits.")
                        return FlowResult(ContinueResult.SUCCESS)

                    self.swipe_screen(start, end, 300)
                    self.tap_screen(*shop_currency_1_pos)
                    continue

                elif currency == "tactical_coin":
                    if self.detector.is_in_shop_tactical_coin():
                        logger.info("Successfully entered shop: tactical coin.")
                        return FlowResult(ContinueResult.SUCCESS)
                    
                    self.swipe_screen(end, start, 300)
                    self.tap_screen(*shop_currency_4_pos)
                    continue

                else:
                    logger.error("Invalid currency.")
                    return FlowResult(ContinueResult.STOP)
            
            if self.detector.is_in_home_screen():
                logger.info("In home screen, attempting to enter shop.")
                self.tap_screen(*shop_pos)
                tapped = True

            elif not tapped:
                logger.info("Not in home screen, attemptimg to enter.")
                self.back_to_home()
                continue

            else:            
                logger.info("Wait loading...")

        logger.info("Failed to complete action within timeout.")
        return FlowResult(ContinueResult.RETRY)

    def enter_campaign(self, timeout=10):
        logger.info("Attempting to enter campaign.")
        self.tap_screen(*empty_pos, 0)
        self.tap_screen(*empty_pos, 0.1)
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_campaign_screen():
                logger.info("Successfully entered campaign screen.")
                return ContinueResult.SUCCESS

            res = self.detector.is_in_home_screen()

            if res:
                logger.info("At home screen, attempting to enter campaign.")
                self.tap_screen(*res)
                tapped = True

            elif not tapped:
                logger.info("Not in home screen, attempting to return to home.")
                self.adb_client.keyevent(4)

            else:
                logger.info("Wait loading...")

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_missions(self, mode="hard", timeout=20):
        logger.info("Attempting to enter missions page.")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_missions_page(mode):
                logger.info(f"Successfully entered missions: {mode}")
                return ContinueResult.SUCCESS
            
            elif self.detector.is_in_missions_page("hard") or self.detector.is_in_missions_page("normal"):
                if mode == "hard":
                    logger.info("In missions: normal, switchig to: hard.")
                    pos = self.detector.is_in_missions_page("normal")
                    self.tap_screen(*pos)
                    continue
                
                elif mode == "normal":
                    logger.info("In missions: hard, switchig to: normal.")
                    pos = self.detector.is_in_missions_page("hard")
                    self.tap_screen(*pos)
                    continue

            if self.detector.is_in_campaign_screen():
                logger.info("At campaign screen, attempting to enter missions.")
                self.tap_screen(*missions_pos)
                tapped = True

            elif not tapped:
                logger.info("Not in campaign screen, attempting to enter campaign.")
                self.enter_campaign()
            
            else:
                logger.info("Wait loading...")
                self.tap_screen(*empty_pos)
    
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_missions_area(self, mode="hard", stage=293, timeout=40):
        if self.energy < 10 or self.energy < 20 and mode == "hard":
            logger.error("Insufficient energy.")
            return ContinueResult.STOP

        area = int(stage/10)
        logger.info(f"Attempting to enter {mode} missions Area: {area}.")
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            # self.wait_loading()

            if not self.detector.is_in_missions_page(mode):
                logger.info("Not in missions page, attempting to enter missions.")
                self.enter_missions(mode)

            present_stages = self.detector.get_present_stages()
            
            if present_stages ==None:
                logger.error("Fail to get stages.")
                return ContinueResult.RETRY
            
            present_area = int(present_stages[0]/10)

            if present_area == area:
                logger.info(f"Successfully entered area: {area}.")
                return ContinueResult.SUCCESS

            logger.info("Target not in present page, attempting to redirect to correct page.")
            
            if present_area < area:
                for i in range(area - present_area):
                    self.tap_screen(*missions_select_right_arrow_pos)
                continue
            
            for i in range(present_area - area):
                self.tap_screen(*missions_select_left_arrow_pos)
 
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_bounty(self, timeout=20):
        logger.info("Attempting to enter bounty.")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_bounty_screen():
                logger.info("Successfully entered bounty screen.")
                return ContinueResult.SUCCESS

            if self.detector.is_in_campaign_screen() and not tapped:
                logger.info("At campaign screen, attempting to enter bounty.")
                self.tap_screen(*bounty_pos)
                self.wait_loading()
                tapped = True
            
            elif not tapped:
                logger.info("Not in campaign screen, attempting to enter campaign.")
                self.enter_campaign()
            
            else:
                logger.info("Wait loading...")
                self.tap_screen(*empty_pos)

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_commissions(self, timeout=20):
        logger.info("Attempting to enter commissions.")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_commissions_screen():
                logger.info("Successfully entered commissions screen.")
                return ContinueResult.SUCCESS

            if self.detector.is_in_campaign_screen():
                logger.info("At campaign screen, attempting to enter commissions.")
                self.tap_screen(*commissions_pos)
                tapped = True
            
            elif not tapped:
                logger.info("Not in campaign screen, attempting to enter campaign.")
                self.enter_campaign()
    
            else:
                logger.info("Wait loading...")
                self.tap_screen(*empty_pos)

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_scrimmage(self, timeout=20):
        logger.info("Attempting to enter scrimmage.")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_scrimmage_screen():
                logger.info("Successfully entered scrimmage screen.")
                return ContinueResult.SUCCESS

            if not self.detector.is_in_campaign_screen() and not tapped:
                logger.info("Not in campaign screen, attempting to enter campaign.")
                self.enter_campaign()
            
            elif self.detector.is_in_campaign_screen():
                logger.info("At campaign screen, attempting to enter scrimmage.")
                self.tap_screen(*scrimmage_pos)
                tapped = True

            else:
                logger.info("Wait loading...")
                self.tap_screen(*empty_pos)

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_bounty_location(self, name="classroom", timeout=25):
        logger.info(f"Attempting to enter bounty: {name}.")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_bounty_name(name):
                logger.info(f"Successfully entered {name}.")
                return ContinueResult.SUCCESS
            
            if self.detector.is_in_bounty_screen():
                logger.info(f"In bounty screen, attempting to enter bounty: {name}.")

                if name == "highway":
                    self.tap_screen(*highway_pos)
                    self.time_wait()
                    tapped = True
                
                elif name == "railway":
                    self.tap_screen(*railway_pos)
                    self.time_wait()
                    tapped = True
                
                elif name == "classroom":
                    self.tap_screen(*classroom_pos)
                    self.time_wait()
                    tapped = True
                
                else:
                    logger.error("Invalid bounty location name.")
                    return ContinueResult.STOP

            elif not tapped:
                logger.info("Not in bounty screen, attempting to enter.")
                self.enter_bounty()

            else:
                logger.info("Wait loading...")
            
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_scrimmage_location(self, name="Trinity", timeout=25):
        logger.info(f"Attempting to enter scrimmage: {name}.")  
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()

            if self.detector.is_in_scrimmage_name(name):
                logger.info(f"Successfully entered {name}")
                return ContinueResult.SUCCESS

            if self.detector.is_in_scrimmage_screen():
                logger.info(f"In scrimmage screen, attempting to enter scrimmage: {name}.")

                if name == "Trinity":
                    self.tap_screen(*Trinity_pos)
                    self.time_wait()
                    tapped = True
                
                elif name == "Gehenna":
                    self.tap_screen(*Gehenna_pos)
                    self.time_wait()
                    tapped = True
                
                elif name == "Millennium":
                    self.tap_screen(*Millennium_pos)
                    self.time_wait()
                    tapped = True
                
                else:
                    logger.error("Invaild location name")
                    return ContinueResult.STOP   
                         
            elif not tapped:
                logger.info("Not in scrimmage screen, attempting to enter")
                self.enter_scrimmage()

            else:
                logger.info("Wait loading...")

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def enter_sweep_page(self, stage=10, timeout=10):
        logger.info(f"Attempting to enter stage: {stage} sweep page.")
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            # self.wait_loading()

            if self.detector.is_in_sweep_page():
                logger.info("Successfully enter sweep page.")
                return ContinueResult.SUCCESS
        
            present_stages = self.detector.get_present_stages()
            
            if present_stages == None:
                logger.info("Fail to get stages.")
                return ContinueResult.RETRY

            try:
                idx = present_stages.index(stage)

            except ValueError:
                logger.info("Target not in present screen, attempting to redirect to correct screen.")
                start = (1000, 200)
                end = (1000, 700)

                if present_stages[0] < stage:
                    self.swipe_screen(end, start, 400)
                    continue

                self.swipe_screen(start, end, 400)
                continue

            loc = self.detector.get_stage_entrance_locs(idx)

            if loc == None:
                logger.warning("Fail to get entrance location.")
                return ContinueResult.STOP

            self.tap_screen(*loc)

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def execute_sweep_with_ticket(self, ticket, runs, timeout=30):
        logger.info(f"Attempting to sweep: {runs} runs with ticket: {ticket}.")
        actual_runs = runs

        if ticket < runs:
            logger.warning("Insufficient tickets, sweeping as much as possible.")
            self.tap_screen(*sweep_max_pos)
            actual_runs = ticket

        if ticket == runs:
            self.tap_screen(*sweep_max_pos)
        
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            # self.time_wait()
            times = self.detector.get_sweep_times(False)

            if times == None:
                logger.warning("Fail to get sweep times.")
                return ContinueResult.RETRY

            if times < actual_runs:
                for i in range(actual_runs - times):
                    self.tap_screen(*sweep_add_pos, 0.2)
                continue

            if times > actual_runs:
                for i in range(times - actual_runs):
                    self.tap_screen(*sweep_sub_pos, 0.2)
                continue

            logger.info("Attempting to sweep.")
            self.tap_screen(*sweep_start_pos, 0.2)
            self.update_screenshot(0.5)
            confirm_pos = self.detector.find_confirm_button()

            if confirm_pos != None:
                self.tap_screen(*confirm_pos)
                return ContinueResult.SUCCESS

            logger.warning("Confirm buttom not found.")
            return ContinueResult.RETRY
        
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def execute_sweep_with_energy(self, energy, runs, cost, timeout=30):
        logger.info(f"Attempting to sweep: {runs} runs with energy: {energy}.")
        actual_runs = runs

        if energy < cost:
            logger.error("Insufficient energy.")
            self.adb_client.keyevent(4)
            return ContinueResult.STOP

        if energy < runs*cost:
            logger.warning("Insufficient energy, sweeping as much as possible.")
            self.tap_screen(*sweep_max_pos)
            actual_runs = int(energy / cost)

        start_time = time.time()

        for i in range(actual_runs - 1):
            self.tap_screen(*sweep_add_pos, 0.2)

        while time.time() - start_time < timeout:

            self.handle_popups_and_updatescreen()
            # self.time_wait()
            times = self.detector.get_sweep_times(True)

            if times < actual_runs:
                for i in range(actual_runs - times):
                    self.tap_screen(*sweep_add_pos, 0.2)
                continue
        
            if times > actual_runs:
                for i in range(times - actual_runs):
                    self.tap_screen(*sweep_sub_pos, 0.2)
                continue
        
            logger.info("Attempting to sweep")
            self.tap_screen(*sweep_start_pos, 0.2)
            self.update_screenshot(0.5)
            confirm_pos = self.detector.find_confirm_button()

            if confirm_pos != None:
                self.tap_screen(*confirm_pos)
                return ContinueResult.SUCCESS

            logger.warning("Confirm buttom not found.")
            return ContinueResult.RETRY
        
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def max_actual_run(self, ticket, energy, energy_cost, expect_runs):
        times_with_energy = int(energy / energy_cost)

        return min(times_with_energy, ticket, expect_runs)

    def sweep_missions(self, mode="hard", stage=293, runs=3):
        logger.info(f"Attempting to sweep missions: {stage} mode: {mode} runs: {runs}.")
        self.handle_popups_and_updatescreen()
        # self.time_wait()
    
        if mode == "hard":
            remaining_sweeps = self.detector.get_hard_quest_remaining_sweeps()
            
            if runs > remaining_sweeps:
                logger.warning("Insufficient remaining sweeps, sweeping as much as possible.")
            
            actual_runs = min(remaining_sweeps, runs)
            
            if actual_runs == 0:
                logger.error("Insufficient sweep times.")
                self.adb_client.keyevent(4)
                return ContinueResult.STOP
            
            return self.execute_sweep_with_energy(self.energy, actual_runs, 20)
        
        elif mode == "normal":
            return self.execute_sweep_with_energy(self.energy, runs, 10)
        
        else:
            logger.error("Invaild mode name.")
            return ContinueResult.STOP
    
    def sweep_scrimmage(self, name="Trinity", stage=4, runs=6, energy_cost=15):
        logger.info(f"Attempting to sweep scrimmage: {name} stage: {stage} runs: {runs}.")
        self.handle_popups_and_updatescreen()
        # self.wait_loading()

        actual_runs = self.max_actual_run(self.scrimmage_ticket, self.energy, energy_cost, runs)
        if actual_runs < runs and actual_runs > 0:
            logger.warning(f"Expect {runs} runs, actual {actual_runs} runs.")
        
        if actual_runs == 0:
            logger.error("Insufficient tickets or energy.")
            self.adb_client.keyevent(4)
            return ContinueResult.STOP

        return self.execute_sweep_with_ticket(self.scrimmage_ticket, actual_runs)

    def claim_cafe_energy(self, timeout=15):
        logger.info("Claiming cafe energy.")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen(off_notice=True)
            # self.wait_loading()
            
            if self.detector.is_in_cafe_rewards_screen():
                tapped = True
                if self.detector.is_cafe_claim_button_active():
                    logger.info("Claiming rewards...")
                    self.tap_screen(*cafe_claim_pos)
                    continue
            
                logger.info("Rewards claimed.")
                self.adb_client.keyevent(4)
                # self.adb_client.keyevent(4)
                return ContinueResult.SUCCESS

            elif self.detector.is_touch_to_continue():
                logger.info("touching...")
                self.tap_screen(*empty_pos)
                continue

            elif not tapped:
                self.tap_screen(*cafe_rewards_pos)
                continue
            
            else:
                logger.info("Wait loading...")
                self.tap_screen(*empty_pos)

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def claim_group_rewards(self, timeout=10):
        logger.info("Claiming group check in rewards.")
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            self.wait_loading()
            
            pos = self.detector.find_confirm_button()
            
            if not pos:
                logger.info("Rewards claimed.")
                self.adb_client.keyevent(4)
                return ContinueResult.SUCCESS
            
            logger.info("Claiming rewards...")
            self.tap_screen(*pos)
            self.time_wait()

        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def claim_mailbox_rewards(self, timeout=10):
        logger.info("Claiming mailbox rewards.")
        turn = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            self.wait_loading()
            
            if self.detector.is_touch_to_continue():
                logger.info(f"Touching...")
                self.tap_screen(*empty_pos)
                turn = False
                continue
            
            if self.detector.is_mail_claim_button_active():
                logger.info(f"Claiming mails...")
                self.tap_screen(*claim_all_pos)
                turn = True
                continue

            if turn == False:
                logger.info("All mail claimed.")
                self.adb_client.keyevent(4)
                return ContinueResult.SUCCESS            
            
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    def claim_tasks(self, timeout=10):
        logger.info("Claiming tasks rewards.")
        start_time = time.time()
        turn = True


        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen()
            self.wait_loading()
            
            if self.detector.is_touch_to_continue():
                logger.info(f"Touching...")
                self.tap_screen(*empty_pos)
                turn = True
                continue
            
            if self.detector.is_tasks_claim_button_active():
                logger.info(f"Claiming tasks...")
                self.tap_screen(*claim_all_pos)
                turn = False
                continue

            if self.detector.is_diamond_claim_button_active():
                logger.info(f"Claiming diamonds...")
                self.tap_screen(*claim_diamond_pos)
                turn = False
                continue

            if turn == True:
                logger.info("All mail claimed.")
                self.adb_client.keyevent(4)
                return ContinueResult.SUCCESS            
            
        logger.info("Failed to complete action within timeout.")
        return ContinueResult.RETRY

    # def buy_items(self, slots:list, refresh=0, timeout=20):
    #     logger.info(f"buying items slot: {slots}.")
    #     cur_page = 0
    #     tapped = False
    #     turn = False
    #     start = (1150, 700)
    #     end = (1150, 200)
    #     start_time = time.time()

    #     while time.time() - start_time < timeout:
    #         if not tapped:
    #             for slot in slots:
    #                 page, loc = self.slot_to_page_and_loc(slot)

    #                 if page != cur_page:
    #                     for i in range(page - cur_page):
    #                         self.swipe_screen(start, end, 300)
    #                         cur_page += 1

    #                 self.tap_screen(*loc)
    #             tapped = True

    #         self.handle_popups_and_updatescreen(off_notice=True)
            
    #         if self.detector.is_buy_button_active():
    #             logger.info(f"buy button active, tapping...")
    #             self.tap_screen(*buy_button_pos)
    #             self.tap_screen(*buy_confirm_pos)
    #             turn = True
    #             continue
            
    #         if self.detector.is_touch_to_continue():
    #             logger.info(f"Touching...")
    #             self.tap_screen(*empty_pos)
    #             turn = False
    #             continue

    #         if refresh > 0:
    #             self.tap_screen(*buy_button_pos)
    #             self.tap_screen(*refresh_confirm_pos)
    #             self.time_wait(1)
    #             refresh -= 1
    #             tapped = False
    #             continue

    #         if turn == False and refresh == 0:
    #             logger.info("Ttems have been purchased.")
    #             return ContinueResult.SUCCESS

    def select_slots(self, slots:list, timeout=10): #无检查
        logger.info(f"Selecting slots {slots}.")
        # cur_page = 0
        start = (1150, 700)
        end = (1150, 200)
        start_time = time.time()

        while time.time() - start_time < timeout:
            for slot in slots:
                    page, loc = self.slot_to_page_and_loc(slot)

                    if page > self.cur_page:
                        for i in range(page - self.cur_page):
                            self.swipe_screen(start, end, 300)
                            self.cur_page += 1

                    elif page < self.cur_page:
                        for i in range(self.cur_page - page):
                            self.swipe_screen(end, start, 300)
                            self.cur_page -= 1

                    self.tap_screen(*loc)
            
            return FlowResult(ContinueResult.SUCCESS)
        
        logger.info("Failed to complete action within timeout.")
        return FlowResult(ContinueResult.RETRY)

    def buy_confirm(self, timeout=15):
        logger.info("Confirming...")
        tapped = False
        start_time = time.time()

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen(off_notice=True)

            if self.detector.is_touch_to_continue():
                self.tap_screen(*empty_pos)
                return FlowResult(ContinueResult.SUCCESS)
            
            elif tapped:
                logger.info("Wait loading...")

            if self.detector.is_buy_button_active() and not tapped:
                self.tap_screen(*buy_button_pos)
                self.tap_screen(*buy_confirm_pos)
                tapped = True
                continue

            elif not self.detector.is_buy_button_active() and not tapped:
                logger.error("Items sold out.")
                return FlowResult(ContinueResult.STOP, None)
        
        logger.info("Failed to complete action within timeout.")
        return FlowResult(ContinueResult.RETRY)

    def refresh_slot(self, timeout=10):
        start_time = time.time()
        tapped = False

        while time.time() - start_time < timeout:
            self.handle_popups_and_updatescreen(off_notice=True)
            
            if self.refresh == 0:
                return FlowResult(ContinueResult.SUCCESS)
            
            elif not tapped:
                logger.info("Attempting to refresh items.")
                self.tap_screen(*buy_button_pos)
                tapped = True
                continue

            if self.detector.is_declear_popup() and tapped:
                logger.info("Comfirming...")
                self.tap_screen(*refresh_confirm_pos)
                self.refresh -= 1
                return FlowResult(ContinueResult.GO_TO, "SELECT_SLOT")
                      
            else:
                logger.info("Unable to refresh.")
                return FlowResult(ContinueResult.STOP)
            
        logger.info("Failed to complete action within timeout.")
        return FlowResult(ContinueResult.RETRY)

    def slot_to_page_and_loc(self, slot:int):
        page = slot // 8
        idx = slot % 8        
        row = idx // 4
        col = idx % 4
        return page, (shop_slot_0_pops[0] + col * slot_dx, shop_slot_0_pops[1] + row * slot_dy)

    def execute(self):
        pass
    # def perform_action_with_retries(self, action_method, max_retries=10, interval=0.5):
    #     retry_count = 0
    #     result = ContinueResult.RETRY

    #     while result == ContinueResult.RETRY and retry_count < max_retries:
    #         result = action_method()
    #         if result == ContinueResult.SUCCESS:
    #             logger.info("Action completed successfully.")
    #             return ContinueResult.SUCCESS
    #         elif result == ContinueResult.RETRY:
    #             logger.info(f"attempt {retry_count + 1}/{max_retries}")
    #             retry_count += 1
    #             time.sleep(interval)
    #         else:
    #             logger.error("Action failed.")
    #             return ContinueResult.STOP

    #     logger.error("Exceeded maximum retries.")
    #     return ContinueResult.STOP
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
    action = Action()
    # action.back_to_home()
    # action.enter_tasks()
    # action.enter_mailbox()
    # action.enter_shop("credits")
    # action.enter_missions()
    # action.enter_bounty()
    # action.enter_commissions()
    # action.enter_scrimmage()
    # action.enter_bounty_location()
    # action.enter_scrimmage_location()

    # action.update_energy()
    # action.update_scrimmage_ticket_and_energy()
    # action.update_bounty_ticket()
    # action.enter_missions_area()
    # print(res)
    # start = (1150, 200)
    # end = (1150, 700)
    # action.swipe_screen(start, end, 300)
    # action.swipe_screen(end, start, 300)
    # action.buy_items([16, 17, 18, 19,
    #                   20, 21, 22, 23])
    # action.buy_items([6, 7], 1)
    timeout = 10
    # start_time = time.time()

    # while time.time() - start_time < timeout:
    #     print("test")