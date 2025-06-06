from PyQt5.QtCore import QMutex
from .constants import ELEVATOR_STATUS, ELEVATOR_NUMS, MOVING_STATUS

# 全局变量存储
elevator_status = []                    # 每组电梯的状态
elevator_move_status = []               # 每台电梯当前的扫描运行状态
elevator_current_floor = []                 # 每台电梯的当前楼层
remaining_up_task = []                    # 电梯在向上扫描的过程中，还需要处理的任务
remaining_down_task = []                  # 电梯在向下扫描的过程中，还需要处理的任务
open_button_clicked = []                # 每台电梯内部的开门键是否被按
close_button_clicked = []               # 每台电梯内部的关门键是否被按
door_open_status = []                   # 每台电梯开门的进度条 范围为0-1的浮点数
elevator_door = []                 # 每个电梯的电梯门
outer_request = []                  # 外部按钮请求的事件
mutex = QMutex()                        # mutex互斥锁

# 初始化全局变量
def init_global_vars():
    global elevator_status, elevator_move_status, elevator_current_floor
    global remaining_up_task, remaining_down_task
    global open_button_clicked, close_button_clicked, door_open_status
    
    # 清空 以防重复初始化
    elevator_status.clear()
    elevator_move_status.clear()
    elevator_current_floor.clear()
    remaining_up_task.clear()
    remaining_down_task.clear()
    open_button_clicked.clear()
    close_button_clicked.clear()
    door_open_status.clear()
    
    # 初始化
    for i in range(ELEVATOR_NUMS):
        elevator_status.append(ELEVATOR_STATUS.normal)  # 默认正常
        elevator_current_floor.append(1)  # 默认在1楼
        remaining_up_task.append([])  # 二维数组
        remaining_down_task.append([])  # 二维数组
        close_button_clicked.append(False)  # 默认关门键没按
        open_button_clicked.append(False)  # 默认关门键没按
        elevator_move_status.append(MOVING_STATUS.up)  # 默认向上
        door_open_status.append(0.0)  # 默认门没开 即进度为0.0