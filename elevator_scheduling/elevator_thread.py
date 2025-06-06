from PyQt5.QtCore import QThread
from utils.constants import ELEVATOR_STATUS, MOVING_STATUS, TIME_ATOMIC_MOVE,\
    OUTER_TASK_STATUS
from utils.global_vars import (
    mutex, elevator_status, elevator_current_floor, elevator_move_status,
    remaining_up_task, remaining_down_task, open_button_clicked, close_button_clicked,
    door_open_status, outer_request
)

# 处理电梯的操作
class Elevator(QThread):
    def __init__(self, elevator_id):
        super().__init__()                  # 父类构造函数
        self.elevator_id = elevator_id      # 电梯编号
        self.rest_time = 10                 # 时间间隔

    def update_elevator_status(self, move_state):
        if move_state == MOVING_STATUS.up:
            elevator_status[self.elevator_id] = ELEVATOR_STATUS.moving_up
        elif move_state == MOVING_STATUS.down:
            elevator_status[self.elevator_id] = ELEVATOR_STATUS.moving_down

    # 检查故障 若故障返回False 若正常返回True
    def check_for_faults(self):
        slept_time = 0
        while slept_time != TIME_ATOMIC_MOVE:
            mutex.unlock()
            self.msleep(self.rest_time)
            slept_time += self.rest_time
            mutex.lock()
            if elevator_status[self.elevator_id] == ELEVATOR_STATUS.break_down:
                self.handle_fault()
                return False
        return True

    def update_current_floor(self, move_state):
        if move_state == MOVING_STATUS.up:
            direction = 1
        elif move_state == MOVING_STATUS.down:
            direction = -1
        else:
            direction = 0
        elevator_current_floor[self.elevator_id] += direction
        elevator_status[self.elevator_id] = ELEVATOR_STATUS.normal

    def atomic_move(self, move_state):
        self.update_elevator_status(move_state)
        # 故障检查和处理(若发现故障, check_for_faults内会自行调用handle_fault)
        if not self.check_for_faults():
            return
        self.update_current_floor(move_state)

    # 一次门的操作 包括开门和关门
    def door_operation(self):
        from utils.constants import TIME_DOOR_OP, TIME_STAY_OPEN
        
        opening_time = 0.0  # 记录门打开所需的累积时间
        open_time = 0.0     # 记录门保持开启的累积时间
        elevator_status[self.elevator_id] = ELEVATOR_STATUS.door_openning  # 初始设置为门正在打开

        while True:
            # 检查电梯是否处于故障状态
            if elevator_status[self.elevator_id] == ELEVATOR_STATUS.break_down:
                self.handle_fault()  # 处理故障
                break

            # 处理开门请求
            if open_button_clicked[self.elevator_id]:
                if elevator_status[self.elevator_id] == ELEVATOR_STATUS.door_closing:
                    elevator_status[self.elevator_id] = ELEVATOR_STATUS.door_openning
                if elevator_status[self.elevator_id] == ELEVATOR_STATUS.door_open:
                    open_time = 0

                # 重置开门按钮状态
                open_button_clicked[self.elevator_id] = False

            # 处理关门请求
            if close_button_clicked[self.elevator_id]:
                elevator_status[self.elevator_id] = ELEVATOR_STATUS.door_closing  # 设置为门正在关闭
                open_time = 0  # 重置门开启时间

                close_button_clicked[self.elevator_id] = False

            # 开门过程的逻辑
            if elevator_status[self.elevator_id] == ELEVATOR_STATUS.door_openning:
                mutex.unlock()  # 允许其他线程运行
                self.msleep(self.rest_time)  # 等待一个时间段
                mutex.lock()  # 重新锁定
                opening_time += self.rest_time
                door_open_status[self.elevator_id] = opening_time / TIME_DOOR_OP  # 更新打开进度

                # 如果完全打开（根据openning_time)
                if opening_time >= TIME_DOOR_OP:
                    elevator_status[self.elevator_id] = ELEVATOR_STATUS.door_open

            # 门已经完全开启的处理
            elif elevator_status[self.elevator_id] == ELEVATOR_STATUS.door_open:
                mutex.unlock()
                self.msleep(self.rest_time)
                mutex.lock()
                open_time += self.rest_time
                if open_time >= TIME_STAY_OPEN:
                    elevator_status[self.elevator_id] = ELEVATOR_STATUS.door_closing  # 时间到，开始关门

            # 关门过程的逻辑
            elif elevator_status[self.elevator_id] == ELEVATOR_STATUS.door_closing:
                mutex.unlock()
                self.msleep(self.rest_time)
                mutex.lock()
                opening_time -= self.rest_time
                door_open_status[self.elevator_id] = opening_time / TIME_DOOR_OP  # 更新关闭进度

                # 门完全关闭
                if opening_time <= 0:
                    elevator_status[self.elevator_id] = ELEVATOR_STATUS.normal
                    break

    # 当故障发生时 清除原先的所有任务
    def handle_fault(self):
        from utils.constants import OUTER_TASK_STATUS
        
        elevator_status[self.elevator_id] = ELEVATOR_STATUS.break_down
        door_open_status[self.elevator_id] = 0.0
        open_button_clicked[self.elevator_id] = False
        close_button_clicked[self.elevator_id] = False
        elevator_status[self.elevator_id] = ELEVATOR_STATUS.break_down
        # 遍历所有外部按钮任务
        for outer_task in outer_request:
            # 检查任务是否处于等待状态
            if outer_task.state == OUTER_TASK_STATUS.waiting:
                # 如果任务目标楼层在上行或下行任务列表中，将其状态设置为未分配
                if outer_task.target in remaining_up_task[self.elevator_id] or outer_task.target in remaining_down_task[self.elevator_id]:
                    outer_task.state = OUTER_TASK_STATUS.unassigned  # 使这些任务可被重新分配
        # 清空当前电梯的上行任务列表
        remaining_up_task[self.elevator_id] = []
        # 清空当前电梯的下行任务列表
        remaining_down_task[self.elevator_id] = []

    def run(self):
        while True:
            mutex.lock()
            # 检查电梯是否处于故障状态
            if elevator_status[self.elevator_id] == ELEVATOR_STATUS.break_down:
                self.handle_fault()
                mutex.unlock()
                continue

            # 移动状态为up时
            if elevator_move_status[self.elevator_id] == MOVING_STATUS.up:
                # 检查处理上行任务
                if remaining_up_task[self.elevator_id]:
                    next_floor = remaining_up_task[self.elevator_id][0]
                    if next_floor == elevator_current_floor[self.elevator_id]:
                        self.door_operation()  # 开关门
                        if remaining_up_task[self.elevator_id]:
                            remaining_up_task[self.elevator_id].pop(0)
                            for outer_task in outer_request:
                                if outer_task.target == elevator_current_floor[self.elevator_id]:
                                    outer_task.state = OUTER_TASK_STATUS.finished
                    elif next_floor > elevator_current_floor[self.elevator_id]:
                        self.atomic_move(MOVING_STATUS.up)

                # 如果没有上行任务但有下行任务，更改移动状态为下行
                elif not remaining_up_task[self.elevator_id] and remaining_down_task[self.elevator_id]:
                    elevator_move_status[self.elevator_id] = MOVING_STATUS.down

            # 处理向下移动状态
            elif elevator_move_status[self.elevator_id] == MOVING_STATUS.down:
                if remaining_down_task[self.elevator_id]:
                    next_floor = remaining_down_task[self.elevator_id][0]
                    if next_floor == elevator_current_floor[self.elevator_id]:
                        self.door_operation()  # 开关门
                        remaining_down_task[self.elevator_id].pop(0)
                        for outer_task in outer_request:
                            if outer_task.target == elevator_current_floor[self.elevator_id]:
                                outer_task.state = OUTER_TASK_STATUS.finished
                    elif next_floor < elevator_current_floor[self.elevator_id]:
                        self.atomic_move(MOVING_STATUS.down)

                # 如果没有下行任务但有上行任务，更改移动状态为上行
                elif not remaining_down_task[self.elevator_id] and remaining_up_task[self.elevator_id]:
                    elevator_move_status[self.elevator_id] = MOVING_STATUS.up

            mutex.unlock()