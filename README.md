Rasp-Clock
==========

Setup
-----
* ???


Todos
------
* Letzte Zahl bei der Timereingabe zurücksetzen

Anleitung
---------

1. Bevor wir anfangen können muss der Nummernblock mittels der "NUM LOCK"-Taste aktiviert werden (oben links)
2. Anzahl der Zeitmesspunkte angeben
    * Steuerung: mit den Zahlenblock die gewünschte Anzahl der Zeitmesspunkte eingeben
    * Bei einer Eingabe einer falschen Zahl kann mittels der "Backspace"-Taste (oben rechts mit dem Pfeil <-) die letzte eingegebene Zahl gelöscht werden
    * Wenn die gewünschte Anzahl auf den Display steht kann mittels der "Enter"-Taste (unten rechts) dieser Modus verlassen werden
    * Es können nur Zahlen eingegeben werden
3. Eingabe der Zeiten
    * Steuerung: mit dem Zahlenblock die gewünschten MINUTEN:SEKUNDEN eingebnen
    * Bei einer Eingabe einer falschen Zahl kann mittels der "Backspace"-Taste (oben rechts mit dem Pfeil <-) die letzte eingegebene Zahl gelöscht werden
    * Sollte Sekunden eingeben >60 (welche also eine eine volle Minute beschreiben) werden diese automatisch zu den Minuten dazugerechnet
4. Kontrolle der Zeiten
    * Sobald Kontrolle auf dem Display steht kann mittels der SELECT-Taste (unter dem Display ganz links) die Kontrolle begonnen werden
    * Mittels der HOCH-Taste kann der nächste Timer angezeigt werden, mit der RUNTER-Taste kann der vorige Timer angezeigt werden
    * Mittels der RECHTS-Taste kann die Zeit verändert werden -> Steuerung dazu wie bei 3.
5. Scharfschaltung
    * Die eingestellten Zeiten sind "scharf" geschaltet
    * mit der RECHTS-Taste können die Timer gestartet werden
6. Timer laufen
    * Wenn alle Timer fertig sind steht "Fertig" auf den Display
    * mit der HOCH-Tasge kann der nächste Timer angezeigt werden
    * mit der RUNTER-Tasge kann der vorrige Timer angezeigt werden falls dieser noch nicht abgelaufen ist
    * in den letzten 10 Sekunden kommt ein Ton über die Kopfhörer und das Gerät piept auch



Verbesserungen
--------------
* übersichtlicherer Code
* bessere Anleitung/Dokumentation
* vernünftige Logging-Mechanismus um Fehler zu finden
* genauigkeit von paar Microsekunden




    def run(self):
        self.logger.debug("CRS-Stage run")
        current_index = 0
        ticker = BetterTick(self.communication_queue)
        ticker.start()
        #displayer = DisplayThread(self.lcd)
        #displayer.start()
        sound = SoundThread()
        sound.start()
        beeper = BeeperThread()
        beeper.start()
        while True:
            event = self.communication_queue.get()
            if event == 8:
                rest_time = self.calculate_remaining_time(self.offsets[current_index])
                if rest_time <= 0:
                    current_index+=1
                    if current_index >= len(self.offsets):
                        break
                    rest_time = self.calculate_remaining_time(self.offsets[current_index])
                elif rest_time <= 10:
                    #sound.play()
                    #beeper.beep()
                    pass
                self.logger.debug("Rest Time: %s"%rest_time)
                #displayer.set_message("Timer %d\n%s"%(current_index+1,self.seconds_to_str(rest_time)))
            elif event == LCD.UP and current_index < len(self.offsets)-1:
                current_index +=1
                self.communication_queue.put(8)
            elif event == LCD.DOWN and current_index > 0:
                current_index -=1
                self.communication_queue.put(8)
        ticker.stop()
        self.write_msg_to_display("Fertig")
        now = datetime.now()
        self.logger.debug("Time taken: %s"%(now - self.reference_point))
        return