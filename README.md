# EEGProj

This project is a model car controlled by brain waves. The subjects will use tense or relaxed emotions to control the forward and backward movement of the car. 
We have tested the program in this environment:
* Windows Platform
* Python 3.9.12

Hardware
------------
* Cyton board
* Ultracortex Mark IV
* ESP32 based model car

Detailed documentation and purchase links regarding the testing equipment are available at the following address: https://docs.openbci.com/

Installation
------------
To run this project, please download and install the OpenBCI library first. https://github.com/brainflow-dev/brainflow

First, turn on the power of the Cyton board and then run:
    <pre>```.\getData.py --board-id 0 --serial-port COMx```</pre>
"COMx" is the port number mapped in your computer.

`EEGModelCar.ino` is the code for the model car based on ESP32, which needs to be burned into the car using Arduino.The assembly requirements of the trolley can be found in the report for details.
