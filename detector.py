import os
os.environ["PYTHONUTF8"] = "1"

import logger_config
from PIL import Image
from adb_client import ADBClient
import cv2
import re
import numpy as np
import pytesseract

logger = logger_config.setup_logging("detector")

#1600*900
energy_box_home = (610, 30, 720, 65)
energy_box_not_home = (660, 17, 780, 50)
bounty_ticket_box = (210, 110, 270, 150)
scrimmage_ticket_box = (210, 110, 270, 150)

bounty_stage_box = (880, 200, 930, 820)
hard_quest_box = (1200, 180, 1220, 200)

stage_box = (860, 200, 940, 810)
entrance_box = (1320, 200, 1470, 840)

sweep_times_box = (1140, 360, 1200, 390)
mission_sweep_times_box = (1140, 400, 1200, 430)
claim_all_tasks_box = (1303, 798, 1573, 877)
claim_all_mail_box = (1283, 798, 1553, 877)
claim_diamond_box = (1160, 800, 1270, 875)
task_popup_box = (410, 20, 530, 100)
shop_slot_box = (765, 145, 1535, 766)
buy_button_box = (1385, 795, 1525, 855)
cafe_claim_box = (660, 620, 940, 700)

remaining_sweeps_box = (1340, 635, 1385, 660)


tesseract_path = r"C:\apps\tesseract\tesseract.exe"

