print("[~] Initializing Python modules...")

import datetime
from PIL import Image
import os
import time
import traceback
import torch
import cv2
from pathlib import Path
import warnings
from sys import platform
import telepot
import pymysql
import GPUtil

print("[+] Modules initialized")

warnings.filterwarnings("ignore")


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


class TelegramBot:
    def __init__(self, bot_token, group_id):
        self.bot_token = bot_token
        self.group_id = group_id

        print("[~] Connecting to a Telegram bot...")
        self.bot = telepot.Bot(self.bot_token)
        print("[+] Connected to the Telegram bot")


    def send_image_with_description(self, image_location, description):
        self.bot.sendPhoto(self.group_id, open(image_location, "rb"), caption=description)


class YoloDetectionModel:
    def __init__(self, classes_for_detection, model_type="yolov5l", minimum_probability_for_detection=0.6, database_sender=None, telegram_bot=None):
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
        self.image_manager = ImageManager()

        if telegram_bot is not None:
            self.telegram_bot = telegram_bot
        else:
            self.telegram_bot = None

        if database_sender is not None:
            self.database_sender = database_sender
        else:
            self.database_sender = None

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
   
        self.model.classes = self.yolo_classes
        self.model.conf = self.minimum_probability_for_detection
        # self.model.iou = 0.45  # NMS IoU threshold
        # self.model.agnostic = False  # NMS class-agnostic
        # self.model.multi_label = False  # NMS multiple labels per box
        # self.model.max_det = 1000  # maximum number of detections per image
        print("[+] Model loaded")
    



    def perform_detection_on_images_from_current_folder(self):
        print("[~] Starting detection (it may take a while...)")
        while True:
            GPUtil.getGPUs()[0].load
            print(GPUtil.getGPUs()[0].memoryUsed)
            detection_start_time = time.time()
            for file in os.listdir(os.getcwd()):
                if file.endswith(".jpg") or file.endswith(".png"):
                    image = file
                    try:
                        image_name_without_extension = Path(image).stem
                        image = cv2.imread(image)
                        results = self.model(image)  # Perform detection
                        model_has_detected_something = len(results.pandas().xyxy[0]) >= self.minimum_number_of_objects_to_consider_as_detection

                        if model_has_detected_something:
                            print(f"[!] Detected something on: {image_name_without_extension}")
                            rendered_image = self._render_results(results)
                            self.image_manager.create_new_folder_with_image_name(image_name_without_extension)
                            self.image_manager.save_rendered_image_to_folder(rendered_image)

                            if self.telegram_bot is not None:
                                self.telegram_bot.send_image_with_description(self.image_manager.current_image_path,
                                                                              f"Wykryto człowieka na kamerze {image_name_without_extension} "
                                                                              f"o godzinie {time.strftime('%H:%M:%S')}.")
                    except KeyboardInterrupt:
                        os._exit(1)
                    except Exception:
                        print(traceback.print_exc())
                        time.sleep(4)

            print(f"[i] Detection performed in:", time.time() - detection_start_time, "seconds")
            try:
                if self.database_sender is not None:
                    self.database_sender.send_ping(1)
            except:
                continue

    def _render_results(self, results):
        results.render()
        for img in results.imgs:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            rendered_image = Image.fromarray(img)
        return rendered_image


class ImageManager:
    def __init__(self):
        self.current_folder_name = ""
        self.current_image_path = ""

    def create_new_folder_with_image_name(self, image_name_without_extension):
        if not os.path.isdir(f"{DateTimePicker.get_current_date()}"):
            os.mkdir(f"{DateTimePicker.get_current_date()}")
        if not os.path.isdir(f"{DateTimePicker.get_current_date()}/{image_name_without_extension}"):
            os.mkdir(f"{DateTimePicker.get_current_date()}/{image_name_without_extension}")
        self.current_folder_name = image_name_without_extension

    def save_rendered_image_to_folder(self, rendered_image):
        rendered_image.save(f"{DateTimePicker.get_current_date()}/{self.current_folder_name}/{DateTimePicker.get_current_time()}.jpg", format="JPEG")
        self.current_image_path = f"{DateTimePicker.get_current_date()}/{self.current_folder_name}/{DateTimePicker.get_current_time()}.jpg"


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
        with open("detector_script_pid.txt", "w+") as f:
            f.write(str(os.getpid()))


class DatabaseSender:
    def __init__(self,host,user,password,database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
    
    def send_ping(self, id):
        con=pymysql.connect(host=self.host,user=self.user,password=self.password,database=self.database,cursorclass=pymysql.cursors.DictCursor)
        cur = con.cursor()
        query = "update activity set ts=now(), status = 1 where id = {}".format(id)
        cur.execute(query)
        con.commit()
        con.close()

if __name__ == "__main__":

    database_sender = DatabaseSender('1111.111.111','user','pass','db_name')

    PIDWriter.write_current_script_pid_to_file()

    yolo_detection_model = YoloDetectionModel(["person"], minimum_probability_for_detection=0.6, database_sender=database_sender)#telegram_bot=telegram_bot

    yolo_detection_model.perform_detection_on_images_from_current_folder()
