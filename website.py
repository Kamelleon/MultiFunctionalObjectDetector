import datetime
import threading
import re
from flask import Flask, render_template, request, session, url_for, redirect
from flask_autoindex import AutoIndex
import os
import time
app = Flask(__name__)

auto_index = AutoIndex(app, os.path.curdir, add_url_rules=False)


class DetectorManager:
    def __init__(self):
        self.detector_pid = ""

    def get_pid_of_detector(self):
        get_pid_thread = threading.Thread(target=self._get_pid_of_detector)
        get_pid_thread.start()

    def _get_pid_of_detector(self):
        while True:
            with open("detector_script_pid.txt", "r") as f:
                self.detector_pid = str(f.readline())
            time.sleep(2)

    def stop_detector(self):
        t1 = threading.Thread(target=self._stop_detector)
        t1.start()

    def _stop_detector(self):
        os.system(
            f'if [ "$(ps -o state= -p {self.detector_pid})" = T ]; then echo "Detector already sleeps"; else sudo kill -STOP {self.detector_pid}; sleep 20; sudo kill -CONT {self.detector_pid}; fi;')


@app.route("/")
def home():
    detector_manager.stop_detector()
    directories_with_dates = []
    dirs_list = os.listdir(os.getcwd())
    for directory in dirs_list:
        if re.match(".{2}-.{2}-.{4}", directory):
            directories_with_dates.append(directory)
    directories_with_dates.sort(key=lambda date: datetime.datetime.strptime(date, '%d-%m-%Y'))
    return render_template('home.html',data=directories_with_dates)


@app.route('/check_cameras/<path:path>',methods=['GET', 'POST'])
def autoindex(path='.'):
    detector_manager.stop_detector()
    return auto_index.render_autoindex(path)


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("home"))


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = '0'
    response.headers["Pragma"] = "no-cache"
    return response


if __name__ == "__main__":
    detector_manager = DetectorManager()
    detector_manager.get_pid_of_detector()
    app.secret_key = "super secret key"
    app.debug = True
    app.run(host="0.0.0.0")
