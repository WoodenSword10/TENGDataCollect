import sys 
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QMessageBox
import serial
import Ui_untitled
import serial.tools.list_ports
import time 
import pyqtgraph as pg
import numpy as np
import random

class find_port(QThread):
    port_list = pyqtSignal(list)

    def __init__(self):
        super(find_port, self).__init__()
        self.old_port = list(serial.tools.list_ports.comports())
        self.old_port_list = []
        for port in self.old_port:
            self.old_port_list.append(port[0])
        self.port_list.emit(self.old_port_list)

    def run(self):
        while True:
            new_port_list = list(serial.tools.list_ports.comports())
            if new_port_list != self.old_port:
                self.old_port = new_port_list
                self.old_port_list.clear()
                for port in new_port_list:
                    self.old_port_list.append(port[0])
                self.port_list.emit(self.old_port_list)
            time.sleep(1)

class read_data(QThread):
    Data = pyqtSignal(int)
    
    def __init__(self):
        super(read_data,self).__init__()
        self.port = None
        self.init_state = True

    def set_port(self, port):
        self.port = port
        if self.port:
            self.data = self.port.readline()

    def run(self):
        while(True):
            if self.port and self.port.isOpen():
                if self.init_state:
                    self.data = self.port.readline().decode().strip()
                self.data = self.port.readline().decode().strip()
                try:
                    self.Data.emit(int(self.data))
                except:
                    self.data = self.port.readline().decode().strip()
                    self.Data.emit(int(self.data))
                else:
                    pass
 
class MainWin(QMainWindow, Ui_untitled.Ui_Dialog):
    
    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        self.setupUi(self)
        self.all_data = []
        self.init_data = 0
        self.init_state = True
        self.max_state = False
        self.min_state = False
        self.max_frist = False
        self.min_frist = False
        self.old_diff = 0
        self.max_data = 0
        self.min_data = 0
        self.count = 0
        self.port_line = list(serial.tools.list_ports.comports())
        self.port_list = []
        for port in self.port_line:
            self.port_list.append(port[0])
        self.comboBox.addItems(self.port_list)
        self.comboBox_3.addItems(self.port_list)
        brud_list = ['9600', '115200']
        self.comboBox_2.addItems(brud_list)
        self.comboBox_4.addItems(brud_list)
        self.pushButton.clicked.connect(self.port_link)
        self.pushButton_2.clicked.connect(self.port_link2)
        self.port = serial.Serial()
        self.port2 = serial.Serial()
        self.thread1 = read_data()
        self.thread1.Data.connect(self.deal_data)
        self.thread1.start()
        self.thread2 = find_port()
        self.thread2.port_list.connect(self.change_port)
        self.thread2.start()
        pg.setConfigOptions(leftButtonPan=False)        
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.pw = pg.PlotWidget(self)
        self.plot_data = self.pw.plot(range(len(self.all_data)), self.all_data,pen='b', color='r')
        self.pw.setYRange(0,4000)
        self.gridLayout_3.addWidget(self.pw)


    def change_port(self, a):
        self.comboBox.clear()
        self.comboBox.addItems(a)
        self.comboBox_3.clear()
        self.comboBox_3.addItems(a)

    def port_link(self):
        box = QMessageBox()
        port = self.comboBox.currentText()
        brud = self.comboBox_2.currentText()
        try:
            self.port = serial.Serial(port, brud)
        except:
            box.setText('连接失败')
        else:
            self.thread1.set_port(self.port)
            box.setText("连接成功")
        box.exec_()

    def port_link2(self):
        box = QMessageBox()
        port = self.comboBox_3.currentText()
        brud = self.comboBox_4.currentText()
        try:
            self.port2 = serial.Serial(port, brud)
        except:
            box.setText('连接失败')
        else:
            box.setText("连接成功")
        box.exec_()

    def plot_view(self):
        self.plot_data.setData(range(len(self.all_data)), self.all_data, pen='b',color='r')
        pass

    def deal_data(self, data):
        if(len(self.all_data) == 5000):
            self.all_data[:-1] = self.all_data[1:]
            self.all_data[-1] = data
        else:
            self.all_data.append(data)
        self.plot_view()
        if self.init_state:
            self.count += 1
            if self.count == 11:
                self.init_data /= 10
                self.init_state = False
                self.textBrowser.append("基值：" + str(self.init_data))
            else:
                self.init_data += data
        else:
            diff = data - self.init_data
            if diff > 100:
                if not self.min_frist:
                    self.max_frist = True
                self.max_state = True
                if diff > self.old_diff:
                    self.max_data = data
            elif diff < -100:
                if not self.max_frist:
                    self.min_frist = True
                self.min_state = True
                if diff < self.old_diff:
                    self.min_data = data
            elif diff < 100 and diff > -100 and self.max_state and self.min_state:
                self.max_state = False
                self.min_state = False
                if self.max_frist:
                    info = 'a-' + str(self.max_data) + '-' + str(self.min_data) + '\n'
                    print(info.encode())
                    self.port2.write(info.encode())
                    self.textBrowser.append("记录：先大后小"+ "最大值：" + str(self.max_data) + "; 最小值：" + str(self.min_data))
                else:
                    info = 'b-' + str(self.max_data) + '-' + str(self.min_data) + '\n'
                    print(info.encode())
                    self.port2.write(info.encode())
                    self.textBrowser.append("记录：先小后大"+ "最大值：" + str(self.max_data) + "; 最小值：" + str(self.min_data))
                self.max_frist = False
                self.min_frist = False
            self.old_diff = diff


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    main = MainWin()
    main.show()
    sys.exit(app.exec_())