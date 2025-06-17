#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件系统图形用户界面
基于PyQt5的文件资源管理器
"""

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

from utils.Helpers import FileSystem
from utils.constants import SAVE_FILE


class FileSystemGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.fs = FileSystem()
        self.open_files = {}  # 存储打开的文件窗口
        self.init_ui()
        self.load_filesystem()
        self.refresh_file_list()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("文件系统管理器")
        self.setGeometry(100, 100, 1000, 700)
        
        # 设置应用图标
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建地址栏
        self.create_address_bar()
        main_layout.addWidget(self.address_widget)
        
        # 创建分割器（左侧目录树，右侧文件列表）
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 创建左侧目录树
        self.create_directory_tree()
        splitter.addWidget(self.tree_widget)
        
        # 创建右侧文件列表
        self.create_file_list()
        splitter.addWidget(self.list_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 700])
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建菜单栏
        self.create_menu_bar()
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        
        # 返回上级目录
        back_action = QAction(self.style().standardIcon(QStyle.SP_ArrowBack), '返回', self)
        back_action.setShortcut('Alt+Left')
        back_action.triggered.connect(self.go_back)
        toolbar.addAction(back_action)
        
        # 刷新
        refresh_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), '刷新', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_file_list)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 新建文件夹
        new_folder_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), '新建文件夹', self)
        new_folder_action.setShortcut('Ctrl+Shift+N')
        new_folder_action.triggered.connect(self.create_new_folder)
        toolbar.addAction(new_folder_action)
        
        # 新建文件
        new_file_action = QAction(self.style().standardIcon(QStyle.SP_FileIcon), '新建文件', self)
        new_file_action.setShortcut('Ctrl+N')
        new_file_action.triggered.connect(self.create_new_file)
        toolbar.addAction(new_file_action)
        
        toolbar.addSeparator()
        
        # 删除
        delete_action = QAction(self.style().standardIcon(QStyle.SP_TrashIcon), '删除', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_selected)
        toolbar.addAction(delete_action)
        
        # 保存文件系统
        save_action = QAction(self.style().standardIcon(QStyle.SP_DialogSaveButton), '保存', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_filesystem)
        toolbar.addAction(save_action)
        
    def create_address_bar(self):
        """创建地址栏"""
        self.address_widget = QWidget()
        layout = QHBoxLayout(self.address_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        layout.addWidget(QLabel("位置:"))
        
        self.address_line = QLineEdit()
        self.address_line.setReadOnly(True)
        self.address_line.setText("/")
        layout.addWidget(self.address_line)
        
        # 转到按钮
        goto_btn = QPushButton("转到")
        goto_btn.clicked.connect(self.goto_address)
        layout.addWidget(goto_btn)
        
    def create_directory_tree(self):
        """创建目录树"""
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("目录结构")
        self.tree_widget.itemClicked.connect(self.tree_item_clicked)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_tree_context_menu)
        
    def create_file_list(self):
        """创建文件列表"""
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ListMode)
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_widget.itemDoubleClicked.connect(self.item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_list_context_menu)
        
        # 设置项目大小
        self.list_widget.setGridSize(QSize(80, 80))
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 添加文件系统信息
        self.info_label = QLabel()
        self.status_bar.addPermanentWidget(self.info_label)
        self.update_status_info()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        new_file_action = QAction('新建文件', self)
        new_file_action.setShortcut('Ctrl+N')
        new_file_action.triggered.connect(self.create_new_file)
        file_menu.addAction(new_file_action)
        
        new_folder_action = QAction('新建文件夹', self)
        new_folder_action.setShortcut('Ctrl+Shift+N')
        new_folder_action.triggered.connect(self.create_new_folder)
        file_menu.addAction(new_folder_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('保存文件系统', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_filesystem)
        file_menu.addAction(save_action)
        
        load_action = QAction('加载文件系统', self)
        load_action.setShortcut('Ctrl+O')
        load_action.triggered.connect(self.load_filesystem)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        
        delete_action = QAction('删除', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)
        
        # 查看菜单
        view_menu = menubar.addMenu('查看')
        
        refresh_action = QAction('刷新', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_file_list)
        view_menu.addAction(refresh_action)
        
        # 系统菜单
        system_menu = menubar.addMenu('系统')
        
        format_action = QAction('格式化文件系统', self)
        format_action.triggered.connect(self.format_filesystem)
        system_menu.addAction(format_action)
        
        info_action = QAction('系统信息', self)
        info_action.triggered.connect(self.show_system_info)
        system_menu.addAction(info_action)
        
    def load_filesystem(self):
        """加载文件系统"""
        if os.path.exists(SAVE_FILE):
            success, msg = self.fs.load_from_file()
            if success:
                self.status_bar.showMessage(f"已加载文件系统: {msg}")
            else:
                self.status_bar.showMessage(f"加载失败: {msg}")
        else:
            self.status_bar.showMessage("使用新文件系统")
        
        self.update_directory_tree()
        self.refresh_file_list()
        self.update_status_info()
        
    def save_filesystem(self):
        """保存文件系统"""
        success, msg = self.fs.save_to_file()
        self.status_bar.showMessage(msg)
        
    def format_filesystem(self):
        """格式化文件系统"""
        reply = QMessageBox.question(self, '确认格式化', 
                                   '确定要格式化文件系统吗？所有数据将丢失！', 
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.fs.format()
            self.update_directory_tree()
            self.refresh_file_list()
            self.update_status_info()
            self.status_bar.showMessage("文件系统已格式化")
            
    def update_directory_tree(self):
        """更新目录树"""
        self.tree_widget.clear()
        
        # 创建根节点
        root_item = QTreeWidgetItem(self.tree_widget)
        root_item.setText(0, "文件系统 (/)")
        root_item.setIcon(0, self.style().standardIcon(QStyle.SP_DriveHDIcon))
        root_item.setData(0, Qt.UserRole, "/")
        
        # 递归添加子目录
        self._add_tree_items(self.fs.root, root_item, "/")
        
        # 展开根节点
        root_item.setExpanded(True)
        
    def _add_tree_items(self, node, parent_item, path):
        """递归添加树项目"""
        for child in node.children:
            if child.fcb.is_directory:
                child_path = path + ("" if path.endswith("/") else "/") + child.fcb.name
                item = QTreeWidgetItem(parent_item)
                item.setText(0, child.fcb.name)
                item.setIcon(0, self.style().standardIcon(QStyle.SP_DirClosedIcon))
                item.setData(0, Qt.UserRole, child_path)
                
                # 递归添加子目录
                self._add_tree_items(child, item, child_path)
                
    def refresh_file_list(self):
        """刷新文件列表"""
        self.list_widget.clear()
        
        items = self.fs.list_directory()
        for item in items:
            list_item = QListWidgetItem()
            list_item.setText(item['name'])
            
            # 设置图标
            if item['type'] == "目录":
                list_item.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
            else:
                list_item.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
            
            # 存储项目信息
            list_item.setData(Qt.UserRole, item)
            
            self.list_widget.addItem(list_item)
        
        # 更新地址栏
        self.address_line.setText(self.fs.get_current_path())
        self.update_status_info()
        
    def tree_item_clicked(self, item, column):
        """目录树项目点击事件"""
        path = item.data(0, Qt.UserRole)
        if path:
            success, msg = self.fs.change_directory(path)
            if success:
                self.refresh_file_list()
                self.status_bar.showMessage(msg)
            else:
                QMessageBox.warning(self, "错误", msg)
                
    def item_double_clicked(self, item):
        """文件列表项目双击事件"""
        data = item.data(Qt.UserRole)
        if data['type'] == "目录":
            # 进入目录
            success, msg = self.fs.change_directory(data['name'])
            if success:
                self.refresh_file_list()
                self.update_directory_tree()
                self.status_bar.showMessage(msg)
            else:
                QMessageBox.warning(self, "错误", msg)
        else:
            # 打开文件
            self.open_file(data['name'])
            
    def go_back(self):
        """返回上级目录"""
        current_path = self.fs.get_current_path()
        if current_path != "/":
            success, msg = self.fs.change_directory("..")
            if success:
                self.refresh_file_list()
                self.update_directory_tree()
                self.status_bar.showMessage(msg)
                
    def goto_address(self):
        """转到指定地址"""
        path, ok = QInputDialog.getText(self, '转到', '请输入路径:', text=self.address_line.text())
        if ok and path:
            success, msg = self.fs.change_directory(path)
            if success:
                self.refresh_file_list()
                self.update_directory_tree()
                self.status_bar.showMessage(msg)
            else:
                QMessageBox.warning(self, "错误", msg)
                
    def create_new_folder(self):
        """创建新文件夹"""
        name, ok = QInputDialog.getText(self, '新建文件夹', '请输入文件夹名称:')
        if ok and name:
            success, msg = self.fs.create_directory(name)
            if success:
                self.refresh_file_list()
                self.update_directory_tree()
                self.status_bar.showMessage(msg)
            else:
                QMessageBox.warning(self, "错误", msg)
                
    def create_new_file(self):
        """创建新文件"""
        name, ok = QInputDialog.getText(self, '新建文件', '请输入文件名称:')
        if ok and name:
            success, msg = self.fs.create_file(name, "")
            if success:
                self.refresh_file_list()
                self.status_bar.showMessage(msg)
            else:
                QMessageBox.warning(self, "错误", msg)
                
    def delete_selected(self):
        """删除选中的项目"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选择要删除的项目")
            return
        
        # 确认删除
        if len(selected_items) == 1:
            item_data = selected_items[0].data(Qt.UserRole)
            confirm_msg = f"确定要删除 '{item_data['name']}' 吗？"
        else:
            confirm_msg = f"确定要删除选中的 {len(selected_items)} 个项目吗？"
            
        reply = QMessageBox.question(self, '确认删除', confirm_msg, 
                                   QMessageBox.Yes | QMessageBox.No, 
                                   QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
            
        # 执行删除
        for item in selected_items:
            data = item.data(Qt.UserRole)
            if data['type'] == "目录":
                self.delete_directory(data['name'])
            else:
                self.delete_file(data['name'])
                
        self.refresh_file_list()
        self.update_directory_tree()
        
    def delete_directory(self, name):
        """删除目录（支持递归删除确认）"""
        success, result = self.fs.delete_directory(name, recursive=False)
        
        if success:
            self.status_bar.showMessage(result)
            return
            
        # 检查是否需要递归删除
        if isinstance(result, dict) and result.get('type') == 'suggest_recursive':
            dir_info = result['info']
            
            # 显示递归删除确认对话框
            dialog = RecursiveDeleteDialog(dir_info, name, self)
            if dialog.exec_() == QDialog.Accepted:
                # 用户确认递归删除
                success, msg = self.fs.delete_directory(name, recursive=True, force=True)
                if success:
                    self.status_bar.showMessage(msg)
                else:
                    QMessageBox.warning(self, "错误", msg)
            else:
                self.status_bar.showMessage("删除操作已取消")
        else:
            QMessageBox.warning(self, "错误", str(result))
            
    def delete_file(self, name):
        """删除文件"""
        success, msg = self.fs.delete_file(name)
        if success:
            self.status_bar.showMessage(msg)
        else:
            QMessageBox.warning(self, "错误", msg)
            
    def open_file(self, name):
        """打开文件"""
        # 检查文件是否已经打开
        if name in self.open_files:
            self.open_files[name].raise_()
            self.open_files[name].activateWindow()
            return
            
        # 打开文件
        file_id, msg = self.fs.open_file(name, "rw")
        if file_id is None:
            QMessageBox.warning(self, "错误", msg)
            return
            
        # 读取文件内容
        content, msg = self.fs.read_file(file_id)
        if content is None:
            QMessageBox.warning(self, "错误", msg)
            self.fs.close_file(file_id)
            return
            
        # 创建文件编辑窗口
        editor = FileEditor(name, content, file_id, self.fs, self)
        editor.file_saved.connect(self.refresh_file_list)
        editor.show()
        
        # 保存引用
        self.open_files[name] = editor
        editor.finished.connect(lambda: self.open_files.pop(name, None))
        
    def show_tree_context_menu(self, position):
        """显示目录树右键菜单"""
        item = self.tree_widget.itemAt(position)
        if item:
            menu = QMenu()
            
            new_folder_action = menu.addAction("新建文件夹")
            new_folder_action.triggered.connect(self.create_new_folder)
            
            new_file_action = menu.addAction("新建文件")
            new_file_action.triggered.connect(self.create_new_file)
            
            menu.addSeparator()
            
            refresh_action = menu.addAction("刷新")
            refresh_action.triggered.connect(self.refresh_file_list)
            
            menu.exec_(self.tree_widget.mapToGlobal(position))
            
    def show_list_context_menu(self, position):
        """显示文件列表右键菜单"""
        item = self.list_widget.itemAt(position)
        menu = QMenu()
        
        if item:
            data = item.data(Qt.UserRole)
            
            if data['type'] == "目录":
                open_action = menu.addAction("打开")
                open_action.triggered.connect(lambda: self.item_double_clicked(item))
            else:
                open_action = menu.addAction("编辑")
                open_action.triggered.connect(lambda: self.open_file(data['name']))
                
            menu.addSeparator()
            
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(self.delete_selected)
            
            menu.addSeparator()
            
        new_folder_action = menu.addAction("新建文件夹")
        new_folder_action.triggered.connect(self.create_new_folder)
        
        new_file_action = menu.addAction("新建文件")
        new_file_action.triggered.connect(self.create_new_file)
        
        menu.addSeparator()
        
        refresh_action = menu.addAction("刷新")
        refresh_action.triggered.connect(self.refresh_file_list)
        
        menu.exec_(self.list_widget.mapToGlobal(position))
        
    def show_system_info(self):
        """显示系统信息"""
        info = self.fs.get_system_info()
        
        msg = f"""文件系统信息:
        
总容量: {info['total_size']} bytes ({info['total_blocks']} 块)
已使用: {info['used_size']} bytes ({info['used_blocks']} 块)  
空闲: {info['free_size']} bytes ({info['free_blocks']} 块)
块大小: {info['block_size']} bytes
使用率: {info['used_blocks']/info['total_blocks']*100:.1f}%"""
        
        QMessageBox.information(self, "系统信息", msg)
        
    def update_status_info(self):
        """更新状态栏信息"""
        info = self.fs.get_system_info()
        items = self.fs.list_directory()
        file_count = sum(1 for item in items if item['type'] == '文件')
        dir_count = sum(1 for item in items if item['type'] == '目录')
        
        status_text = f"项目: {len(items)} ({file_count} 个文件, {dir_count} 个文件夹) | 使用率: {info['used_blocks']/info['total_blocks']*100:.1f}%"
        self.info_label.setText(status_text)
        
    def closeEvent(self, event):
        """关闭事件"""
        # 自动保存
        self.save_filesystem()
        event.accept()


class RecursiveDeleteDialog(QDialog):
    """递归删除确认对话框"""
    
    def __init__(self, dir_info, dir_name, parent=None):
        super().__init__(parent)
        self.dir_info = dir_info
        self.dir_name = dir_name
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("递归删除确认")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 警告图标和标题
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(32, 32))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(f"删除目录 '{self.dir_name}' 及其所有内容")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # 目录信息
        info_text = f"""目录包含:
• {self.dir_info['total_files']} 个文件
• {self.dir_info['total_dirs']} 个子目录  
• 总大小: {self.dir_info['total_size']} bytes

此操作将永久删除所有内容，无法撤销！"""
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: red; margin: 10px;")
        layout.addWidget(info_label)
        
        # 内容列表
        layout.addWidget(QLabel("包含的项目:"))
        
        list_widget = QListWidget()
        for item in self.dir_info['items'][:20]:  # 只显示前20个
            list_widget.addItem(item)
        
        if len(self.dir_info['items']) > 20:
            list_widget.addItem(f"... 还有 {len(self.dir_info['items']) - 20} 个项目")
        
        layout.addWidget(list_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        delete_btn = QPushButton("确认删除")
        delete_btn.setStyleSheet("background-color: #d32f2f; color: white;")
        delete_btn.clicked.connect(self.accept)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)


