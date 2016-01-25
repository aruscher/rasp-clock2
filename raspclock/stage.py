import logging
import Adafruit_CharLCD as LCD
import sys
import tty
import termios
from datetime import timedelta,datetime
import threading
from math import ceil
import time

class LCDKeyThrad(threading.Thread):
    def __init__(self, queue, lcd, logger):
        super(LCDKeyThrad, self).__init__()
        self.queue = queue
        self.lcd = lcd
        self.logger = logger

    def run(self):
        self.logger.debug("RUN LCD KEY THREAD")
        while True:
            key = self.read_lcd_key()
            self.logger.debug("Put %s to Key-Queue" % key)
            self.queue.put(key)

    def read_lcd_key(self):
        pressed_key = None
        keys = [LCD.SELECT, LCD.LEFT, LCD.RIGHT, LCD.UP, LCD.DOWN]
        # read pressed key
        self.logger.debug("Read Pressed Key")
        while pressed_key is None:
            for key in keys:
                if self.lcd.is_pressed(key):
                    pressed_key = key
        self.logger.debug("%s Key was read" % pressed_key)
        # wait until key is released
        self.logger.debug("Wait for releasing of key")
        is_released = False
        while not is_released:
            if all([not self.lcd.is_pressed(key) for key in keys]):
                is_released = True
        return pressed_key


class TickThread(threading.Thread):
    def __init__(self,queue):
        super(TickThread, self).__init__()
        self.queue = queue

    def run(self):
        while True:
            self.queue.put(8)
            time.sleep(1)

class DisplayThread(threading.Thread):
    def __init__(self,lcd):
        super(DisplayThread, self).__init__()
        self.lcd = lcd
        self.message = ""
        self.flag = False

    def run(self):
        while True:
            if self.flag:
                self.lcd.clear()
                self.lcd.message(self.message)
                self.flag = False

    def set_message(self,msg):
        self.flag = True
        self.message = msg

class Stage():
    def __init__(self,queue):
        self.logger = logging.getLogger("logger")
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.first_line = ""
        self.second_line = ""
        self.lcd_key_thread = None
        self.communication_queue = queue

    def run(self):
        raise NotImplementedError

    def write_msg_to_display(self, msg):
        self.lcd.clear()
        self.lcd.message(msg)
        self.logger.debug("write '%s' to display" % msg.replace("\n", "\\n"))

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

    def _read_time(self):
        time = [0, 0, 0, 0]
        self.second_line = self.time_to_str(time)
        self.write_memory_to_display()
        self.lcd.blink(True)
        # read every diget of the time
        cursor_positions = [0, 1, 3, 4]
        counter = 0
        while True:
            # move cursor to corresponding number
            self.lcd.set_cursor(cursor_positions[counter], 1)
            # read until valid input
            while True:
                key = self.get_char_from_keyboard()
                # accpet only numeric imput
                if 48 <= ord(key) <= 57:
                    time[counter] = int(key)
                    counter += 1
                    break
                # backspace for removing last input
                elif ord(key) == 127:
                    time[counter - 1] = 0
                    counter -= 1
                    break
                # ignore other input
                else:
                    continue
            self.second_line = self.time_to_str(time)
            self.write_memory_to_display()
            if counter == len(cursor_positions):
                break
        return time

    def convert_time_to_offset(self, time):
        minutes = int("%d%d" % (time[0], time[1]))
        seconds = int("%d%d" % (time[2], time[3]))
        delta = timedelta(minutes=minutes, seconds=seconds)
        return delta

    def time_to_str(self, time):
        return "%d%d:%d%d" % (time[0], time[1], time[2], time[3])

    def timedelta_to_str(self, time):
        time_text = str(time)
        splitted_time_text = time_text.split(":")
        splitted_time_ints = [int(ceil(float(elem))) for elem in splitted_time_text]
        time_converted = [splitted_time_ints[0] * 60 + splitted_time_ints[1], splitted_time_ints[2]]
        return "%02d:%02d" % (time_converted[0], time_converted[1])


class ReadZMPStage(Stage):
    def __init__(self,queue):
        Stage.__init__(self,queue)
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
            if ord(key) == 13 or ord(key) == 102:
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
    def __init__(self,queue, zmp):
        Stage.__init__(self,queue)
        self.logger.debug("RT-Stage created")
        self.zmp = zmp
        self.time_offsets = []

    def run(self):
        self.logger.debug("Run RT-Stage")
        for current_index in range(0, self.zmp):
            self.logger.debug("Read Timer: %d" % (current_index + 1))
            self.first_line = "Timer %d:" % (current_index + 1)
            time = self._read_time()
            self.logger.debug("Read Timer: %s" % self.time_to_str(time))
            time_offset = self.convert_time_to_offset(time)
            self.logger.debug("Convert Timer to Offset: %s hh:mm:ss" % time_offset)
            self.time_offsets.append(time_offset)
        return self.time_offsets


