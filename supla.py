import json
import logging
import os
import socket
import threading
import requests
import time
import yaml
from yaml.loader import SafeLoader

class Supla:

    status = "OFF"

    def __init__(self):
        with open("config.yaml", "r") as config_file:
            try:
                config_file = yaml.load(config_file, Loader=SafeLoader)
            except yaml.YAMLError as exc:
                print(exc)
        self.supla_status_url = config_file["supla"]["status_url"]
        self.supla_action_url = config_file["supla"]["action_url"]
        self.supla_headers = {
            'Authorization': 'Authorization_URL'
        }

    def capture_from_supla(self):
        logging.info("Started procedure of capturing signal from Supla")
        while True:
            time.sleep(0.3)
            print(f"Supla status: {Supla.status}")
            response_status = requests.request("GET", self.supla_status_url, headers=self.supla_headers, data={}).json()
            if response_status['state']["connected"] == True and response_status['state']["hi"] == True:
                Supla.status = "ON"
            else:
                Supla.status = "OFF"

    def activate_output(self):
        payload_action = {"action": "OPEN"}
        logging.info("Sending output activation signal...")
        response_action = requests.patch(self.supla_action_url, data=json.dumps(payload_action), headers=self.supla_headers)
        return response_action


class DetectorScript:
    def __init__(self):
        self.script_running = False

    def killer(self):
        logging.info("Killer method started")
        while True:
            if Supla.status == "OFF" and self.script_running == True:
                with open("detector_script_pid.txt", "r") as f:
                    detector_pid = f.readline()
                    detector_pid = str(detector_pid)
                print("Killing detector...")
                os.system(f"sudo kill -9 {detector_pid}")
                self.script_running = False

    def invoker(self):
        logging.info("Invoker method started")
        while True:
            if Supla.status == "ON" and self.script_running == False:
                print("Invoking detector...")
                self.script_running = True
                os.system("sudo -E python3 detector.py")


if __name__ == "__main__":
    logging.basicConfig(filename='detector_logger.txt',
                        filemode='a',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    if os.geteuid() != 0:
        logging.critical(f"You need to have root privileges to run this script.\nPlease try again, this time using 'sudo -E python3 {__file__}'. Exiting.")
        exit(
            f"You need to have root privileges to run this script.\nPlease try again, this time using 'sudo -E python3 {__file__}'. Exiting.")

    supla = Supla()
    detector_script = DetectorScript()

    supla_signal_capturing = threading.Thread(target=supla.capture_from_supla)
    detector_invoker = threading.Thread(target=detector_script.invoker)
    detector_killer = threading.Thread(target=detector_script.killer)

    supla_signal_capturing.start()
    detector_invoker.start()
    detector_killer.start()
