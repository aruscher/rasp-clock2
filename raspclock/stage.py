import logging
import Adafruit_CharLCD as LCD

class Stage():
    def __init__(self):
        self.logger = logging.getLogger("logger")
        self.lcd = LCD.Adafruit_CharLCDPlate()

    def run(self):
        raise NotImplementedError


class ReadZMPStage(Stage):
    def __init__(self):
        Stage.__init__(self)
        self.logger.debug("READ ZMT Created")
        self.zmp = 0

    def run(self):
        self.logger.debug("Run ZMT Stage")
        self.lcd.message("Zeitmesspunkte:\n%d"%(self.zmp))
        self.lcd.set_cursor(0,1)
        self.lcd.blink(True)

    def readZMPStages(self):
        self.lcd.
        pass