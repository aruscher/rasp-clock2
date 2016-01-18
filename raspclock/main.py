from Adafruit_CharLCD import Adafruit_CharLCDPlate
import logging
import logging.handlers
import sys
import stage
import Queue



class ClockApp():
    def __init__(self):
        self.logger = None

    def start(self):
        self.__configure_logging()
        self.logger.info("Start Clock App")
        queue =  Queue.Queue()
        zmpstage = stage.ReadZMPStage(queue)
        zmp = zmpstage.run()
        rtstage = stage.ReadTimesStage(queue,zmp)
        time_offsets = rtstage.run()
        ctstage = stage.CheckTimesStage(queue,time_offsets)
        checked_time_offsets = ctstage.run()
        self.logger.info("Clock Configuration completed")
        self.logger.info("Zeitmesspunkte: %d"%zmp)
        self.logger.info("Zeitoffsets: %s"%[ctstage.timedelta_to_str(offset) for offset in checked_time_offsets])
        wfsstage = stage.WaitForStartStage(queue)
        wfsstage.run()
        crstage = stage.ClockRunningStage(queue,checked_time_offsets)
        crstage.run()


    def __configure_logging(self):
        shandler = logging.StreamHandler(stream=sys.stdout)
        fhandler = logging.handlers.RotatingFileHandler("../logs/clock-app.log",backupCount=20)
        formatter = logging.Formatter('%(levelname)s - %(thread)d - %(funcName)s - %(message)s')
        shandler.setFormatter(formatter)
        fhandler.setFormatter(formatter)
        self.logger = logging.getLogger("logger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(shandler)
        self.logger.addHandler(fhandler)
        self.logger.addHandler(fhandler)
        fhandler.doRollover()

if __name__ == '__main__':
    app = ClockApp()
    app.start()