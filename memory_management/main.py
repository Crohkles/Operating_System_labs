#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer
from ui.main_window import Ui_MainWindow
from utils.allocator import Allocator
from utils.constants import AllocatingAlgorithm


class MainWindow(QMainWindow, Ui_MainWindow):
    """主窗口类，整合 UI 和逻辑"""
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        # 初始化分配器
        self.allocator = Allocator(640)  # 640KB 内存
        
        # 演示序列
        self.demo_sequence = [
            ('allocate', 1, 130),   # 作业1申请130K
            ('allocate', 2, 60),    # 作业2申请60K
            ('allocate', 3, 100),   # 作业3申请100K
            ('free', 2, 0),         # 作业2释放60K
            ('allocate', 4, 200),   # 作业4申请200K
            ('free', 3, 0),         # 作业3释放100K
            ('free', 1, 0),         # 作业1释放130K
            ('allocate', 5, 140),   # 作业5申请140K
            ('allocate', 6, 60),    # 作业6申请60K
            ('allocate', 7, 50),    # 作业7申请50K
            ('free', 6, 0),         # 作业6释放60K
        ]
        
        self.current_step = 0
        self.is_running = False
        
        # 连接信号和槽
        self.start_trigger.clicked.connect(self.start_demo)
        self.clear_trigger.clicked.connect(self.clear_demo)
        
        # 定时器用于演示
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_step)
        
        # 初始化内存视图
        self.update_memory_view()
        
    def start_demo(self):
        """开始演示"""
        if self.is_running:
            return
            
        if self.current_step >= len(self.demo_sequence):
            self.current_step = 0
            self.allocator = Allocator(640)
            
        self.is_running = True
        self.start_trigger.setText("演示进行中...")
        self.start_trigger.setEnabled(False)
        
        # 启动定时器，每2秒执行一步
        self.timer.start(2000)
        
    def clear_demo(self):
        self.timer.stop()
        self.is_running = False
        self.current_step = 0
        
        # 重置分配器
        self.allocator = Allocator(640)
        
        # 重置UI
        self.start_trigger.setText("开始演示")
        self.start_trigger.setEnabled(True)
        self.textEdit.clear()
        
        # 更新内存视图
        self.update_memory_view()
        
    def next_step(self):
        """执行下一步演示"""
        if self.current_step >= len(self.demo_sequence):
            # 演示结束
            self.timer.stop()
            self.is_running = False
            self.start_trigger.setText("开始演示")
            self.start_trigger.setEnabled(True)
            self.append_log("演示完成！")
            return
            
        # 获取当前算法
        algorithm = AllocatingAlgorithm.FIRST_FIT if self.first_fit_button.isChecked() else AllocatingAlgorithm.BEST_FIT
        
        # 执行当前步骤
        action, pid, size = self.demo_sequence[self.current_step]
        
        if action == 'allocate':
            success = self.allocator.allocate(pid, size, algorithm)
            if success:
                self.append_log(f"作业{pid} 成功申请 {size}K 内存")
            else:
                self.append_log(f"作业{pid} 申请 {size}K 内存失败 - 内存不足")
        elif action == 'free':
            success = self.allocator.free(pid)
            if success:
                self.append_log(f"作业{pid} 成功释放内存")
            else:
                self.append_log(f"作业{pid} 释放内存失败 - 进程不存在")
                
        # 更新内存视图
        self.update_memory_view()
        
        self.current_step += 1
        
    def append_log(self, message):
        self.textEdit.append(message)
        
    def update_memory_view(self):
        status = self.allocator.get_memory_status()
        
        # 更新内存视图
        self.widget.set_memory_status(
            status['allocated_blocks'],
            status['free_blocks'],
            status['total_memory']
        )
        

def main():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 启动应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()