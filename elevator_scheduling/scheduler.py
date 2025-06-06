from PyQt5.QtCore import QThread
from utils.constants import FLOORS, ELEVATOR_NUMS, ELEVATOR_STATUS, OUTER_TASK_STATUS, MOVING_STATUS
from utils.global_vars import (
    mutex, elevator_status, elevator_current_floor, elevator_move_status,
    remaining_up_task, remaining_down_task, outer_request
)

# 用于处理外面按钮产生的任务，并选择合适的电梯，将任务添加到对应的任务列表中
class OuterTaskController(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            mutex.lock()
            self.assign_tasks()
            self.cleanup_finished_tasks()
            mutex.unlock()

    def append_task(self, elevator_id, outer_task):
        if outer_task.move_state == MOVING_STATUS.up:
            remaining_up_task[elevator_id].append(outer_task.target)
            remaining_up_task[elevator_id].sort()
        else:
            remaining_down_task[elevator_id].append(outer_task.target)
            remaining_down_task[elevator_id].sort(reverse=True)

    def assign_task_to_elevator(self, outer_task, elevator_id):
        if elevator_current_floor[elevator_id] == outer_task.target:
            self.append_task(elevator_id, outer_task)
        elif elevator_current_floor[elevator_id] < outer_task.target:
            remaining_up_task[elevator_id].append(outer_task.target)
            remaining_up_task[elevator_id].sort()
        elif elevator_current_floor[elevator_id] > outer_task.target:
            remaining_down_task[elevator_id].append(outer_task.target)
            remaining_down_task[elevator_id].sort(reverse=True)
        outer_task.state = OUTER_TASK_STATUS.waiting
    
    def find_closest_elevator(self, outer_task):
        min_cost = float('inf')
        target_id = -1
        for i in range(ELEVATOR_NUMS):
            if elevator_status[i] == ELEVATOR_STATUS.break_down:
                continue
            cost = self.calculate_cost(i, outer_task) 
            if cost < min_cost:
                min_cost = cost
                target_id = i
        return target_id

    def calculate_cost(self, elevator_id, outer_task):
        origin = elevator_current_floor[elevator_id] + (1 if elevator_status[elevator_id] == ELEVATOR_STATUS.moving_up else -1)
        targets = remaining_up_task[elevator_id] if elevator_move_status[elevator_id] == MOVING_STATUS.up else remaining_down_task[elevator_id]
        if not targets:
            return abs(origin - outer_task.target)
        if elevator_move_status[elevator_id] == outer_task.move_state and \
                ((outer_task.move_state == MOVING_STATUS.up and outer_task.target >= origin) or
                 (outer_task.move_state == MOVING_STATUS.down and outer_task.target <= origin)):
            return abs(origin - outer_task.target)
        return abs(origin - targets[-1]) + abs(outer_task.target - targets[-1])
    
    def assign_tasks(self):
        global outer_request
        for outer_task in outer_request:
            if outer_task.state == OUTER_TASK_STATUS.unassigned:
                target_id = self.find_closest_elevator(outer_task)
                if target_id != -1:
                    self.assign_task_to_elevator(outer_task, target_id)

    def cleanup_finished_tasks(self):
        global outer_request
        outer_request[:] = [task for task in outer_request if task.state != OUTER_TASK_STATUS.finished]