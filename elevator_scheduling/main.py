import sys
from PyQt5.QtWidgets import QApplication

from utils.constants import WINDOW_SIZE  
from utils.global_vars import init_global_vars
from elevator_thread import Elevator
from scheduler import OuterTaskController
from gui_mainwindow import UI_MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 初始化全局变量
    init_global_vars()

    # 开启任务调度器线程
    controller = OuterTaskController()
    controller.start()

    # 创建并启动电梯线程
    elevator_list = []
    from utils.constants import ELEVATOR_NUMS
    for i in range(ELEVATOR_NUMS):
        elevator_list.append(Elevator(i))

    # 启动所有电梯线程
    for elevator in elevator_list:
        elevator.start()

    # 创建并显示UI
    w = UI_MainWindow()
    sys.exit(app.exec_())