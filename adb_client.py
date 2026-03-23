import subprocess
import os
import logger_config
import re

logger = logger_config.setup_logging("adb_client")


class ADBClient:
    # def __init__(self, adb_path = "D:\\platform-tools\\adb.exe", device = "192.168.1.12:5555"):
    def __init__(self, adb_path = r"C:\apps\platform-tools\adb.exe", device = "192.168.1.54:5555"):
        self.adb_path = adb_path
        self.device = device
        self.remote_path = "/sdcard"
        self.local_path = r"C:\datas\script\screenshot"
        self.connected = self.adb_connect()
        # self.screen_width, self.screen_height = self.get_screen_size()
        # self.connected = True

    def adb_connect(self):
        command = [self.adb_path, "connect", self.device]
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )

        except subprocess.TimeoutExpired:
            logger.error(f"ADB connect timeout: {self.device}")
            return False

        output = (result.stdout or "") + (result.stderr or "")

        if "connected to" in output.lower():
            logger.info(f"Connected to device: {self.device}")
            return True

        else:
            logger.error(f"ADB connect failed: {output.strip()}")
            return False
    
    def adb_disconnect(self):
        command = [self.adb_path, "disconnect", self.device]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            self.connected = False
            logger.info(f"Disconnected from device: {self.device}")
        
        else:
            logger.error(f"Failed to disconnect from device: {self.device}")

        return result
    
    # def ensure_connected(self):
    #     if not self.connected:
    #         self.adb_connect()

    def ensure_connected(self):
        result = subprocess.run(
            [self.adb_path, "get-state"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.stdout.strip() != "device":
            self.connected = self.adb_connect()

            if not self.connected:
                raise RuntimeError("ADB device can not connected.")
    
    def run(self, args, text=True):
        self.ensure_connected()
        command = [self.adb_path, "-s", self.device] + args
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text)
        return result
    
    # def capture_screenshot(self, name):
    #     path = f"{self.local_path}{name}.png"
    #     result = self.run(["exec-out", "screencap", "-p", path])
    #     return result
    
    def get_current_screenshot(self, name="cur"):
        local_path = f"{self.local_path}/{name}.png"

        with open(local_path, "wb") as f:
            result = subprocess.run(
                [self.adb_path, "-s", self.device, "exec-out", "screencap", "-p"],
                stdout=f,
                stderr=subprocess.PIPE,
            )
            # result = self.run(["exec-out", "screencap", "-p", local_path], text=False)
        return result

    # def pull_screenshot(self, name):
    #     remote_path = os.path.join()
    #     local_path = os.path.join(self.local_path, f"{name}.png")
    #     result = self.run(["pull", remote_path, local_path])
    #     return result
    
    def tap_screen(self, x, y):
        result = self.run(["shell", "input", "tap", str(x), str(y)])
        return result
    
    def swipe_screen(self, x1, y1, x2, y2, duration_ms):
        result = self.run(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)])
        return result
    
    def keyevent(self, keycode):
        result = self.run(["shell", "input", "keyevent", str(keycode)])
        return result
    
    # def zoom_screen(self, scale):
        # command = [self.adb_path, "-s", self.device, "shell", "input", "pinch", str(scale)]
        # result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # return result
    
    # def get_current_screenshot(self, name):
    #     capture_result = self.capture_screenshot(name)
        
    #     if capture_result.returncode != 0:
    #         logger.error(f"Error capturing screenshot: {capture_result.stderr.strip()}")
    #         return False
        
    #     pull_result = self.pull_screenshot(name)
        
    #     if pull_result.returncode != 0:
    #         logger.error(f"Error pulling screenshot: {pull_result.stderr.strip()}")
    #         return False
        
    #     return True
    def get_screen_size(self):
        result = subprocess.check_output(
        [self.adb_path, "shell", "wm", "size"],
        encoding="utf-8"
        )

        match = re.search(r"Physical size:\s*(\d+)x(\d+)", result)
        if not match:
            raise RuntimeError(f"Unable to parse screen resolution: {result}")

        width, height = map(int, match.groups())
        return width, height
    
    def resize(self, target_x, target_y):
        result = self.run(["shell", "wm", "size", f"{target_x}x{target_y}"])
        return result
    
    def reset_screen_size(self):
        result = self.run(["shell", "wm", "size", "reset"])
        return result


if __name__ == "__main__":
    adb_client = ADBClient()
    # adb_client.adb_disconnect()
    # res = adb_client.ensure_connected()
    # event_location = (1560, 250, 1400, 250, 200)
    # if connect_result.returncode == 0:
        # logger.info(f"Connected to device: {adb_client.device}")

    #     success = adb_client.swipe_screen(*event_location)
    # logger.info("Starting action.")
    res = adb_client.get_current_screenshot("cur")
    # # res = adb_client.tap_screen(424, 1264)
    # if res.returncode == 0:
        # logger.info("Action executed successfully.")
    # print(adb_client.screen_width, adb_client.screen_height)
    # adb_client.resize(1600, 800)
    # res = adb_client.get_screen_size()
    # print(res)
    # adb_client.reset_screen_size()
    # else:
    #     logger.error(f"Failed to connect to device: {adb_client.device}")