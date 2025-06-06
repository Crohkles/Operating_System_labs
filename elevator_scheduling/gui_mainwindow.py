import random
from functools import partial
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QTextEdit, 
    QVBoxLayout, QHBoxLayout, QLCDNumber, QLineEdit
)
from utils.constants import (
    WINDOW_SIZE, ELEVATOR_NUMS, FLOORS, ELEVATOR_STATUS, MOVING_STATUS, OUTER_TASK_STATUS
)
from utils.global_vars import (
    mutex, elevator_status, elevator_current_floor,
    remaining_up_task, remaining_down_task, open_button_clicked, 
    close_button_clicked, elevator_door,
    outer_request
)
from utils.requests import OUTER_BUTTON_GENERATE_TASK

# 可视化界面
class UI_MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.output = None
        # 初始化各类按钮和显示设备
        self.__elevator_lcds = []  # 电梯内的楼层显示屏
        self.__inner_floor_buttons = []  # 电梯内的楼层按钮
        self.__inner_open_door_buttons = []  # 电梯内的开门按钮
        self.__inner_close_door_buttons = []  # 电梯内的关门按钮
        self.__outer_up_buttons = []  # 每层楼中的上行按钮
        self.__outer_down_buttons = []  # 每层楼中的下行按钮
        self.__inner_fault_buttons = []  # 电梯内部的故障按钮
        self.timer = QTimer()  # 主定时器，用于UI更新
        self.door_timer = []  # 门的计时器列表
        self.setup_ui()  # 初始化UI界面

    # 设置UI
    def setup_ui(self):
        self.setWindowTitle("Elevator scheduling system_2353018_钱宝强")
        self.setGeometry(WINDOW_SIZE)

        h1 = QHBoxLayout()
        self.setLayout(h1)
        v1 = QVBoxLayout()
        h1.addLayout(v1)
        title1 = QLabel("电梯调度系统")
        title1.setStyleSheet("font-size:33px;""font-weight:bold;")

        v1.addWidget(title1)
        v1.setAlignment(title1, Qt.AlignHCenter)
        # 接收用户输入的产生任务的数量
        input_prompt = QLabel("请输入随机产生的任务数量:")
        v1.addWidget(input_prompt)
        self.get_input_number = QLineEdit()
        self.get_input_number.setStyleSheet("font-size:40px;""font-weight:bold;")
        v1.addWidget(self.get_input_number)
        generate_random_task_button = QPushButton()
        generate_random_task_button.setText("产生随机任务")
        generate_random_task_button.setStyleSheet("background-color :rgb(39, 113, 239);""border-style: solid;"
                             "border-width: 13px;"
                             "border-color:  rgb(39, 113, 239);"
                             "border-radius:7px;"
                             "color:white;")
        generate_random_task_button.clicked.connect(self.__generate_tasks)
        v1.addWidget(generate_random_task_button)

        # 输出电梯信息
        self.output = QTextEdit()
        self.output.setText("系统运行信息：\n")
        v1.addWidget(self.output)
        h2 = QHBoxLayout()
        h1.addLayout(h2)

        # 对每一个电梯都进行相同的设置
        for i in range(ELEVATOR_NUMS):
            v2 = QVBoxLayout()  # 竖直布局
            h2.addLayout(v2)

            # 电梯上方的LCD显示屏
            floor_display = QLCDNumber()
            floor_display.setNumDigits(2)
            floor_display.setSegmentStyle(QLCDNumber.Flat)
            floor_display.setStyleSheet("color: rgb(0, 0, 0);")
            floor_display.setFixedSize(100, 50)
            self.__elevator_lcds.append(floor_display)
            v2.addWidget(floor_display)

            # 添加文字提示
            Text = QLabel("电梯" + str(i + 1) + "内部按钮", self)
            v2.addWidget(Text)

            # 故障按钮
            fault_button = QPushButton("故障")
            fault_button.setFixedSize(100, 50)
            fault_button.clicked.connect(partial(self.__inner_fault_button_clicked, i))
            self.__inner_fault_buttons.append(fault_button)
            v2.addWidget(fault_button)

            # 电梯内部按钮
            self.__inner_floor_buttons.append([])
            elevator_button_layout = QHBoxLayout()
            # 创建电梯按钮
            button_group1 = QVBoxLayout()  # 前10层按钮
            for j in range(1, int(FLOORS / 2 + 1)):
                button = QPushButton(str(int(FLOORS / 2 + 1 - j)))
                button.setFixedSize(25, 25)

                # 绑定点击每一个楼层的按钮后的事件
                button.clicked.connect(partial(self.__inner_num_button_clicked, i, int(FLOORS / 2 + 1 - j)))
                button.setStyleSheet("background-color : rgb(255,255,255);""border-style: solid;"
                                     "border-width: 1px;"
                                     "border-color:  rgb(100,200,160);"
                                     "border-radius:3px;"
                                     "color:black;")
                self.__inner_floor_buttons[i].append(button)
                button_group1.addWidget(button)
            button_group1.setSpacing(7)

            # 开门按钮
            open_button = QPushButton("开")
            open_button.setFixedSize(25, 25)
            open_button.clicked.connect(partial(self.__inner_open_button_clicked, i))
            self.__inner_open_door_buttons.append(open_button)
            open_button.setStyleSheet("background-color :rgb(237,220,195);""border-style: solid;"
                                      "border-width: 2px;"
                                      "border-color: rgb(192, 192, 192);"
                                      "border-radius:10px;"
                                      "color:black;")
            button_group1.addWidget(open_button)

            button_group2 = QVBoxLayout()  # 后10层按钮
            for j in range(1, int(FLOORS / 2 + 1)):
                button = QPushButton(str(FLOORS + 1 - j))
                button.setFixedSize(25, 25)

                # 绑定点击每一个楼层的按钮后的事件
                button.clicked.connect(partial(self.__inner_num_button_clicked, i, FLOORS + 1 - j))
                button.setStyleSheet("background-color : rgb(255,255,255);""border-style: solid;"
                                     "border-width: 1px;"
                                     "border-color:  rgb(100,200,160);"
                                     "border-radius:3px;"
                                     "color:black;")
                self.__inner_floor_buttons[i].append(button)
                button_group2.addWidget(button)
            button_group2.setSpacing(7)


            # 关门按钮
            close_button = QPushButton("关")
            close_button.setFixedSize(25, 25)
            close_button.clicked.connect(partial(self.__inner_close_button_clicked, i))
            close_button.setStyleSheet("background-color :rgb(237,220,195);""border-style: solid;"
                                       "border-width: 2px;"
                                       "border-color: rgb(192, 192, 192);"
                                       "border-radius:10px;"
                                       "color:black;")
            self.__inner_close_door_buttons.append(close_button)
            button_group2.addWidget(close_button)

            button_group1_widget = QWidget()
            button_group1_widget.setLayout(button_group1)
            elevator_button_layout.addWidget(button_group1_widget)
            elevator_button_layout

            button_group2_widget = QWidget()
            button_group2_widget.setLayout(button_group2)
            elevator_button_layout.addWidget(button_group2_widget)

            elevator_button_layout_widget = QWidget()
            elevator_button_layout_widget.setLayout(elevator_button_layout)
            v2.addWidget(elevator_button_layout_widget)
            # 接下来给v2添加门
            door = []
            door_container = QWidget()
            door_container.setFixedSize(80,30)

            # 创建四个充当门的按钮的水平布局
            hbox1 = QHBoxLayout(door_container)
            hbox1.setContentsMargins(0,0,0,0)
            hbox1.setSpacing(0)

            for d in range(4):
                DoorTimer = QTimer()
                self.door_timer.append(DoorTimer)
                button = QPushButton('', self)
                button.setFixedSize(20, 20)
                door.append(button)
                hbox1.addWidget(button)
            
            door[0].setStyleSheet('background-color: transparent;')
            door[1].setStyleSheet('background-color: black;')
            door[2].setStyleSheet('background-color: black;')
            door[3].setStyleSheet('background-color: transparent;')
            elevator_door.append(door)

            v2.addWidget(door_container)

            Text1 = QLabel("电梯" + str(i + 1) + "的门", self)
            v2.addWidget(Text1)

            # 设置布局中的组件水平居中
            v2.setAlignment(floor_display, Qt.AlignHCenter)
            v2.setAlignment(fault_button, Qt.AlignHCenter)
            v2.setAlignment(elevator_button_layout_widget, Qt.AlignHCenter)
            v2.setAlignment(door_container, Qt.AlignHCenter)
            v2.setAlignment(Text, Qt.AlignHCenter)
            v2.setAlignment(Text1, Qt.AlignHCenter)

        v3 = QVBoxLayout()
        h1.addLayout(v3)

        outer_title = QLabel("电梯外按钮")
        v3.addWidget(outer_title)
        v3.setAlignment(outer_title, Qt.AlignHCenter)

        for i in range(FLOORS):  # 对于每一层楼
            h4 = QHBoxLayout()  # 创建一个水平布局
            v3.addLayout(h4)
            label = QLabel(str(FLOORS - i))
            h4.addWidget(label)
            if i != 0:
                # 给2楼到顶楼放置上行按钮
                up_button = QPushButton("▲")
                up_button.setFixedSize(25, 25)
                up_button.clicked.connect(
                    partial(self.__outer_button_clicked, FLOORS - i, MOVING_STATUS.up))
                self.__outer_up_buttons.append(up_button)  # 从顶楼往下一楼开始..
                h4.addWidget(up_button)

            if i != FLOORS - 1:
                # 给1楼到顶楼往下一楼放置下行按钮
                down_button = QPushButton("▼")
                down_button.setFixedSize(25, 25)
                down_button.clicked.connect(
                    partial(self.__outer_button_clicked, FLOORS - i, MOVING_STATUS.down))
                self.__outer_down_buttons.append(down_button)  # 从顶楼开始..到2楼
                h4.addWidget(down_button)

        # 设置定时
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.update)
        self.timer.start()

        self.show()


    # 开门
    def open_the_door(self, elevator_id, choice):
        elevator_door[elevator_id][0].setStyleSheet('background-color: gray;')
        elevator_door[elevator_id][1].setStyleSheet('background-color: black; margin-right: 20px;')
        elevator_door[elevator_id][2].setStyleSheet('background-color: black; margin-left: 20px;')
        elevator_door[elevator_id][3].setStyleSheet('background-color: gray;')

        if choice:
            self.door_timer[elevator_id].setInterval(4000)
            self.door_timer[elevator_id].timeout.connect(lambda: self.close_1s(elevator_id))
            self.door_timer[elevator_id].start()
    # 关门
    def close_the_door(self, elevator_id):
            elevator_door[elevator_id][0].setStyleSheet('background-color: transparent;')
            elevator_door[elevator_id][1].setStyleSheet('background-color: black; margin: 0px;')
            elevator_door[elevator_id][2].setStyleSheet('background-color: black; margin: 0px;')
            elevator_door[elevator_id][3].setStyleSheet('background-color: transparent;')

    # 产生随机任务
    def __generate_tasks(self):
        for i in range(int(self.get_input_number.text()) if self.get_input_number.text() else 0):
            if random.randint(0, 100) < 50:  # 50% 产生外部任务
                target = random.randint(1, FLOORS)
                if target == 1:  # 1楼只能向上
                    self.__outer_button_clicked(target, MOVING_STATUS.up)
                elif target == FLOORS:  # 顶楼只能向下
                    self.__outer_button_clicked(target, MOVING_STATUS.down)
                else:  # 其余则随机指派方向
                    self.__outer_button_clicked(target,
                                                          random.choice([MOVING_STATUS.up, MOVING_STATUS.down]))
            else:  # 产生内部任务
                self.__inner_num_button_clicked(random.randint(0, ELEVATOR_NUMS - 1), random.randint(1, FLOORS))

 # 如果按的是电梯内部的数字按钮，则执行下面的函数进行处理
    def __inner_num_button_clicked(self, elevator_id, floor):
        mutex.lock()
        # 如果电梯出现故障
        if elevator_status[elevator_id] == ELEVATOR_STATUS.break_down:
            self.output.append(str(elevator_id) + "号电梯出现故障 正在维修!")
            mutex.unlock()
            return

        # 相同楼层不处理
        if floor == elevator_current_floor[elevator_id]:
            mutex.unlock()
            return

        if elevator_status[elevator_id] != ELEVATOR_STATUS.break_down:
            if floor > elevator_current_floor[elevator_id] and floor not in remaining_up_task[elevator_id]:
                remaining_up_task[elevator_id].append(floor)  # 将该楼添加到上行的目标楼层中
                remaining_up_task[elevator_id].sort()  # 按照从小到大的顺序排序
            elif floor < elevator_current_floor[elevator_id] and floor not in remaining_down_task[elevator_id]:
                remaining_down_task[elevator_id].append(floor)
                remaining_down_task[elevator_id].sort(reverse=True)  # 降序排序

            mutex.unlock()
            index = 0
            if floor <= FLOORS / 2:
                index = int(FLOORS / 2 - floor)
            else:
                index = int(30 - floor)
            # 将当前楼层按钮的颜色改变
            self.__inner_floor_buttons[elevator_id][index].setStyleSheet(
                "background-color : rgb(192, 192, 192);")
            self.output.append(str(elevator_id) + "号电梯" + "用户需要去" + str(floor) + "楼")

    # 处理电梯外部每层楼的按钮点击事件
    def __outer_button_clicked(self, floor, move_state):
        mutex.lock()
        # 排除故障电梯
        all_fault_flag = True
        for state in elevator_status:
            if state != ELEVATOR_STATUS.break_down:
                all_fault_flag = False

        if all_fault_flag:
            self.output.append("所有电梯均已故障！")
            mutex.unlock()
            return

        task = OUTER_BUTTON_GENERATE_TASK(floor, move_state)

        if task not in outer_request:
            outer_request.append(task)

            if move_state == MOVING_STATUS.up:
                self.__outer_up_buttons[FLOORS - floor - 1].setStyleSheet("background-color : yellow")
                self.output.append(str(floor) + "楼的用户有上楼的需求～")

            elif move_state == MOVING_STATUS.down:
                self.__outer_down_buttons[FLOORS - floor].setStyleSheet("background-color : yellow")
                self.output.append(str(floor) + "楼的用户下楼的需求～")
        
        mutex.unlock()
    
    # 处理指定电梯的开门请求
    def __inner_open_button_clicked(self, elevator_id):
        mutex.lock()
        # 电梯故障
        if elevator_status[elevator_id] == ELEVATOR_STATUS.break_down:
            self.output.append(str(elevator_id) + "号电梯出现故障 正在维修!")
            mutex.unlock()
            return
        # 电梯正在关门或者正在开门
        if elevator_status[elevator_id] == ELEVATOR_STATUS.door_closing or elevator_status[
            elevator_id] == ELEVATOR_STATUS.door_open:
            open_button_clicked[elevator_id] = True
            close_button_clicked[elevator_id] = False
        mutex.unlock()
        # 开门按钮

        self.__inner_open_door_buttons[elevator_id].setStyleSheet("background-color : rgb(192, 192, 192)")
        self.output.append(str(elevator_id) + "电梯开门!")
        # 调用开门函数
        self.open_the_door(elevator_id, 1)

    def close_1s(self, elevator_id):
        print(999)
        # 调用关门函数
        self.close_the_door(elevator_id)
        # 关闭定时器
        self.door_timer[elevator_id] = self.sender()  # 获取信号发送者
        self.door_timer[elevator_id].stop()

    # 处理电梯关门
    def __inner_close_button_clicked(self, elevator_id):
        mutex.lock()
        if elevator_status[elevator_id] == ELEVATOR_STATUS.break_down:
            self.output.append(str(elevator_id) + "号电梯出现故障 正在维修!")
            mutex.unlock()
            return

        if elevator_status[elevator_id] == ELEVATOR_STATUS.door_openning or elevator_status[
            elevator_id] == ELEVATOR_STATUS.door_open:
            close_button_clicked[elevator_id] = True
            open_button_clicked[elevator_id] = False
        mutex.unlock()
        # 关门按钮
        self.__inner_close_door_buttons[elevator_id].setStyleSheet("background-color : rgb(192, 192, 192)")
        self.output.append(str(elevator_id) + "电梯关门!")
        self.close_the_door(elevator_id)

    # 处理电梯故障按钮
    def __inner_fault_button_clicked(self, elevator_id):
        mutex.lock()
        if elevator_status[elevator_id] != ELEVATOR_STATUS.break_down:
            elevator_status[elevator_id] = ELEVATOR_STATUS.break_down
            mutex.unlock()
            self.__inner_fault_buttons[elevator_id].setStyleSheet("background-color : gray;")
            for button in self.__inner_floor_buttons[elevator_id]:
                button.setStyleSheet("background-color :gray;""border-radius:10px;")
            self.__inner_open_door_buttons[elevator_id].setStyleSheet("background-color : gray;")
            self.__inner_close_door_buttons[elevator_id].setStyleSheet("background-color : gray;")

            self.output.append(str(elevator_id) + "电梯故障!")
        # 如果电梯本来就有故障，则再点一下故障就会消失
        else:
            elevator_status[elevator_id] = ELEVATOR_STATUS.normal
            mutex.unlock()

            self.__inner_fault_buttons[elevator_id].setStyleSheet("background-color : None")
            for button in self.__inner_floor_buttons[elevator_id]:
                button.setStyleSheet("background-color : rgb(255,255,255);""border-style: solid;"
                                     "border-width: 1px;"
                                     "border-color:  rgb(100,200,160);"
                                     "border-radius:3px;"
                                     "color:black;")
            self.__inner_open_door_buttons[elevator_id].setStyleSheet("background-color : None;")
            self.__inner_close_door_buttons[elevator_id].setStyleSheet("background-color : None;")
            self.output.append(str(elevator_id) + "电梯正常!")

   

    # 实时更新界面
    def update(self):
        mutex.lock()
        for i in range(ELEVATOR_NUMS):
            # 实时更新楼层
            if elevator_status[i] == ELEVATOR_STATUS.moving_up:
                self.__elevator_lcds[i].display(str(elevator_current_floor[i]))
                self.close_the_door(i)
            elif elevator_status[i] == ELEVATOR_STATUS.moving_down:
                self.__elevator_lcds[i].display(str(elevator_current_floor[i]))
                self.close_the_door(i)
            else:
                self.__elevator_lcds[i].display(elevator_current_floor[i])

            # 实时更新开关门按钮
            if not open_button_clicked[i] and not elevator_status[i] == ELEVATOR_STATUS.break_down:
                self.__inner_open_door_buttons[i].setStyleSheet(
                    "background-color :rgb(237,220,195);""border-style: solid;"
                    "border-width: 2px;"
                    "border-color: rgb(192, 192, 192);"
                    "border-radius:10px;"
                    "color:black;")

            if not close_button_clicked[i] and not elevator_status[i] == ELEVATOR_STATUS.break_down:
                self.__inner_close_door_buttons[i].setStyleSheet(
                    "background-color :rgb(237,220,195);""border-style: solid;"
                    "border-width: 2px;"
                    "border-color: rgb(192, 192, 192);"
                    "border-radius:10px;"
                    "color:black;")

            if elevator_status[i] in [ELEVATOR_STATUS.door_openning, ELEVATOR_STATUS.door_open,
                                      ELEVATOR_STATUS.door_closing]:
                index = 0
                if elevator_current_floor[i] <= FLOORS / 2:
                    index = int(FLOORS / 2 - elevator_current_floor[i])
                else:
                    index = int(30 - elevator_current_floor[i])
                self.__inner_floor_buttons[i][index].setStyleSheet(
                    "background-color : rgb(255,255,255);""border-style: solid;"
                    "border-width: 1px;"
                    "border-color:  rgb(100,200,160);"
                    "border-radius:3px;"
                    "color:black;"
                )

            if elevator_status[i] == ELEVATOR_STATUS.door_openning:
                self.open_the_door(i, 0)
            else:
                self.close_the_door(i)

        mutex.unlock()
        # 对外部来说，遍历任务，找出未完成的设为红色，其他设为默认none
        for button in self.__outer_up_buttons:
            button.setStyleSheet("background-color : None")

        for button in self.__outer_down_buttons:
            button.setStyleSheet("background-color : None")

        mutex.lock()
        for outer_task in outer_request:
            # 如果外部的事件还没有被完全处理好，则将对应的按钮的背景变成红色的
            if outer_task.state != OUTER_TASK_STATUS.finished:
                if outer_task.move_state == MOVING_STATUS.up:
                    self.__outer_up_buttons[FLOORS - outer_task.target - 1].setStyleSheet(
                        "background-color : rgb(192, 192, 192);")
                elif outer_task.move_state == MOVING_STATUS.down:
                    self.__outer_down_buttons[FLOORS - outer_task.target].setStyleSheet(
                        "background-color : rgb(192, 192, 192);")

        mutex.unlock()