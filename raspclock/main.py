from Adafruit_CharLCD import Adafruit_CharLCDPlate
import logging
import logging.handlers
import sys
import stage



class ClockApp():
    def __init__(self):
        self.logger = None

    def start(self):
        self.__configure_logging()
        self.logger.debug("Start Clock App")
        zmtstage = stage.ReadZMPStage()
        zmtstage.run()

    def __configure_logging(self):
        shandler = logging.StreamHandler(stream=sys.stdout)
        fhandler = logging.handlers.RotatingFileHandler("../logs/clock-app.log",backupCount=20)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
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