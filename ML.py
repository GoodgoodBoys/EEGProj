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
    """
    eeg_data: shape (8, n_samples)
    返回值: shape (40,) —— 即 8 个通道 × 5 个波段
    """
    n_channels, n_samples = eeg_data.shape
    
    # 频率分辨率
    freqs = np.fft.fftfreq(n_samples, d=1/fs)  # shape (n_samples,)
    
    # 只取前半段(正频率部分)
    half_len = n_samples // 2
    freqs_pos = freqs[:half_len]  # shape (half_len,)
    
    # 定义 5 个波段范围 (Hz)
    # 你可以根据需求调整波段范围
    delta_range = (0.5, 4)
    theta_range = (4, 8)
    alpha_range = (8, 13)
    beta_range  = (13, 30)
    gamma_range = (30, 50)

    # 用于存放 8 个通道的 5 个波段特征
    features = []

    for ch in range(n_channels):
        signal = eeg_data[ch, :]  # shape (n_samples,)
        
        # 计算 FFT 并取幅度谱
        fft_vals = np.fft.fft(signal)
        mag = np.abs(fft_vals[:half_len])  # shape (half_len,)

        # 计算各波段的能量（简单方法：对幅度谱求和；也可考虑平方或 Welch PSD）
        # 找到每个波段对应的频率索引
        def band_power(freq_band):
            fmin, fmax = freq_band
            idx = np.where((freqs_pos >= fmin) & (freqs_pos < fmax))[0]
            # 对应索引处的幅度求和 (或平方和等)
            return np.sum(mag[idx])
        
        delta_power = band_power(delta_range)
        theta_power = band_power(theta_range)
        alpha_power = band_power(alpha_range)
        beta_power  = band_power(beta_range)
        gamma_power = band_power(gamma_range)
        
        # 将当前通道的 5 个波段特征存入
        features.extend([delta_power, theta_power, alpha_power, beta_power, gamma_power])

    # 转成 numpy array, shape (40,)
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
        self.model = load("svm_final_model.pkl")

        self.window_size = 180
        
        # 用于存储最近的 window_size 个采样点 (8×300)
        self.data_window = np.zeros((8, self.window_size))
        
        # 设定每次触发预测的步长（stride），比如每来 1 个采样点就预测一次
        self.stride = 1
        self.counter = 0  # 用于计数距离上次预测间隔了多少个采样点
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

        # for i in range(7):
        #     DataFilter.perform_bandpass(testdata[i+1], BoardShim.get_sampling_rate(0), 0.5, 50.0, 4,
        #         FilterTypes.BESSEL_ZERO_PHASE, 0)
            
        # print(testdata)

        # 2. 计数器自增
        self.counter += 1

        features = extract_band_features(testdata, fs=self.fs)

        # print(features)
        features_2d = features.reshape(1, -1)
        prediction = self.model.predict(features_2d)  # 假设输出 0 或 1
        if self.counter >= 180:
            self.counter = 0  # 重置计数器
        print(prediction)
    # 3. 每 0.5s 触发一次预测（假设采样率 250Hz -> 每 125 个点约等于 0.5s）

        # 返回预测结果：假设模型输出为 0 或 1        # 4. 模型预测：将 8×300 reshape 成 1×2400，然后调用已经加载好的 SVM 模型
        return prediction[0]

    def stop(self):
        self.running = False
        self.board.stop_stream()
        self.quit()
        self.wait()
