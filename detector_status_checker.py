import time
import telepot
import pymysql
import datetime
class TelegramBot:
    def __init__(self, bot_token, group_id):
        self.bot_token = bot_token
        self.group_id = group_id

        print("[~] Connecting to a Telegram bot...")
        self.bot = telepot.Bot(self.bot_token)
        print("[+] Connected to the Telegram bot")


    def send_message(self, message):
        self.bot.sendMessage(self.group_id, message)

class Database:
    def __init__(self,host,user,password,database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
    
    def check_statuses_of_detectors(self):
        con=pymysql.connect(host=self.host,user=self.user,password=self.password,database=self.database,cursorclass=pymysql.cursors.DictCursor)
        cur = con.cursor()
        query = "select id,ts from activity"
        cur.execute(query)
        result = cur.fetchall()
        print(result)
        for item in result:
                first_Time = item["ts"]
                later_Time = datetime.datetime.now()
                difference = later_Time - first_Time
                print(difference)
                diffInMinutes = int(round(difference.total_seconds()/60,0))
                if diffInMinutes > 1:
                        print("device {} offline since {}".format(item["id"], item['ts'].strftime("%Y-%m-%d %H:%M")))
                        query = "update activity set status = 0 where id = {}".format(item["id"])
                        cur.execute(query)
                        con.commit()
                        return False
                else:
                    return True


if __name__ == "__main__":
    telegram_bot = TelegramBot("tokenid", "-groupid")
    database = Database('111.111.111.111','user','pass','db_name')
    while True:
        detector_online = database.check_statuses_of_detectors()
        if not detector_online:
            telegram_bot.send_message("Detektor nie dziala.")
            while True:
                detector_is_back = database.check_statuses_of_detectors()
                if detector_is_back:
                    telegram_bot.send_message("Detektor zaczal ponownie dzialac.")
                    break
                time.sleep(5)
        time.sleep(5)
            






