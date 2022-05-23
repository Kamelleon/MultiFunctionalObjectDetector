print("[~] Initializing Python modules...")

import datetime
from PIL import Image
import yaml
from yaml.loader import SafeLoader
import os
import time
import traceback
import torch
import cv2
from pathlib import Path
import warnings
from sys import platform
import pymysql
import GPUtil
import logging
import threading
from telegram import TelegramBot
from database import DatabaseSender
from supla import Supla

print("[+] Modules initialized")


# warnings.filterwarnings("ignore")


class ClassSelector:
    CLASS_NAMES = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
                   'traffic light',
                   'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
                   'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase',
                   'frisbee',
                   'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard',
                   'surfboard',
                   'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
                   'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
                   'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard',
                   'cell phone',
                   'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
                   'teddy bear',
                   'hair drier', 'toothbrush']

    @staticmethod
    def choose(selected_class_names_list=None, select_all_classes=False):
        names = []
        if not select_all_classes or selected_class_names_list is not None:
            for list_object in selected_class_names_list:
                index_of_object = ClassSelector.CLASS_NAMES.index(list_object)
                names.append(index_of_object)
        else:
            for list_object in ClassSelector.CLASS_NAMES:
                index_of_object = ClassSelector.CLASS_NAMES.index(list_object)
                names.append(index_of_object)
        return names


class YoloDetectionModel:
    def __init__(self, classes_for_detection, model_type="yolov5l", minimum_probability_for_detection=0.6,
                 skip_outdated_pictures=True, telegram_bot=None, supla=None):
        if torch.cuda.is_available():
            self.device_used_for_detections = "cuda:0"
        else:
            self.device_used_for_detections = "cpu"

        self.yolo_repository = 'ultralytics/yolov5'
        self.yolo_model_type = model_type
        self._classes_for_detection = classes_for_detection
        self.yolo_classes = ClassSelector.choose(self._classes_for_detection)
        self.minimum_probability_for_detection = minimum_probability_for_detection
        self.minimum_number_of_objects_to_consider_as_detection = 1
        self.model = None
        self.skip_outdated_pictures = skip_outdated_pictures
        self.image_manager = ImageManager()

        if telegram_bot is not None:
            self.telegram_bot = telegram_bot
        else:
            self.telegram_bot = None

        if supla is not None:
            self.supla = supla
        else:
            self.supla = None

        self.load()

    def load(self):
        print(f"""
        [i] Trying to load pretrained YOLO model with selected settings:
        -------------------------------------------------
        Device used for detections: {self.device_used_for_detections}
        YOLO repository: {self.yolo_repository}
        YOLO model type: {self.yolo_model_type}
        YOLO repository location: GitHub (remote download)
        Selected classes: {self._classes_for_detection}
        Minimum probability for detection: {self.minimum_probability_for_detection}
        -------------------------------------------------
        """)

        print("[~] Loading model...")
        self.model = torch.hub.load(self.yolo_repository, self.yolo_model_type, pretrained=True, source="github")
        self.images_blacklist = []
        self.model.classes = self.yolo_classes
        self.model.conf = self.minimum_probability_for_detection
        # self.model.iou = 0.45  # NMS IoU threshold
        # self.model.agnostic = False  # NMS class-agnostic
        # self.model.multi_label = False  # NMS multiple labels per box
        # self.model.max_det = 1000  # maximum number of detections per image
        print("[+] Model has been loaded")

    def perform_detection_on_images_from_current_folder(self):
        print("[~] Starting detection (it may take a while...)")
        while True:
            try:
                time.sleep(0.5)
                detection_start_time = time.time()
                for file in os.listdir(os.getcwd()):
                    file_is_image = file.endswith(".jpg") or file.endswith(".png")
                    if file_is_image:
                        image = file
                        image_name_without_extension = Path(image).stem
                        if self.skip_outdated_pictures:
                            last_time_of_modification_in_seconds = self.image_manager.get_modification_timedelta(image)
                            if last_time_of_modification_in_seconds > 10:
                                if not image_name_without_extension in self.images_blacklist:
                                    self.telegram_bot.add_message_to_queue(image_name_without_extension,f"Kamera {image_name_without_extension} nie odpowiada. ({time.strftime('%H:%M:%S')})")
                                    self.images_blacklist.append(image_name_without_extension)
                                else:
                                    continue
                            else:
                                if image_name_without_extension in self.images_blacklist:
                                    self.telegram_bot.add_message_to_queue(image_name_without_extension,f"Kamera {image_name_without_extension} znów działa. ({time.strftime('%H:%M:%S')})")
                                    self.images_blacklist.remove(image_name_without_extension)

                        try:
                            image = cv2.imread(image)
                            # cv2.imshow("obraz",image)
                            # cv2.waitKey(500)
                        except:
                            logging.error("Error occurred during loading image file")
                            logging.error(f"{traceback.format_exc()}")
                            continue
                        try:
                            results = self.model(image)  # Perform detection
                        except:
                            logging.error("Error occurred during performing detection")
                            logging.error(f"{traceback.format_exc()}")
                            continue

                        model_has_detected_something = len(
                            results.pandas().xyxy[0]) >= self.minimum_number_of_objects_to_consider_as_detection

                        if model_has_detected_something:
                            print(f"[!] Detected something on: {image_name_without_extension}")
                            logging.info(f"Detected something on: {image_name_without_extension}")
                            if self.supla is not None:
                                self.supla.activate_output()
                            rendered_image = self._render_results(results)
                            self.image_manager.create_new_folder_with_image_name(image_name_without_extension)
                            self.image_manager.save_rendered_image_to_folder(rendered_image)

                            if self.telegram_bot is not None:
                                self.telegram_bot.add_message_with_image_to_queue(self.image_manager.current_image_path,
                                                                     f"Wykryto człowieka na kamerze {image_name_without_extension} "
                                                                     f"o godzinie {time.strftime('%H:%M:%S')}.")

                print(f"[i] Detection performed in:", time.time() - detection_start_time, "seconds")
                logging.info("Detection successfully performed")

            except KeyboardInterrupt:
                print("Keyboard interrupt detected. Exiting...")
                os._exit(1)

    def _render_results(self, results):
        try:
            results.render()
            for img in results.imgs:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                rendered_image = Image.fromarray(img)
            return rendered_image
        except:
            logging.error("Could not render results")
            logging.error(f"{traceback.format_exc()}")


