import pymysql
import logging
import traceback
import yaml
from yaml.loader import SafeLoader
import time


class DatabaseSender:
    logging.basicConfig(filename='detector_logger.txt',
                        filemode='a',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)

    def __init__(self):
        with open("config.yaml", "r") as config_file:
            try:
                config_file = yaml.load(config_file, Loader=SafeLoader)
            except yaml.YAMLError as exc:
                print(exc)
                logging.error("Could not open config file")
        self.host = config_file["mysql"]["host"]
        self.user = config_file["mysql"]["user"]
        self.password = config_file["mysql"]["password"]
        self.database = config_file["mysql"]["database_name"]
        self.ping_timeout = 3
        self.reconnect_timeout = 10

        try:
            self.con = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database,
                                       cursorclass=pymysql.cursors.DictCursor)
            self.cur = self.con.cursor()
        except:
            logging.error("Error occurred during connecting to the database")
            logging.error(f"{traceback.format_exc()}")

    def send_ping(self, device_id=1):
        query = f"update activity set ts=now(), status = 1 where id = {device_id}"
        while True:
            try:
                self.cur.execute(query)
                self.con.commit()
                logging.info("Database ping has been sent")
                time.sleep(self.ping_timeout)
            except:
                self.con.close()
                time.sleep(self.reconnect_timeout)
                try:
                    self.con = pymysql.connect(host=self.host, user=self.user, password=self.password,
                                               database=self.database,
                                               cursorclass=pymysql.cursors.DictCursor)
                    self.cur = self.con.cursor()
                except:
                    logging.error("Error occurred during connecting to the database")
                    logging.error(f"{traceback.format_exc()}")
                logging.error("Error occurred during sending a ping to the database")
                logging.error(f"{traceback.format_exc()}")
