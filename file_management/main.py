#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件系统主程序
提供命令行界面操作文件系统
"""

import sys
import os

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.Helpers import FileSystem
from utils.constants import SAVE_FILE


class FileSystemCLI:
    """文件系统命令行界面"""
    
    def __init__(self):
        self.fs = FileSystem()
        self.running = True
        
    def show_help(self):
        """显示帮助信息"""
        help_text = """
文件系统命令列表:
=====================================
目录操作:
  ls                    - 显示当前目录内容
  pwd                   - 显示当前路径  
  cd <path>             - 切换目录
  mkdir <name>          - 创建目录
  rmdir <name>          - 删除目录

文件操作:
  touch <name> [content] - 创建文件
  cat <name>            - 显示文件内容
  write <name> <content> - 写入文件内容
  rm <name>             - 删除文件

系统操作:
  format                - 格式化文件系统
  info                  - 显示系统信息
  save [filename]       - 保存文件系统
  load [filename]       - 加载文件系统
  
其他:
  help                  - 显示此帮助
  exit/quit             - 退出程序
=====================================
"""
        print(help_text)
    
    def parse_command(self, command_line):
        """解析命令行"""
        parts = command_line.strip().split(maxsplit=2)
        if not parts:
            return None, []
        
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        return cmd, args
    
    def cmd_ls(self, args):
        """显示目录内容"""
        items = self.fs.list_directory()
        if not items:
            print("目录为空")
            return
        
        print(f"{'类型':<6} {'名称':<20} {'大小':<10} {'修改时间'}")
        print("-" * 50)
        for item in items:
            print(f"{item['type']:<6} {item['name']:<20} {item['size']:<10} {item['modified']}")
    
    def cmd_pwd(self, args):
        """显示当前路径"""
        print(self.fs.get_current_path())
    
    def cmd_cd(self, args):
        """切换目录"""
        if not args:
            print("用法: cd <path>")
            return
        
        success, msg = self.fs.change_directory(args[0])
        print(msg)
    
    def cmd_mkdir(self, args):
        """创建目录"""
        if not args:
            print("用法: mkdir <name>")
            return
        
        success, msg = self.fs.create_directory(args[0])
        print(msg)
    
    def cmd_rmdir(self, args):
        """删除目录"""
        if not args:
            print("用法: rmdir <name>")
            return
        
        success, msg = self.fs.delete_directory(args[0])
        print(msg)
    
    def cmd_touch(self, args):
        """创建文件"""
        if not args:
            print("用法: touch <name> [content]")
            return
        
        name = args[0]
        content = args[1] if len(args) > 1 else ""
        success, msg = self.fs.create_file(name, content)
        print(msg)
    
    def cmd_cat(self, args):
        """显示文件内容"""
        if not args:
            print("用法: cat <name>")
            return
        
        file_id, msg = self.fs.open_file(args[0], "r")
        if file_id is None:
            print(msg)
            return
        
        content, msg = self.fs.read_file(file_id)
        if content is not None:
            print("文件内容:")
            print("-" * 30)
            print(content)
            print("-" * 30)
        else:
            print(msg)
        
        self.fs.close_file(file_id)
    
    def cmd_write(self, args):
        """写入文件"""
        if len(args) < 2:
            print("用法: write <name> <content>")
            return
        
        name = args[0]
        content = args[1]
        
        file_id, msg = self.fs.open_file(name, "w")
        if file_id is None:
            print(msg)
            return
        
        success, msg = self.fs.write_file(file_id, content)
        print(msg)
        self.fs.close_file(file_id)
    
    def cmd_rm(self, args):
        """删除文件"""
        if not args:
            print("用法: rm <name>")
            return
        
        success, msg = self.fs.delete_file(args[0])
        print(msg)
    
    def cmd_format(self, args):
        """格式化文件系统"""
        confirm = input("确定要格式化文件系统吗？所有数据将丢失 (y/N): ")
        if confirm.lower() == 'y':
            self.fs.format()
        else:
            print("操作已取消")
    
    def cmd_info(self, args):
        """显示系统信息"""
        info = self.fs.get_system_info()
        print("文件系统信息:")
        print(f"  总容量: {info['total_size']} bytes ({info['total_blocks']} 块)")
        print(f"  已使用: {info['used_size']} bytes ({info['used_blocks']} 块)")
        print(f"  空闲:   {info['free_size']} bytes ({info['free_blocks']} 块)")
        print(f"  块大小: {info['block_size']} bytes")
        print(f"  使用率: {info['used_blocks']/info['total_blocks']*100:.1f}%")
    
    def cmd_save(self, args):
        """保存文件系统"""
        filename = args[0] if args else None
        success, msg = self.fs.save_to_file(filename)
        print(msg)
    
    def cmd_load(self, args):
        """加载文件系统"""
        filename = args[0] if args else None
        success, msg = self.fs.load_from_file(filename)
        print(msg)
    
    def cmd_help(self, args):
        """显示帮助"""
        self.show_help()
    
    def cmd_exit(self, args):
        """退出程序"""
        # 自动保存
        print("正在保存文件系统...")
        success, msg = self.fs.save_to_file()
        print(msg)
        
        print("再见!")
        self.running = False
    
    def run(self):
        """运行命令行界面"""
        print("=" * 50)
        print("欢迎使用简单文件系统")
        print("=" * 50)
        print("输入 'help' 查看命令列表")
        
        # 尝试加载现有文件系统
        if os.path.exists(SAVE_FILE):
            success, msg = self.fs.load_from_file()
            if success:
                print(f"已加载现有文件系统: {msg}")
            else:
                print(f"加载失败，使用新文件系统: {msg}")
        
        while self.running:
            try:
                current_path = self.fs.get_current_path()
                command_line = input(f"filesystem:{current_path}$ ")
                
                if not command_line.strip():
                    continue
                
                cmd, args = self.parse_command(command_line)
                
                # 查找对应的命令方法
                method_name = f"cmd_{cmd}"
                if hasattr(self, method_name):
                    method = getattr(self, method_name)
                    method(args)
                elif cmd in ['quit', 'exit']:
                    self.cmd_exit(args)
                else:
                    print(f"未知命令: {cmd}")
                    print("输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                print("\n使用 'exit' 命令退出程序")
            except Exception as e:
                print(f"错误: {e}")


def main():
    """主函数"""
    cli = FileSystemCLI()
    cli.run()


if __name__ == "__main__":
    main()
