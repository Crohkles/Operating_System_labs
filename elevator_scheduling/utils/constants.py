from enum import Enum
from PyQt5.QtCore import QRect
# 窗口大小设置
WINDOW_SIZE = QRect(150, 50, 600, 450)

# 全局变量定义
ELEVATOR_NUMS = 5                       # 电梯数量
FLOORS = 20                             # 电梯层数
TIME_ATOMIC_MOVE = 800                  # 移动一层所需时间
TIME_DOOR_OP = 500                 # 打开一扇门所需时间
TIME_STAY_OPEN = 700                   # 门打开后维持的时间

# 电梯的扫描移动状态
class MOVING_STATUS(Enum):
    up = 1                              # 电梯在向上扫描的状态中
    down = -1                           # 电梯在向下扫描的状态中

# 电梯状态
class ELEVATOR_STATUS(Enum):
    normal = 0                          # 表示电梯状态是正常的
    break_down = 1                      # 表示电梯此时状态是故障的状态
    door_openning = 2                    # 表示电梯正在开门
    door_open = 3                       # 表示电梯门已经打开
    door_closing = 4                    # 表示电梯正在关门
    moving_up = 5                       # 表示电梯正在上行
    moving_down = 6                     # 表示电梯正在下行

# 外部按钮可能处在的状态
class OUTER_TASK_STATUS(Enum):
    unassigned = 1                      # 任务未被分配
    waiting = 2                         # 任务已被分配，等待被处理
    finished = 3                        # 任务已经完成