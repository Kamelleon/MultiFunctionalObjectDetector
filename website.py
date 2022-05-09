import datetime
import threading

from flask import Flask, render_template, request, session, url_for, redirect
from flask_autoindex import AutoIndex
import os

app = Flask(__name__)

auto_index = AutoIndex(app, os.path.curdir, add_url_rules=False)




# @sleep_if_someone_connected
def stop_detector():
    os.system(
        f'if [ "$(ps -o state= -p {detector_pid})" = T ]; then echo "Detector already sleeps"; else sudo kill -STOP {detector_pid}; sleep 20; sudo kill -CONT {detector_pid}; fi;')

def detector_stopper():
    t1 = threading.Thread(target=stop_detector)
    t1.start()

@app.route("/")
def home():
    detector_stopper()
    session['url'] = url_for('home')
    return render_template('index.html')


@app.route('/check_cameras',methods=['GET', 'POST'])
@app.route('/check_cameras/<path:path>',methods=['GET', 'POST'])
def autoindex(path='.'):
    detector_stopper()
    if request.method == 'POST':
        date = request.form.get('calendar')
        date_converted = datetime.datetime.strptime(date,"%Y-%m-%d").strftime("%d-%m-%Y")
        session['url'] = url_for('autoindex')
        return auto_index.render_autoindex(date_converted)
    if path != ".":
        return auto_index.render_autoindex(path)
    else:
        return redirect(url_for("home"))


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("home"))


if __name__ == "__main__":
    with open("detector_script_pid.txt","r") as f:
        detector_pid = f.readline()
        detector_pid = str(detector_pid)
    app.secret_key = "secret"
    app.debug = True
    app.run(host="0.0.0.0")
