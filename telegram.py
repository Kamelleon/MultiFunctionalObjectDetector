import telepot
import datetime
import os
import traceback
import threading
import logging
import time
import yaml
from yaml.loader import SafeLoader


class TelegramBot:
    logging.basicConfig(filename='detector_logger.txt',
                        filemode='a',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    def __init__(self):
        with open("config.yaml", "r") as config_file:
            try:
                self.config_file = yaml.load(config_file, Loader=SafeLoader)
            except yaml.YAMLError:
                logging.error("Error occured during loading config file.")

        self.bot_token = self.config_file["telegram_bot"]["token"]
        self.group_id = self.config_file["telegram_bot"]["group_id"]

        self.image_messages_queue = {}
        self.messages_queue = {}

        self.message_timeout = 4

        image_sender_thread = threading.Thread(target=self.send_message_with_image_queue)
        image_sender_thread.start()

        message_sender_thread = threading.Thread(target=self.send_message_queue)
        message_sender_thread.start()

        print("[~] Connecting to a Telegram bot...")
        try:
            self.bot = telepot.Bot(self.bot_token)
            print("[+] Connected to the Telegram bot")
            logging.info("Connected to the Telegram bot")
        except:
            print("[-] Could not connect to the Telegram bot")
            logging.error("Error occured during connecting to the Telegram bot:")
            logging.error(f"{traceback.format_exc()}")
            os._exit(1)

    def add_message_to_queue(self, camera_name, message):
        self.messages_queue[camera_name] = message

    def add_message_with_image_to_queue(self, image_location, description):
        self.image_messages_queue[image_location] = description

    def send_message_with_image_queue(self):
        while True:
            try:
                time.sleep(self.message_timeout)
                last_item_of_dict = list(self.image_messages_queue)[-1]
                self.bot.sendPhoto(self.group_id, open(last_item_of_dict, "rb"), caption=self.image_messages_queue[last_item_of_dict])
                # self.image_messages_queue.pop(last_item_of_dict,None)
                self.image_messages_queue = {}
            except IndexError:
                continue
            except:
                print(traceback.print_exc())
                time.sleep(1)
                logging.error("Error during sending an image to the Telegram bot")
                logging.error(traceback.format_exc())
                continue

    def send_message_queue(self):
        while True:
            try:
                time.sleep(self.message_timeout)
                last_item_of_dict = list(self.messages_queue)[-1]
                self.bot.sendMessage(self.group_id, self.messages_queue[last_item_of_dict])
                self.messages_queue.pop(last_item_of_dict, None)
            except IndexError:
                continue
            except:
                print(traceback.print_exc())
                logging.error("Error during sending an image to the Telegram bot")
                logging.error(traceback.format_exc())
                time.sleep(1)
                continue