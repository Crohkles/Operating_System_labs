from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
from PyQt5.QtWidgets import QWidget


class MemoryView(QWidget):
    """内存可视化组件，用于显示动态分区内存分配状态"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 内存相关属性
        self.memory_size = 640  # 总内存大小（KB）
        self.allocated_blocks = {}  # 已分配的内存块 {pid: (start, size)}
        self.free_blocks = [(0, 640)]  # 空闲内存块 [(start, size), ...]
          # 界面相关属性
        self.margin = 10  # 边距
        self.block_height = 60  # 每个内存块的高度（增加以便显示更多文字）
        self.font_size = 9
        
        # 颜色配置
        self.allocated_color = QColor(255, 102, 102)  # 红色 - 已分配
        self.free_color = QColor(102, 255, 102)       # 绿色 - 空闲
        self.border_color = QColor(0, 0, 0)           # 黑色 - 边框
        
        # 设置最小大小（增加高度以适应更高的方块）
        self.setMinimumSize(381, 200)
        
    def set_memory_status(self, allocated_blocks, free_blocks, total_size):
        """
        更新内存状态
        
        Args:
            allocated_blocks: dict {pid: (start, size)}
            free_blocks: list [(start, size), ...]
            total_size: int 总内存大小
        """
        self.allocated_blocks = allocated_blocks
        self.free_blocks = free_blocks
        self.memory_size = total_size
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        """重写绘制事件，绘制内存块"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取可绘制区域
        rect = self.rect()
        draw_width = rect.width() - 2 * self.margin
        draw_height = rect.height() - 2 * self.margin
        
        if draw_width <= 0 or draw_height <= 0:
            return
            
        # 设置字体
        font = QFont()
        font.setPointSize(self.font_size)
        painter.setFont(font)
        
        # 计算缩放比例（内存大小到像素的转换）
        scale = draw_width / self.memory_size if self.memory_size > 0 else 1
        
        # 创建一个包含所有内存块信息的列表，按起始地址排序
        all_blocks = []
        
        # 添加已分配的块
        for pid, (start, size) in self.allocated_blocks.items():
            all_blocks.append({
                'start': start,
                'size': size,
                'type': 'allocated',
                'pid': pid
            })
            
        # 添加空闲块
        for start, size in self.free_blocks:
            all_blocks.append({
                'start': start,
                'size': size,
                'type': 'free',
                'pid': None
            })
            
        # 按起始地址排序
        all_blocks.sort(key=lambda x: x['start'])
          # 绘制内存块 - 所有块在同一行
        current_y = self.margin
        
        for block in all_blocks:
            start = block['start']
            size = block['size']
            block_type = block['type']
            pid = block['pid']
            
            # 计算块的位置和大小
            block_x = self.margin + start * scale
            block_width = size * scale
            
            # 确保块宽度至少为1像素
            if block_width < 1:
                block_width = 1
                
            # 选择颜色
            if block_type == 'allocated':
                color = self.allocated_color
            else:
                color = self.free_color
                
            # 绘制矩形
            painter.fillRect(
                int(block_x), 
                current_y, 
                int(block_width), 
                self.block_height, 
                color
            )
            
            # 绘制边框
            painter.setPen(QPen(self.border_color, 1))
            painter.drawRect(
                int(block_x), 
                current_y, 
                int(block_width), 
                self.block_height
            )
            
            # 绘制文字
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            
            if block_type == 'allocated':
                # 已分配的块始终显示 pid 和大小
                text = f"P{pid}\n{size}K"
            else:
                # 空闲块显示大小
                text = f"{size}K"
                
            # 计算文字位置
            text_rect = QRect(
                int(block_x) + 2, 
                current_y + 2, 
                int(block_width) - 4, 
                self.block_height - 4
            )
            
            # 根据方块大小调整字体
            if block_width < 30:
                # 非常小的块使用更小的字体
                small_font = QFont()
                small_font.setPointSize(7)
                painter.setFont(small_font)
            elif block_width < 50:
                # 中等大小的块使用稍小的字体
                medium_font = QFont()
                medium_font.setPointSize(8)
                painter.setFont(medium_font)
            else:
                # 大块使用正常字体
                normal_font = QFont()
                normal_font.setPointSize(self.font_size)
                painter.setFont(normal_font)
            
            painter.drawText(
                text_rect, 
                Qt.AlignCenter | Qt.TextWordWrap, 
                text
            )
            
        # 绘制内存地址标尺
        self._draw_ruler(painter, rect, scale)
        
    def _draw_ruler(self, painter, rect, scale):
        """绘制内存地址标尺"""
        ruler_height = 20
        ruler_y = rect.height() - ruler_height - 5
        
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        
        # 绘制标尺线
        painter.drawLine(
            self.margin, 
            ruler_y, 
            rect.width() - self.margin, 
            ruler_y
        )
        
        # 绘制刻度
        num_ticks = 5
        for i in range(num_ticks + 1):
            tick_pos = self.margin + (rect.width() - 2 * self.margin) * i / num_ticks
            tick_value = int(self.memory_size * i / num_ticks)
            
            # 绘制刻度线
            painter.drawLine(
                int(tick_pos), 
                ruler_y - 3, 
                int(tick_pos), 
                ruler_y + 3
            )
              # 绘制刻度值
            painter.drawText(
                int(tick_pos) - 15, 
                ruler_y + 15, 
                30, 
                10, 
                Qt.AlignCenter, 
                f"{tick_value}K"
            )
            
    def clear_memory(self):
        """清空内存，重置为初始状态"""
        self.allocated_blocks = {}
        self.free_blocks = [(0, self.memory_size)]
        self.update()
        
    def sizeHint(self):
        """返回推荐大小"""
        return QtCore.QSize(381, 200)
        
    def minimumSizeHint(self):
        """返回最小大小"""
        return QtCore.QSize(200, 120)