class ImageManager:
    def __init__(self):
        self.current_folder_name = ""
        self.current_image_path = ""

    def get_modification_timedelta(self, file):
        last_modified = str(datetime.datetime.fromtimestamp(os.path.getmtime(file)).time()).split(".")[0]
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        FMT = "%H:%M:%S"
        tdelta = datetime.datetime.strptime(str(current_time), FMT) - datetime.datetime.strptime(
            str(last_modified), FMT)
        return tdelta.total_seconds()

    def create_new_folder_with_image_name(self, image_name_without_extension):
        try:
            current_date = DateTimePicker.get_current_date()
            if not os.path.isdir(f"{current_date}"):
                os.mkdir(f"{current_date}")
            if not os.path.isdir(f"{current_date}/{image_name_without_extension}"):
                os.mkdir(f"{current_date}/{image_name_without_extension}")
            self.current_folder_name = image_name_without_extension
        except:
            logging.error("Could not create a folder with image name")
            logging.error(f"{traceback.format_exc()}")
            os._exit(1)

    def save_rendered_image_to_folder(self, rendered_image):
        try:
            current_date = DateTimePicker.get_current_date()
            current_time = DateTimePicker.get_current_time()
            rendered_image.save(f"{current_date}/{self.current_folder_name}/{current_time}.jpg", format="JPEG")
            self.current_image_path = f"{current_date}/{self.current_folder_name}/{current_time}.jpg"
        except:
            logging.error("Could not save an image to a folder")
            logging.error(f"{traceback.format_exc()}")
            os._exit(1)


class DateTimePicker:
    @staticmethod
    def get_current_date():
        return datetime.date.today().strftime("%d-%m-%Y")

    @staticmethod
    def get_current_time():
        return time.strftime('%H_%M_%S')


class PIDWriter:
    @staticmethod
    def write_current_script_pid_to_file():
        try:
            with open("detector_script_pid.txt", "w+") as f:
                f.write(str(os.getpid()))
        except:
            print("[-] Could not write a PID to a file")
            logging.error("Could not write a PID to a file")
            logging.error(f"{traceback.format_exc()}")
            os._exit(1)


if __name__ == "__main__":
    logging.basicConfig(filename='detector_logger.txt',
                        filemode='a',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    with open("config.yaml", "r") as config_file:
        try:
            config_file = yaml.load(config_file, Loader=SafeLoader)
        except yaml.YAMLError as exc:
            logging.critical("Could not open config file")

    supla = Supla()

    telegram_bot = TelegramBot()

    database_sender = DatabaseSender()
    db_thread = threading.Thread(target=database_sender.send_ping)
    db_thread.start()

    PIDWriter.write_current_script_pid_to_file()

    yolo_detection_model = YoloDetectionModel(["person"], minimum_probability_for_detection=float(
        config_file["detector"]["confidence"]),
                                              telegram_bot=telegram_bot, supla=supla)

    yolo_detection_model.perform_detection_on_images_from_current_folder()
