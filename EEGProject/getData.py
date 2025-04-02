import sys
import argparse
import glob
# from glob import glob
import time
import serial.tools.list_ports
import os
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

import ML
from testGame import testGame
from winDataCollection import winDataCollection, winDataCollection10
from carControllib import carControl

def main():
    BoardShim.enable_dev_board_logger()

    parser = argparse.ArgumentParser()
    # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
    parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False,
                        default=0)
    parser.add_argument('--ip-port', type=int, help='ip port', required=False, default=0)
    parser.add_argument('--ip-protocol', type=int, help='ip protocol, check IpProtocolType enum', required=False,
                        default=0)
    parser.add_argument('--ip-address', type=str, help='ip address', required=False, default='')
    parser.add_argument('--serial-port', type=str, help='serial port', required=False, default='')
    parser.add_argument('--mac-address', type=str, help='mac address', required=False, default='')
    parser.add_argument('--other-info', type=str, help='other info', required=False, default='')
    parser.add_argument('--serial-number', type=str, help='serial number', required=False, default='')
    parser.add_argument('--board-id', type=int, help='board id, check docs to get a list of supported boards',
                        required=True)
    parser.add_argument('--file', type=str, help='file', required=False, default='')
    parser.add_argument('--master-board', type=int, help='master board id for streaming and playback boards',
                        required=False, default=BoardIds.NO_BOARD)
    args = parser.parse_args()

    params = BrainFlowInputParams()
    params.ip_port = args.ip_port
    params.serial_port = args.serial_port
    params.mac_address = args.mac_address
    params.other_info = args.other_info
    params.serial_number = args.serial_number
    params.ip_address = args.ip_address
    params.ip_protocol = args.ip_protocol
    params.timeout = args.timeout
    params.file = args.file
    params.master_board = args.master_board

    board = BoardShim(args.board_id, params)
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found. Please check your device connection.")
    else:
        for port in ports:
            print(f"Found port: {port.device}")
    board.prepare_session()

    app = QApplication([])
    win = QWidget()
    win.setWindowTitle("Team#8_EEG_TestWindow")
    win.resize(300, 200)

    input_box = QLineEdit()
    input_box.setPlaceholderText("COMx")

    # Define button
    btnWaveform = QPushButton("BrainWave")
    btnWaveform.clicked.connect(lambda: print("BrainWaveButton"))
    
    btnStartTraining = QPushButton("DataCollection")
    btnStartTraining.clicked.connect(lambda: winDataCollection(board))

    btnStartTraining10 = QPushButton("10 times")
    btnStartTraining10.clicked.connect(lambda: winDataCollection10(board))

    btnTest = QPushButton("TestGame")
    btnTest.clicked.connect(lambda: testGame(board))

    btnCarControl = QPushButton("carControl")
    btnCarControl.clicked.connect(lambda: carControl(board))

    # Create button
    layout = QVBoxLayout()
    layout.addWidget(input_box)
    layout.addWidget(btnWaveform)
    layout.addWidget(btnStartTraining)
    layout.addWidget(btnStartTraining10)
    layout.addWidget(btnTest)
    layout.addWidget(btnCarControl)
    win.setLayout(layout)

    win.show()
    app.exec_()


if __name__ == "__main__":
    main()