class Detector:
    def __init__(self):
        # self.adb_client = ADBClient()
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.screenshot_path = os.path.join("screenshot", "cur.png")

    def match_template(self, image_path, template_path, threshold=0.8, showheatmap=False) -> tuple:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        # edges = cv2.Canny(image, 80, 160)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        
        if showheatmap:
            print(res.max())
            res_norm = cv2.normalize(res, None, 0, 255, cv2.NORM_MINMAX)
            res_norm = res_norm.astype(np.uint8)
            heatmap = cv2.applyColorMap(res_norm, cv2.COLORMAP_JET)
            heatmap = cv2.resize(heatmap, (1600, 900))
            cv2.imshow("match heatmap", heatmap)
            cv2.waitKey(0)

        loc = cv2.minMaxLoc(res)

        if loc[1] >= threshold:
            h, w = template.shape[:2]
            center_x = loc[3][0] + w // 2
            center_y = loc[3][1] + h // 2
            return (center_x, center_y)
        
        return None
    
    def match_template_list(self, roi, template_path, threshold=0.85) -> list:
        gray = cv2.imread(self.screenshot_path, cv2.IMREAD_GRAYSCALE)
        x1, y1, x2, y2 = roi
        crop = gray[int(y1):int(y2), int(x1):int(x2)]
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        res = cv2.matchTemplate(crop, template, cv2.TM_CCOEFF_NORMED)
        
        ys, xs = np.where(res >= threshold)
        points = list(zip(xs, ys))
        filtered = []

        for pt in points:

            if all(abs(pt[0]-fx) > 50 or abs(pt[1]-fy) > 50 for fx,fy in filtered):
                filtered.append(pt)

        return filtered

    def crop_image(self, image_path, crop_box, save_path):
        image = Image.open(image_path)
        cropped_image = image.crop(crop_box)
        cropped_image.save(save_path)

    def get_number_from_image(self, roi, mode=7, invert=False) -> str:
        gray = cv2.imread(self.screenshot_path, cv2.IMREAD_GRAYSCALE)
        x1, y1, x2, y2 = roi
        crop = gray[int(y1):int(y2), int(x1):int(x2)]
        _, bin_img = cv2.threshold(crop, 180, 255, cv2.THRESH_BINARY)
        if invert:
            bin_img = cv2.bitwise_not(bin_img)
        # bin_img = cv2.resize(bin_img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        bin_img = cv2.resize(bin_img, None, fx=2, fy=2)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,1))
        bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, kernel)
        # bin_img = cv2.dilate(bin_img, kernel)
        # cv2.imshow('mo', bin_img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        config = f"--psm {mode} -c tessedit_char_whitelist=0123456789/"

        result = pytesseract.image_to_string(bin_img, config=config)
        
        if result and result.strip():
            match = re.sub(r"[ \n]", " ", result.strip())
            logger.info(f"OCR result: {match}")
            return match
        
        return None

    def get_letter_from_image(self, image_path):
        gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        _, bin_img = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2,1))
        bin_img = cv2.dilate(bin_img, kernel, 1)

        config = "--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMN"

        result = pytesseract.image_to_string(bin_img, config=config)
        if result and result.strip():
            logger.info(f"OCR result for {image_path}: {result.strip()}")
            match = re.sub(r"[ \n]", "", result.strip())
            if match:
                return match
            return result.strip()
        return None

    def is_loading(self) -> bool:
        template_path = os.path.join("icons", "loading_icon.png")
        result_1 = self.match_template(self.screenshot_path, template_path)
        result_2 = self.is_screen_dimmed()
        return result_1 or result_2

    def is_update_popup(self):
        pass
    
    def is_login_event_popup(self):
        template_path = os.path.join("icons", "dont_display_tick2.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_everyday_login_popup(self) -> tuple:
        template_path = os.path.join("icons", "everyday_login.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_login_from_store_popup(self) -> tuple:
        template_path = os.path.join("icons", "dont_display_tick.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result
    
    def is_other_popup(self) -> tuple:
        template_path = os.path.join("icons", "page_close_icon.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result
    
    def is_reconnect_popup(self) -> tuple:
        template_path = os.path.join("icons", "reconnect_icon.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_notice_popup(self) -> tuple:
        template_path = os.path.join("icons", "notice.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_declear_popup(self) -> tuple:
        template_path = os.path.join("icons", "declear.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_task_popup(self) -> tuple:
        template_path = os.path.join("icons", "task_popup.png")
        result = self.match_template(self.screenshot_path, template_path, 0.9)
        return result

    def is_in_login_screen(self, threshold=0.75) -> tuple:
        template_path = os.path.join("icons", "menu_icon.png")
        result = self.match_template(self.screenshot_path, template_path, threshold)
        return result

    def is_in_home_screen(self, showheatmap=False) -> tuple:
        template_path = os.path.join("icons", "campaign_icon.png")
        result = self.match_template(self.screenshot_path, template_path, showheatmap=showheatmap)
        return result

    def is_in_mailbox_screen(self) -> tuple:
        template_path = os.path.join("icons", "mailbox.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_cafe_screen(self) -> tuple: #unfinish
        template_path = os.path.join("icons", "cafe.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_group_screen(self) -> bool:
        template_1_path = os.path.join("icons", "group_check_in.png")
        template_2_path = os.path.join("icons", "group_ID.png")
        res_1 = self.match_template(self.screenshot_path, template_1_path)
        res_2 = self.match_template(self.screenshot_path, template_2_path)

        return res_1 or res_2

    def is_in_task_screen(self) -> tuple:
        template_path = os.path.join("icons", "task.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_shop_screen(self) -> tuple:
        template_path = os.path.join("icons", "shop.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_shop_credits(self) -> tuple:
        template_path = os.path.join("icons", "credits.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result
    
    def is_in_shop_tactical_coin(self) -> tuple:
        template_path = os.path.join("icons", "tactical_coin.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_campaign_screen(self) -> tuple:
        template_path = os.path.join("icons", "story.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result
    
    def is_in_missions_page(self, mode:str) -> tuple:
        if mode == "hard":
            template_path = os.path.join("icons", "normal_quest.png")

        elif mode == "normal":
            template_path = os.path.join("icons", "hard_quest.png")

        else:
            logger.error("Invalid mode name.")
            return None
        
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_bounty_screen(self) -> tuple:
        template_path = os.path.join("icons", "location_select.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result
    
    def is_in_commissions_screen(self) -> tuple:
        template_path = os.path.join("icons", "request_select.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result
    
    def is_in_scrimmage_screen(self) -> tuple:
        template_path = os.path.join("icons", "academy_select.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_bounty_name(self, name) -> tuple:
        template_path = os.path.join("icons", f"bounty_{name}.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_scrimmage_name(self, name) -> tuple:
        template_path = os.path.join("icons", f"scrimmage_{name}.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_cafe_rewards_screen(self) -> tuple:
        template_path = os.path.join("icons", "cafe_rewards.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_cafe_claim_button_active(self) -> bool:
        template_path = os.path.join("screenshot", "cur.png")
        img = cv2.imread(template_path)
        x1, y1, x2, y2 = cafe_claim_box
        crop = img[int(y1):int(y2), int(x1):int(x2)]

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        lower = np.array([18, 90, 120])
        upper = np.array([35, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)

        yellow_ratio = mask.mean() / 255  # 0~1

        if yellow_ratio > 0.5:
            return True

        else:
            return False

    def is_tasks_claim_button_active(self) -> bool:
        template_path = os.path.join("screenshot", "cur.png")
        img = cv2.imread(template_path)
        x1, y1, x2, y2 = claim_all_tasks_box
        crop = img[int(y1):int(y2), int(x1):int(x2)]

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        lower = np.array([18, 90, 120])
        upper = np.array([35, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)

        yellow_ratio = mask.mean() / 255  # 0~1

        if yellow_ratio > 0.5:
            return True

        else:
            return False

    def is_diamond_claim_button_active(self) -> bool:
        template_path = os.path.join("screenshot", "cur.png")
        img = cv2.imread(template_path)
        x1, y1, x2, y2 = claim_diamond_box
        crop = img[int(y1):int(y2), int(x1):int(x2)]

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        lower = np.array([18, 90, 120])
        upper = np.array([35, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)

        yellow_ratio = mask.mean() / 255  # 0~1

        if yellow_ratio > 0.5:
            return True

        else:
            return False

    def is_mail_claim_button_active(self) -> bool:
        template_path = os.path.join("screenshot", "cur.png")
        img = cv2.imread(template_path)
        x1, y1, x2, y2 = claim_all_mail_box
        crop = img[int(y1):int(y2), int(x1):int(x2)]

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        lower = np.array([18, 90, 120])
        upper = np.array([35, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)

        yellow_ratio = mask.mean() / 255  # 0~1

        if yellow_ratio > 0.5:
            return True

        else:
            return False
  
    def is_buy_button_active(self) -> bool:
        template_path = os.path.join("screenshot", "cur.png")
        img = cv2.imread(template_path)
        x1, y1, x2, y2 = buy_button_box
        crop = img[int(y1):int(y2), int(x1):int(x2)]

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        lower = np.array([18, 90, 120])
        upper = np.array([35, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)

        yellow_ratio = mask.mean() / 255  # 0~1

        if yellow_ratio > 0.5:
            return True

        else:
            return False

    def is_screen_dimmed(self, baseline_mean=80) -> bool:
        img = cv2.imread(self.screenshot_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cur_mean = gray.mean()
        
        if cur_mean < baseline_mean:
            return True

        else:
            return False

    def is_in_sweep_page(self) -> tuple:
        template_path = os.path.join("icons", "sweep.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def is_in_sweep_settlement_page(self) -> tuple:
        template_1_path = os.path.join("icons", "sweep_success.png")
        # template_2_path = os.path.join("icons", "sweep_success_2.png")
        result_1 = self.match_template(self.screenshot_path, template_1_path)
        # result_2 = self.match_template(self.screenshot_path, template_2_path)
        # return result_1[0] or result_2[0]
        return result_1

    def is_touch_to_continue(self) -> tuple:
        template_path = os.path.join("icons", "touch_to_continue.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def find_BA_icon(self) -> tuple:
        template_path = os.path.join("icons", "BA_icon.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def find_close_button(self) -> tuple:
        template_path = os.path.join("icons", "close_button.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def find_confirm_button(self) -> tuple:
        template_path = os.path.join("icons", "confirm_button.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def find_home_button(self) -> tuple:
        template_path = os.path.join("icons", "home_button.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    def find_back_button(self) -> tuple:
        template_path = os.path.join("icons", "back_button.png")
        result = self.match_template(self.screenshot_path, template_path)
        return result

    # def find_claim_all_button(self) -> tuple:
    #     template_path = os.path.join("icons", "claim_all_tasks.png")
    #     result = self.match_template(self.screenshot_path, template_path)
    #     return result

    # def find_claim_mail_button(self) -> tuple:
    #     template_path = os.path.join("icons", "claim_all_mail.png")
    #     result = self.match_template(self.screenshot_path, template_path)
    #     return result

    def get_energy(self, home=True) -> int:
        if home:
            res = self.get_number_from_image(energy_box_home, invert=True)
        
        else:
            res = self.get_number_from_image(energy_box_not_home, invert=True)

        if not res:
            return None

        match = re.search(r'\d+', res)

        if not match:
            return None
                
        number = int(match.group())

        if number > 999 or number < 0:
            return None
        
        return number

    def get_hard_quest_remaining_sweeps(self) -> int:
        res = self.get_number_from_image(remaining_sweeps_box)

        if not res:
            return None
        
        match = re.search(r'\d+', res)

        if not match:
            return None
                
        number = int(match.group())
        return number

    def get_bounty_ticket(self) -> int:
        res = self.get_number_from_image(bounty_ticket_box)
       
        if not res:
            return None

        match = re.search(r'\d+', res)

        if not match:
            return None
                
        number = int(match.group())

        if number > 15 or number < 0:
            return None
        
        return number

    def get_scrimmage_ticket(self) -> int:
        res = self.get_number_from_image(scrimmage_ticket_box)

        if not res:
            return None

        match = re.search(r'\d+', res)

        if not match:
            return None
                
        number = int(match.group())

        if number > 15 or number < 0:
            return None
        
        return number

    def get_present_stages(self) -> list:
        res_raw = self.get_number_from_image(stage_box, mode=6)
        
        if res_raw == None:
            logger.error("Fail to get stages.")
            return res_raw

        res_list = list(map(int, res_raw.split()))
        return res_list

    def get_stage_entrance_locs(self, index:int) -> tuple:
        template_path = os.path.join("icons", "entrance.png")
        buttons = self.match_template_list(entrance_box, template_path)
        
        if len(buttons) < index:
            return None
        
        return (buttons[index][0] + entrance_box[0] + 30 , buttons[index][1] + entrance_box[1] + 30)

    def get_sweep_times(self, mission=True) -> int:
        if mission:
            times = self.get_number_from_image(mission_sweep_times_box)
        else:    
            times = self.get_number_from_image(sweep_times_box)

        if times == None:
            return times

        return int(times)

if __name__ == "__main__":
    # adb_client = ADBClient()
    # success = adb_client.adb_connect()
    # if success.returncode != 0:
        # logger.error(f"ADB connect error: {success.stderr.strip()}")
    # success = adb_client.get_current_screenshot("cur")
    detector = Detector()
    success = detector.is_in_home_screen(showheatmap=True)
    if success:
        logger.info("Success.")
    else:
        logger.error("Action failed.")

    detector = Detector()

    # res = detector.match_template_list(shop_slot_box, "icons/buy.png")
    # print(res)