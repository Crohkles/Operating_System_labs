import os
import json
from datetime import datetime
from bitarray import bitarray
from .constants import FAT_FREE, FAT_END, SAVE_FILE

class Disk:
    def __init__(self, block_count, block_size):
        self.block_size = block_size
        self.block_count = block_count
        self.blocks=["" for _ in range(block_count)]

class FCB:
    def __init__(self, name, size, start_block, is_directory=False):
        self.name = name
        self.size = size
        self.start_block = start_block
        self.is_directory = is_directory
        self.creation_time = datetime.now()
        self.last_access_time = datetime.now()
        self.last_modification_time = datetime.now()
    
    def to_dict(self):
        """转换为字典用于序列化"""
        return {
            'name': self.name,
            'size': self.size,
            'start_block': self.start_block,
            'is_directory': self.is_directory,
            'creation_time': self.creation_time.isoformat(),
            'last_access_time': self.last_access_time.isoformat(),
            'last_modification_time': self.last_modification_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建FCB对象"""
        fcb = cls(data['name'], data['size'], data['start_block'], data['is_directory'])
        fcb.creation_time = datetime.fromisoformat(data['creation_time'])
        fcb.last_access_time = datetime.fromisoformat(data['last_access_time'])
        fcb.last_modification_time = datetime.fromisoformat(data['last_modification_time'])
        return fcb

class FAT:
    def __init__(self, block_count):
        self.block_count = block_count
        self.fat = [FAT_FREE] * block_count
    
    def allocate_blocks(self, size_needed, block_size):
        """分配所需的块"""
        blocks_needed = (size_needed + block_size - 1) // block_size
        if blocks_needed == 0:
            return []
        
        allocated_blocks = []
        for i in range(self.block_count):
            if self.fat[i] == FAT_FREE:
                allocated_blocks.append(i)
                if len(allocated_blocks) == blocks_needed:
                    break
        
        if len(allocated_blocks) < blocks_needed:
            return None  # 空间不足
        
        # 建立FAT链
        for i in range(len(allocated_blocks) - 1):
            self.fat[allocated_blocks[i]] = allocated_blocks[i + 1]
        self.fat[allocated_blocks[-1]] = FAT_END
        
        return allocated_blocks[0]  # 返回起始块号
    
    def get_file_blocks(self, start_block):
        """获取文件的所有块号"""
        blocks = []
        current = start_block
        while current != FAT_END and current != FAT_FREE:
            blocks.append(current)
            current = self.fat[current]
        return blocks
    
    def free_blocks(self, start_block):
        """释放文件占用的块"""
        blocks = self.get_file_blocks(start_block)
        for block in blocks:
            self.fat[block] = FAT_FREE
        return len(blocks)

class FreeSpaceBitmap:
    def __init__(self, block_count):
        self.block_count = block_count
        self.bitmap = bitarray(block_count)
        self.bitmap.setall(0)  # 0表示空闲，1表示占用
    
    def allocate_block(self, block_num):
        """分配指定块"""
        if block_num < self.block_count and not self.bitmap[block_num]:
            self.bitmap[block_num] = 1
            return True
        return False
    
    def free_block(self, block_num):
        """释放指定块"""
        if block_num < self.block_count:
            self.bitmap[block_num] = 0
    
    def get_free_blocks_count(self):
        """获取空闲块数量"""
        return self.bitmap.count(0)

class FileNode:
    def __init__(self, fcb):
        self.fcb = fcb
        self.children = []
        self.parent = None 
        self.path = fcb.name if not fcb.is_directory else fcb.name + '/'
    
    def add_child(self, child_node):
        """添加子节点"""
        child_node.parent = self
        self.children.append(child_node)
    
    def remove_child(self, child_name):
        """移除子节点"""
        self.children = [child for child in self.children if child.fcb.name != child_name]
    
    def find_child(self, name):
        """查找子节点"""
        for child in self.children:
            if child.fcb.name == name:
                return child
        return None
    
    def to_dict(self):
        """转换为字典用于序列化"""
        return {
            'fcb': self.fcb.to_dict(),
            'children': [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建FileNode对象"""
        fcb = FCB.from_dict(data['fcb'])
        node = cls(fcb)
        for child_data in data['children']:
            child_node = cls.from_dict(child_data)
            node.add_child(child_node)
        return node

class FileSystem:
    def __init__(self, block_count=1000, block_size=1024):
        self.block_size = block_size
        self.block_count = block_count
        
        # 初始化各组件
        self.disk = Disk(block_count, block_size)
        self.fat = FAT(block_count)
        self.bitmap = FreeSpaceBitmap(block_count)
        
        # 创建根目录
        root_fcb = FCB("/", 0, -1, is_directory=True)
        self.root = FileNode(root_fcb)
        self.current_dir = self.root
        self.current_path = ["/"]
        
        # 打开文件表
        self.open_files = {}  # {file_id: {'node': FileNode, 'mode': str, 'position': int}}
        self.next_file_id = 1
    
    def format(self):
        """格式化文件系统"""
        self.disk = Disk(self.block_count, self.block_size)
        self.fat = FAT(self.block_count)
        self.bitmap = FreeSpaceBitmap(self.block_count)
        
        root_fcb = FCB("/", 0, -1, is_directory=True)
        self.root = FileNode(root_fcb)
        self.current_dir = self.root
        self.current_path = ["/"]
        self.open_files = {}
        print("文件系统格式化完成")
    
    def create_directory(self, name):
        """创建子目录"""
        if self.current_dir.find_child(name):
            return False, f"目录 '{name}' 已存在"
        
        dir_fcb = FCB(name, 0, -1, is_directory=True)
        dir_node = FileNode(dir_fcb)
        self.current_dir.add_child(dir_node)
        return True, f"目录 '{name}' 创建成功"
    
    def delete_directory(self, name):
        """删除子目录"""
        child = self.current_dir.find_child(name)
        if not child:
            return False, f"目录 '{name}' 不存在"
        
        if not child.fcb.is_directory:
            return False, f"'{name}' 不是目录"
        
        if child.children:
            return False, f"目录 '{name}' 不为空，无法删除"
        
        self.current_dir.remove_child(name)
        return True, f"目录 '{name}' 删除成功"
    
    def list_directory(self):
        """显示当前目录内容"""
        items = []
        for child in self.current_dir.children:
            fcb = child.fcb
            item_type = "目录" if fcb.is_directory else "文件"
            items.append({
                'name': fcb.name,
                'type': item_type,
                'size': fcb.size,
                'created': fcb.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
                'modified': fcb.last_modification_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        return items
    
    def change_directory(self, path):
        """更改当前目录"""
        if path == "..":
            if self.current_dir.parent:
                self.current_dir = self.current_dir.parent
                self.current_path.pop()
                return True, f"切换到上级目录"
            else:
                return False, "已在根目录"
        
        if path.startswith("/"):
            # 绝对路径
            self.current_dir = self.root
            self.current_path = ["/"]
            if path == "/":
                return True, "切换到根目录"
            path = path[1:]  # 移除开头的/
        
        # 相对路径
        parts = path.split("/")
        for part in parts:
            if not part:
                continue
            child = self.current_dir.find_child(part)
            if not child or not child.fcb.is_directory:
                return False, f"目录 '{part}' 不存在"
            self.current_dir = child
            self.current_path.append(part)
        
        return True, f"切换到目录: {'/' if len(self.current_path) == 1 else '/'.join(self.current_path[1:])}"
    
    def create_file(self, name, content=""):
        """创建文件"""
        if self.current_dir.find_child(name):
            return False, f"文件 '{name}' 已存在"
        
        # 分配磁盘块
        start_block = self.fat.allocate_blocks(len(content), self.block_size)
        if start_block is None:
            return False, "磁盘空间不足"
        
        # 写入内容到磁盘块
        if content:
            self._write_to_blocks(start_block, content)
            # 更新位图
            blocks = self.fat.get_file_blocks(start_block)
            for block in blocks:
                self.bitmap.allocate_block(block)
        
        # 创建FCB和文件节点
        file_fcb = FCB(name, len(content), start_block if content else -1, is_directory=False)
        file_node = FileNode(file_fcb)
        self.current_dir.add_child(file_node)
        
        return True, f"文件 '{name}' 创建成功"
    
    def delete_file(self, name):
        """删除文件"""
        child = self.current_dir.find_child(name)
        if not child:
            return False, f"文件 '{name}' 不存在"
        
        if child.fcb.is_directory:
            return False, f"'{name}' 是目录，请使用删除目录命令"
        
        # 释放磁盘块
        if child.fcb.start_block != -1:
            blocks = self.fat.get_file_blocks(child.fcb.start_block)
            for block in blocks:
                self.bitmap.free_block(block)
            self.fat.free_blocks(child.fcb.start_block)
        
        # 关闭打开的文件
        for file_id, file_info in list(self.open_files.items()):
            if file_info['node'] == child:
                del self.open_files[file_id]
        
        self.current_dir.remove_child(name)
        return True, f"文件 '{name}' 删除成功"
    
    def open_file(self, name, mode="r"):
        """打开文件"""
        child = self.current_dir.find_child(name)
        if not child:
            return None, f"文件 '{name}' 不存在"
        
        if child.fcb.is_directory:
            return None, f"'{name}' 是目录，无法打开"
        
        if mode not in ["r", "w", "rw"]:
            return None, "无效的文件模式"
        
        file_id = self.next_file_id
        self.next_file_id += 1
        
        self.open_files[file_id] = {
            'node': child,
            'mode': mode,
            'position': 0
        }
        
        child.fcb.last_access_time = datetime.now()
        return file_id, f"文件 '{name}' 打开成功"
    
    def close_file(self, file_id):
        """关闭文件"""
        if file_id not in self.open_files:
            return False, "无效的文件ID"
        
        del self.open_files[file_id]
        return True, "文件关闭成功"
    
    def read_file(self, file_id, size=-1):
        """读取文件"""
        if file_id not in self.open_files:
            return None, "无效的文件ID"
        
        file_info = self.open_files[file_id]
        if "r" not in file_info['mode']:
            return None, "文件未以读模式打开"
        
        node = file_info['node']
        if node.fcb.start_block == -1:
            return "", "文件为空"
        
        content = self._read_from_blocks(node.fcb.start_block, node.fcb.size)
        start_pos = file_info['position']
        
        if size == -1:
            result = content[start_pos:]
            file_info['position'] = len(content)
        else:
            result = content[start_pos:start_pos + size]
            file_info['position'] = min(len(content), start_pos + size)
        
        node.fcb.last_access_time = datetime.now()
        return result, "读取成功"
    
    def write_file(self, file_id, content):
        """写入文件"""
        if file_id not in self.open_files:
            return False, "无效的文件ID"
        
        file_info = self.open_files[file_id]
        if "w" not in file_info['mode']:
            return False, "文件未以写模式打开"
        
        node = file_info['node']
        
        # 释放原有块
        if node.fcb.start_block != -1:
            blocks = self.fat.get_file_blocks(node.fcb.start_block)
            for block in blocks:
                self.bitmap.free_block(block)
            self.fat.free_blocks(node.fcb.start_block)
        
        # 分配新块
        if content:
            start_block = self.fat.allocate_blocks(len(content), self.block_size)
            if start_block is None:
                return False, "磁盘空间不足"
            
            self._write_to_blocks(start_block, content)
            blocks = self.fat.get_file_blocks(start_block)
            for block in blocks:
                self.bitmap.allocate_block(block)
            
            node.fcb.start_block = start_block
        else:
            node.fcb.start_block = -1
        
        node.fcb.size = len(content)
        node.fcb.last_modification_time = datetime.now()
        file_info['position'] = len(content)
        
        return True, "写入成功"
    
    def _write_to_blocks(self, start_block, content):
        """将内容写入磁盘块"""
        blocks = self.fat.get_file_blocks(start_block)
        content_bytes = content.encode('utf-8')
        
        for i, block_num in enumerate(blocks):
            start_pos = i * self.block_size
            end_pos = min(start_pos + self.block_size, len(content_bytes))
            block_content = content_bytes[start_pos:end_pos].decode('utf-8')
            self.disk.blocks[block_num] = block_content
    
    def _read_from_blocks(self, start_block, file_size):
        """从磁盘块读取内容"""
        blocks = self.fat.get_file_blocks(start_block)
        content = ""
        
        for block_num in blocks:
            content += self.disk.blocks[block_num]
        
        return content[:file_size] if file_size > 0 else content
    
    def get_current_path(self):
        """获取当前路径"""
        if len(self.current_path) == 1:
            return "/"
        return "/" + "/".join(self.current_path[1:])
    
    def get_system_info(self):
        """获取系统信息"""
        total_blocks = self.block_count
        free_blocks = self.bitmap.get_free_blocks_count()
        used_blocks = total_blocks - free_blocks
        
        return {
            'total_blocks': total_blocks,
            'used_blocks': used_blocks,
            'free_blocks': free_blocks,
            'block_size': self.block_size,
            'total_size': total_blocks * self.block_size,
            'used_size': used_blocks * self.block_size,
            'free_size': free_blocks * self.block_size
        }
    
    def save_to_file(self, filename=None):
        """保存文件系统到JSON文件"""
        if filename is None:
            filename = SAVE_FILE
        
        try:
            fs_data = {
                'block_count': self.block_count,
                'block_size': self.block_size,
                'fat': self.fat.fat,
                'bitmap': self.bitmap.bitmap.tolist(),
                'disk_blocks': self.disk.blocks,
                'root': self.root.to_dict(),
                'current_path': self.current_path,
                'next_file_id': self.next_file_id
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(fs_data, f, ensure_ascii=False, indent=2)
            
            return True, f"文件系统已保存到 {filename}"
        except Exception as e:
            return False, f"保存失败: {str(e)}"
    
    def load_from_file(self, filename=None):
        """从JSON文件加载文件系统"""
        if filename is None:
            filename = SAVE_FILE
        
        try:
            if not os.path.exists(filename):
                return False, f"文件 {filename} 不存在"
            
            with open(filename, 'r', encoding='utf-8') as f:
                fs_data = json.load(f)
            
            # 恢复基本参数
            self.block_count = fs_data['block_count']
            self.block_size = fs_data['block_size']
            
            # 恢复磁盘
            self.disk = Disk(self.block_count, self.block_size)
            self.disk.blocks = fs_data['disk_blocks']
            
            # 恢复FAT表
            self.fat = FAT(self.block_count)
            self.fat.fat = fs_data['fat']
            
            # 恢复位图
            self.bitmap = FreeSpaceBitmap(self.block_count)
            self.bitmap.bitmap = bitarray(fs_data['bitmap'])
            
            # 恢复目录结构
            self.root = FileNode.from_dict(fs_data['root'])
            self.current_path = fs_data['current_path']
            self.next_file_id = fs_data.get('next_file_id', 1)
            
            # 恢复当前目录
            self.current_dir = self.root
            for path_part in self.current_path[1:]:  # 跳过根目录
                self.current_dir = self.current_dir.find_child(path_part)
            
            # 清空打开文件表
            self.open_files = {}
            
            return True, f"文件系统已从 {filename} 加载"
        except Exception as e:
            return False, f"加载失败: {str(e)}"