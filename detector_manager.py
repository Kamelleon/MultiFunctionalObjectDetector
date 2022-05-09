import socket, threading, os

run_status = ""
script_running = False
def signal_reciever():
    global run_status
    s = socket.socket()

    s.bind(('0.0.0.0', 6666 ))
    s.listen(0)

    while True:

        client, addr = s.accept()

        while True:
            command = client.recv(32)

            if len(command) ==0:
               break

            else:
                run_status = command.decode("utf-8")
                print(run_status)

        client.close()


def script_killer():
    global script_running, run_status
    while True:
        if run_status == "OFF" and script_running == True:
            with open("detector_script_pid.txt","r") as f:
                detector_pid = f.readline()
                detector_pid = str(detector_pid)
            os.system(f"sudo kill -9 {detector_pid}")
            script_running = False

def script_invoker():
    global script_running, run_status
    while True:
        print(run_status)
        if run_status == "ON" and script_running == False:
            print("invoke")
            script_running = True
            os.system("sudo -E python3 main.py")



t1 = threading.Thread(target=signal_reciever)
t1.start()
t2 = threading.Thread(target=script_invoker)
t2.start()
t3 = threading.Thread(target=script_killer)
t3.start()
