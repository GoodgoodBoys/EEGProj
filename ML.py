import numpy as np
import pyqtgraph as pg
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor
from joblib import load

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowOperations, WaveletTypes

from winDataCollection import ImageSequenceAnimation

def extract_band_features(eeg_data, fs=256):

    n_channels, n_samples = eeg_data.shape
    
    freqs = np.fft.fftfreq(n_samples, d=1/fs)
    

    half_len = n_samples // 2
    freqs_pos = freqs[:half_len]
    
    delta_range = (0.5, 4)
    theta_range = (4, 8)
    alpha_range = (8, 13)
    beta_range  = (13, 30)
    gamma_range = (30, 50)

    features = []

    for ch in range(n_channels):
        signal = eeg_data[ch, :]
        
        fft_vals = np.fft.fft(signal)
        mag = np.abs(fft_vals[:half_len])


        def band_power(freq_band):
            fmin, fmax = freq_band
            idx = np.where((freqs_pos >= fmin) & (freqs_pos < fmax))[0]
            return np.sum(mag[idx])
        
        delta_power = band_power(delta_range)
        theta_power = band_power(theta_range)
        alpha_power = band_power(alpha_range)
        beta_power  = band_power(beta_range)
        gamma_power = band_power(gamma_range)
        
        features.extend([delta_power, theta_power, alpha_power, beta_power, gamma_power])

    return np.array(features)



class EEGCurrentData(QThread):
    action_signal = pyqtSignal(int)
    Action_left = ImageSequenceAnimation.Action_left
    Action_right = ImageSequenceAnimation.Action_right
    Action_error = ImageSequenceAnimation.Action_error

    def __init__(self, board):
        super().__init__()
        self.board = board
        self.running = True
        self.model = load("svm_final_model_2.pkl")

        self.window_size = 180
        
        self.data_window = np.zeros((8, self.window_size))
        
        self.stride = 1
        self.counter = 0
        self.fs = 256 
        self.running = True

    def run(self):
        self.board.start_stream()
        while self.running:
            data = self.board.get_board_data(1)
            current_data = np.vstack([data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8]])
            if current_data.shape == (8, 1):
                action = self.identify_action(current_data)
                self.action_signal.emit(action)
            
            


    def identify_action(self, current_data):
        self.data_window = np.roll(self.data_window, shift=-1, axis=1)
        self.data_window[:, -1] = current_data[:, 0]

        testdata = self.data_window

        self.counter += 1

        features = extract_band_features(testdata, fs=self.fs)

        features_2d = features.reshape(1, -1)
        prediction = self.model.predict(features_2d)
        if self.counter >= 180:
            self.counter = 0
        print(prediction)

        return prediction[0]

    def stop(self):
        self.running = False
        self.board.stop_stream()
        self.quit()
        self.wait()
