import yaml
from yaml.loader import SafeLoader
import os


class Bash:
    def __init__(self):
        self.scripts_folder_name = "camera_scripts"
        self.logs_folder_name = "camera_logs"

    def create_script(self, camera_name, gst_command):
        os.system(f"touch {self.logs_folder_name}/{camera_name}.log")
        with open(f"{self.scripts_folder_name}/{camera_name}.sh", "w+") as sh_file:
            sh_file.write(
                f"while true; do gst-launch-1.0 rtspsrc location={gst_command} ! videorate ! video/x-raw,framerate=2/1 ! jpegenc ! multifilesink location='./{camera_name}.jpg' | while IFS= read -r line; do printf '%s %s\n' \"$(date)\" \"$line\"; done >>{self.logs_folder_name}/{camera_name}.log; sleep 1; done")

    def run_script(self, camera_name):
        os.system(f"bash {self.scripts_folder_name}/{camera_name}.sh & ")


class Cameras:
    def __init__(self):
        self.bash = Bash()
        self.config_filename = "config.yaml"

    def set_up_from_config_file(self):
        with open(self.config_filename, "r") as config_file:
            try:
                config_file = yaml.load(config_file, Loader=SafeLoader)

                for name in config_file['cameras']:
                    rtsp_ip = config_file['cameras'][name]["rtsp_ip"]
                    if config_file['cameras'][name]["type"] == "h265":
                        gst_string = f"'{rtsp_ip}' ! rtph265depay ! avdec_h265"
                        self.bash.create_script(name, gst_string)
                        self.bash.run_script(name)
                    elif config_file['cameras'][name]["type"] == "h264":
                        gst_string = f"'{rtsp_ip}' ! rtph264depay ! avdec_h264"
                        self.bash.create_script(name, gst_string)
                        self.bash.run_script(name)
                    else:
                        print(f"Unsupported codec for camera: {name}")


            except yaml.YAMLError as exc:
                print(exc)
                print("Could not open config file")
                logging.critical("Could not read config file.")


if __name__ == "__main__":
    c = Cameras()
    c.set_up_from_config_file()