class FileEditor(QDialog):
    """文件编辑器"""
    
    file_saved = pyqtSignal()
    
    def __init__(self, filename, content, file_id, filesystem, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.file_id = file_id
        self.fs = filesystem
        self.original_content = content
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"编辑 - {self.filename}")
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.setShortcut("Ctrl+S")
        save_btn.clicked.connect(self.save_file)
        toolbar.addWidget(save_btn)
        
        toolbar.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        toolbar.addWidget(close_btn)
        
        layout.addLayout(toolbar)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.original_content)
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)
        
    def on_text_changed(self):
        """文本改变事件"""
        if self.text_edit.toPlainText() != self.original_content:
            self.setWindowTitle(f"编辑 - {self.filename} *")
            self.status_label.setText("已修改")
        else:
            self.setWindowTitle(f"编辑 - {self.filename}")
            self.status_label.setText("就绪")
            
    def save_file(self):
        """保存文件"""
        content = self.text_edit.toPlainText()
        success, msg = self.fs.write_file(self.file_id, content)
        
        if success:
            self.original_content = content
            self.setWindowTitle(f"编辑 - {self.filename}")
            self.status_label.setText("已保存")
            self.file_saved.emit()
        else:
            QMessageBox.warning(self, "错误", msg)
            
    def closeEvent(self, event):
        """关闭事件"""
        if self.text_edit.toPlainText() != self.original_content:
            reply = QMessageBox.question(self, '保存更改', 
                                       f'文件 "{self.filename}" 已修改，是否保存更改？',
                                       QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                       QMessageBox.Save)
            
            if reply == QMessageBox.Save:
                self.save_file()
                self.fs.close_file(self.file_id)
                event.accept()
            elif reply == QMessageBox.Discard:
                self.fs.close_file(self.file_id)
                event.accept()
            else:
                event.ignore()
        else:
            self.fs.close_file(self.file_id)
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("文件系统管理器")
    app.setApplicationVersion("1.0")
    
    # 创建主窗口
    window = FileSystemGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
