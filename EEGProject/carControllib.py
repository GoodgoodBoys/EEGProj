import numpy as np
import pyqtgraph as pg
import random
import serial
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor
from joblib import load

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowOperations, WaveletTypes

from winDataCollection import ImageSequenceAnimation
from ML import EEGCurrentData

def carControl(board): 
    global modelCar
    modelCar = carController(board)
    modelCar.show()

class carController(QWidget):
    Action_left = ImageSequenceAnimation.Action_left                    # Action define
    Action_right = ImageSequenceAnimation.Action_right
    Action_stop = ImageSequenceAnimation.Action_stop
    Action_error = ImageSequenceAnimation.Action_error

    def __init__(self, board):
        super().__init__()

        self.board = board

        self.WIDTH = 3000
        self.HEIGHT = 400
        self.setWindowTitle("Control model car")
        self.setGeometry(100, 100, self.WIDTH, self.HEIGHT)
        self.esp32 = serial.Serial("COM5", 115200, timeout=1)

        self.running = True

        self.eeg_thread = EEGCurrentData(self.board)
        self.eeg_thread.action_signal.connect(self.handle_action)       # connect handle action
        self.eeg_thread.start()
        

    def handle_action(self, action):
        self.esp32.write(str(action).encode())                          # emit action

    def closeEvent(self, a0):
        if self.eeg_thread.isRunning():
            self.eeg_thread.stop()
        if self.esp32 and self.esp32.is_open:
            self.esp32.close()
        self.running = False
        return super().closeEvent(a0)



