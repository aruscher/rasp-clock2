import logging
import Adafruit_CharLCD as LCD
import sys
import tty
import termios
from datetime import timedelta

class Stage():
    def __init__(self):
        self.logger = logging.getLogger("logger")
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.first_line = ""
        self.second_line = ""

    def run(self):
        raise NotImplementedError

    def write_msg_to_display(self, msg):
        self.lcd.clear()
        self.lcd.message(msg)
        self.logger.debug("write '%s' to display"%msg.replace("\n","\\n"))

    def write_memory_to_display(self):
        msg = "%s\n%s" % (self.first_line, self.second_line)
        self.write_msg_to_display(msg)

    def get_char_from_keyboard(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class ReadZMPStage(Stage):
    def __init__(self):
        Stage.__init__(self)
        self.logger.debug("Read ZMP Stage created")
        self.zmp = 0

    def run(self):
        self.logger.debug("Run ZMP Stage")
        self.first_line = "Zeitmesspunkte:"
        self.second_line = ""
        self.write_memory_to_display()
        self.lcd.blink(True)
        self._readZMPStages()
        return self.zmp

    def _readZMPStages(self):
        text = ""
        while (True):
            key = self.get_char_from_keyboard()
            # Enter
            if ord(key) == 13:
                break
            # backspace
            elif ord(key) == 127:
                text = text[:-1]
            # accept only numeric values
            elif 48 <= ord(key) <= 57:
                text += key
            self.second_line = text
            self.write_memory_to_display()
        self.zmp = int(text)
        self.logger.debug("Read '%d' Zeitmesspunkte" % self.zmp)

class ReadTimesStage(Stage):
    def __init__(self, zmp):
        Stage.__init__(self)
        self.logger.debug("RT-Stage created")
        self.zmp = zmp
        self.time_offsets = []

    def run(self):
        self.logger.debug("Run RT-Stage")
        for current_index in range(0,self.zmp):
            self.logger.debug("Read Timer: %d"%(current_index+1))
            self.first_line = "Timer %d:"%(current_index+1)
            time = self._read_time()
            self.logger.debug("Read Timer: %s"%self._time_to_str(time))
            time_offset = self._convert_time_to_offset(time)
            self.logger.debug("Convert Timer to Offset: %s hh:mm:ss"%time_offset)
            self.time_offsets.append(time_offset)
        return self.time_offsets

    def _read_time(self):
        time = [0,0,0,0]
        self.second_line = self._time_to_str(time)
        self.write_memory_to_display()
        self.lcd.blink(True)
        #read every diget of the time
        cursor_positions = [0,1,3,4]
        for i in range(0,len(time)):
            #move cursor to corresponding number
            self.lcd.set_cursor(cursor_positions[i],1)
            #read until valid input
            while True:
                key = self.get_char_from_keyboard()
                #accpet only numeric imput
                if 48 <= ord(key) <= 57:
                    time[i] = int(key)
                    break
                #ignore other input
                else:
                    continue
            self.second_line = self._time_to_str(time)
            self.write_memory_to_display()
        return time

    def _convert_time_to_offset(self,time):
        minutes = int("%d%d"%(time[0],time[1]))
        seconds = int("%d%d"%(time[2],time[3]))
        delta = timedelta(minutes=minutes,seconds=seconds)
        return delta

    def _time_to_str(self,time):
        return "%d%d:%d%d"%(time[0],time[1],time[2],time[3])

class CheckTimesStage(Stage):
    def __init__(self,offsets):
        Stage.__init__(self)
        self.logger.debug("CT-Stage created")
        self.offsets = offsets

    def run(self):
        self.logger.debug("Run CT-Stage")
        return self.offsets