class CheckTimesStage(Stage):
    def __init__(self, queue,offsets):
        Stage.__init__(self,queue)
        self.logger.debug("CT-Stage created")
        self.offsets = offsets

    def run(self):
        self.logger.debug("Run CT-Stage")
        self.first_line = "Kontrolle!"
        self.second_line = "SELECT"
        self.write_memory_to_display()
        self.lcd_key_thread = LCDKeyThrad(self.communication_queue, self.lcd, self.logger)
        self.lcd_key_thread.start()
        while True:
            pressed_key = self.communication_queue.get()
            if pressed_key == LCD.SELECT:
                self.check_times()
                break
        self.logger.debug("Complete timer control")
        self.logger.debug("Saved Timers: %s" % [self.timedelta_to_str(offset) for offset in self.offsets])
        return self.offsets

    def check_times(self):
        current_index = 0
        is_ready = False
        while not is_ready:
            current_offset = self.offsets[current_index]
            self.first_line = "Timer %d" % (current_index + 1)
            self.second_line = self.timedelta_to_str(current_offset)
            self.write_memory_to_display()
            pressed_key = self.communication_queue.get()
            if pressed_key == LCD.UP and current_index != len(self.offsets) - 1:
                current_index += 1
                self.logger.debug("Show next timer")
            elif pressed_key == LCD.DOWN and current_index > 0:
                current_index -= 1
                self.logger.debug("Show previous timer")
            elif pressed_key == LCD.RIGHT:
                self.logger.debug("Reread timer")
                time = self.convert_time_to_offset(self._read_time())
                self.logger.debug("Change timer from %s to %s" % (self.offsets[current_index], time))
                self.offsets[current_index] = time
                self.lcd.blink(False)
            elif pressed_key == LCD.LEFT:
                return


class WaitForStartStage(Stage):
    def __init__(self,queue):
        Stage.__init__(self,queue)
        self.logger.debug("WFS-Stage created")

    def run(self):
        self.logger.debug("WFS-Stage run")
        self.first_line = "Bereit"
        self.second_line = ""
        self.write_memory_to_display()
        while True:
            key = self.communication_queue.get()
            self.logger.debug("pressed key")
            if key == LCD.RIGHT:
                break
        self.logger.debug("Complete WFS Stage")


class ClockRunningStage(Stage):
    def __init__(self,queue, offsets):
        Stage.__init__(self,queue)
        self.logger.debug("CRS-Stage created")
        self.offsets = offsets
        self.reference_point = datetime.now()
        self.logger.info("Timer reference point: %s"%self.reference_point)

    def run(self):
        self.logger.debug("CRS-Stage run")
        current_index = 0
        ticker = TickThread(self.communication_queue)
        ticker.start()
        displayer = DisplayThread(self.lcd)
        displayer.start()
        while True:
            event = self.communication_queue.get()
            if event == 8:
                rest_time = self.calculate_remaining_time(self.offsets[current_index])
                if rest_time <= 0:
                    current_index+=1
                    if current_index >= len(self.offsets):
                        break
                    rest_time = self.calculate_remaining_time(self.offsets[current_index])
                self.logger.debug("Rest Time: %s"%rest_time)
                displayer.set_message("Timer %d\n%s"%(current_index+1,self.seconds_to_str(rest_time)))
            elif event == LCD.UP and current_index < len(self.offsets)-1:
                current_index +=1
                self.communication_queue.put(8)
            elif event == LCD.DOWN and current_index > 0:
                current_index -=1
                self.communication_queue.put(8)
        self.write_msg_to_display("Fertig")
        return

    def calculate_remaining_time(self,offset):
        now = datetime.now()
        ref = self.reference_point
        ref_seconds = (ref.hour*60+ref.minute)*60+ref.second
        now_seconds = (now.hour*60+now.minute)*60+now.second
        rest_seconds = ref_seconds+offset.seconds-now_seconds
        return rest_seconds

    def seconds_to_str(self,seconds):
        minutes = seconds //60
        seconds %= 60
        return "%02d:%02d"%(minutes,seconds)