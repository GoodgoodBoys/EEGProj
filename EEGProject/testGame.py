import numpy as np
import pyqtgraph as pg
import random
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QLabel, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor
from joblib import load

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowOperations, WaveletTypes

from winDataCollection import ImageSequenceAnimation
from ML import EEGCurrentData

def testGame(board):
    global game
    game = BallGame(board)
    game.show()

class BallGame(QWidget):
    Action_left = ImageSequenceAnimation.Action_left
    Action_right = ImageSequenceAnimation.Action_right
    Action_error = ImageSequenceAnimation.Action_error

    def __init__(self, board):
        super().__init__()

        self.board = board

        # 窗口参数
        self.WIDTH = 3000
        self.HEIGHT = 400
        self.setWindowTitle("TestBench")
        self.setGeometry(100, 100, self.WIDTH, self.HEIGHT)

        # 小球参数
        self.ball_radius = 20
        self.ball_x = self.WIDTH // 2
        self.ball_y = self.HEIGHT // 2
        self.ball_speed = 5

        # 挡板参数（随机在顶部或底部）
        self.bar_width = 20
        self.bar_height = self.HEIGHT
        self.bar_x = random.choice([0, self.WIDTH - self.bar_width])
        self.bar_y = 0
        
        # 定时器（控制刷新率）
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(100)  # 100ms 刷新一次

        self.running = True

        self.update_game()

        self.eeg_thread = EEGCurrentData(self.board)
        self.eeg_thread.action_signal.connect(self.handle_action)  # 连接信号与槽
        self.eeg_thread.start()
        

    def handle_action(self, action):
        if action == self.Action_left and self.ball_x >= 0:
            self.ball_x -= self.ball_speed
        elif action == self.Action_right and self.ball_x <= self.WIDTH:
            self.ball_x += self.ball_speed
        self.update()

    def update_game(self):
        """ 更新游戏状态 """
        if not self.running:
            return
        
        # 触碰挡板判定
        if self.bar_x == 0 and self.ball_x - self.ball_radius <= self.bar_width:
            print("Game Over! 碰到左挡板")
            self.running = False
            self.eeg_thread.stop()
        elif self.bar_x == self.WIDTH - self.bar_width and self.ball_x + self.ball_radius >= self.WIDTH - self.bar_width:
            print("Game Over! 碰到右挡板")
            self.running = False
            self.eeg_thread.stop()

        self.update()  # 刷新画面

    # def keyPressEvent(self, event):
    #     """ 处理键盘事件（W/S 或 ↑/↓ 控制小球移动） """
    #     if not self.running:
    #         return
        
    #     if event.key() == Qt.Key_W or event.key() == Qt.Key_Up:
    #         self.ball_y -= self.ball_speed
    #     elif event.key() == Qt.Key_S or event.key() == Qt.Key_Down:
    #         self.ball_y += self.ball_speed

    #     self.update()  # 立即刷新画面

    def paintEvent(self, event):
        """ 绘制游戏界面 """
        painter = QPainter(self)
        painter.fillRect(0, 0, self.WIDTH, self.HEIGHT, QColor(150, 150, 150))  # 背景

        # 画小球
        painter.setBrush(QColor(50, 50, 255))
        painter.drawEllipse(self.ball_x - self.ball_radius, self.ball_y - self.ball_radius, self.ball_radius * 2, self.ball_radius * 2)

        # 画挡板
        painter.setBrush(QColor(255, 50, 50))
        painter.drawRect(self.bar_x, self.bar_y, self.bar_width, self.bar_height)

    def closeEvent(self, a0):
        if self.eeg_thread.isRunning():
            self.eeg_thread.stop()
        self.running = False
        return super().closeEvent(a0)

