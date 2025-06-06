from .constants import OUTER_TASK_STATUS

# 外部按钮按下产生的任务描述
class OUTER_BUTTON_GENERATE_TASK:
    def __init__(self, target, move_state, state=OUTER_TASK_STATUS.unassigned):
        self.target = target            # 目标楼层
        self.move_state = move_state    # 需要的电梯运行方向
        self.state = state              # 是否完成（默认未完成）
        
    def __eq__(self, other):
        if not isinstance(other, OUTER_BUTTON_GENERATE_TASK):
            return False
        return self.target == other.target and self.move_state == other.move_state