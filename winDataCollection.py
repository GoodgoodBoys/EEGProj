import time
import random
import glob
import os
import numpy as np
import pyqtgraph as pg

from datetime import datetime

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowOperations, WaveletTypes


# Data collection
def winDataCollection(board):
    global window
    window = ImageSequenceAnimation(board)
    window.show()

# Data collection for 10 times
def winDataCollection10(board): 
    runTimeCount = 0
    while runTimeCount < 10:
        loop = QEventLoop()    
        window = ImageSequenceAnimation(board)
        window.window_closed.connect(loop.quit)
        window.show()
        loop.exec_()

        time.sleep(0.5)
        runTimeCount += 1

class ImageSequenceAnimation(QWidget):
    window_closed = pyqtSignal()

    Action_left = 0
    Action_right = 1
    Action_stop = 3
    Action_error = 100

    def __init__(self, board):
        super().__init__()

        self.board = board

        self.setWindowTitle("Test animation")
        self.setGeometry(100, 100, 400, 400)

        layout = QVBoxLayout()
        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.setLayout(layout)

        rand_int = random.randint(0, 1)
        print("rand_int = ", rand_int)
        action_flag = self.action_switch(rand_int)

        if action_flag == self.Action_left:
            self.frames = sorted(glob.glob(os.path.join("frames_left", "*.png")))
        else :            
            self.frames = sorted(glob.glob(os.path.join("frames_right", "*.png")))

        self.frames = [os.path.abspath(frame) for frame in self.frames]  # Convert to absolute address
        print("Animation file:", self.frames)

        if not self.frames:
            print("Test animation file error!")
            return
        self.count = 0
        self.frame_index = 0

        # Setting timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(1000)  # Setting switch time 1000 == 1s

        self.start_task(action_flag)

        self.next_frame()  # Show first pricture
        QTimer.singleShot(6000, self.stop_timer_and_close)
    
    def action_switch(self, random_num): 
        if (random_num == 0):
                return ImageSequenceAnimation.Action_left
        elif (random_num == 1):
                return ImageSequenceAnimation.Action_right
        elif (random_num == 2):
                 return ImageSequenceAnimation.Action_error

    def next_frame(self):
        if self.frames:
            pixmap = QPixmap()
            pixmap.load(self.frames[self.frame_index])
            if pixmap.isNull():
                print(f"Can't load picture: {self.frames[self.frame_index]}")
            else:
                print(f"Current picture: {self.frames[self.frame_index]}")
                self.label.setPixmap(pixmap)
                self.label.adjustSize()  # Resize

            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.count += 1        
            if self.count == 5:
                self.timer.setInterval(100)
    
    # Data collection thread
    def start_task(self, action_flag):
        self.worker = DataCollectionThread(self.board, action_flag)
        self.worker.start()

    # Stop timer
    def stop_timer_and_close(self):
        self.timer.stop()
        self.window_closed.emit()
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.close()

    def closeEvent(self, event):
        self.timer.stop()
        self.window_closed.emit()
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()

class DataCollectionThread(QThread):
    dirPath = './data'

    def __init__(self, board, action):
        super().__init__()
        self.is_running = True  # Running status
        self.board = board      # Board Information
        self.action = action    # Action flag

    def run(self):
        try:
            self.board.start_stream()
            print("Start streaming")
        except Exception as e:
            print(f"Error: {e}")

        while self.is_running == True :
            pass
        self.collectData()

    def collectData(self):
        self.board.stop_stream()
        count = 0
        dataBuffer = np.empty((8, 0))
        while True:
            data = self.board.get_board_data(256)  # get all data and remove it from internal buffer
            current_data = np.vstack([data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8]])
            for i in range(7):
                DataFilter.perform_bandpass(data[i+1], BoardShim.get_sampling_rate(0), 0.5, 50.0, 4,
                    FilterTypes.BESSEL_ZERO_PHASE, 0)

            dataBuffer = np.concatenate((dataBuffer, current_data), axis=1)

            if data.shape[1] <= 0: 
                print("Collect all data.")
                break
        
        os.makedirs(self.dirPath, exist_ok=True)
        fileName = self.get_filename_by_milliseconds(self.dirPath)      # Create file name with current time

        np.savez(fileName, action_flag = self.action, data = dataBuffer)
        print("dataBuffer Size:  ", dataBuffer.size)
        print("dataBuffer Shape: ", dataBuffer.shape)
        print("Data save in: ", fileName)

    def get_filename_by_milliseconds(self, base_path, prefix="data", ext=".npz"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return os.path.join(base_path, f"{prefix}_{timestamp}{ext}")

    def stop(self):
        print("stop")
        self.is_running = False

