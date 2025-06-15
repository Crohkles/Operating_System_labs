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
        """创建子目录 - 现在支持路径"""
        # 检查是否包含路径分隔符，如果有则使用路径解析
        if "/" in name:
            return self.create_directory_with_path(name)
          # 原有逻辑：在当前目录下创建
        if self.current_dir.find_child(name):
            return False, f"目录 '{name}' 已存在"
        
        dir_fcb = FCB(name, 0, -1, is_directory=True)
        dir_node = FileNode(dir_fcb)
        self.current_dir.add_child(dir_node)
        return True, f"目录 '{name}' 创建成功"
    
    def delete_directory(self, name, recursive=False, force=False, confirm_callback=None):
        """删除子目录 - 现在支持路径和递归删除
        
        Args:
            name: 目录名或路径
            recursive: 是否递归删除
            force: 是否强制删除（跳过确认）
            confirm_callback: 确认回调函数
        """
        # 检查是否包含路径分隔符，如果有则使用路径解析
        if "/" in name:
            return self.delete_directory_with_path(name, recursive, force, confirm_callback)
        
        # 原有逻辑：在当前目录下删除
        child = self.current_dir.find_child(name)
        if not child:
            return False, f"目录 '{name}' 不存在"
        
        if not child.fcb.is_directory:
            return False, f"'{name}' 不是目录"
        
        if child.children:
            if recursive:
                # 使用递归删除
                return self.delete_directory_recursive(name, force, confirm_callback)
            else:
                # 非递归模式，提供递归删除建议
                dir_info = self._get_directory_info(child, name)
                return False, {
                    'type': 'suggest_recursive',
                    'info': dir_info,
                    'message': f"目录 '{name}' 不为空，包含 {dir_info['total_files']} 个文件和 {dir_info['total_dirs']} 个子目录。使用 recursive=True 进行递归删除。"
                }
        
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
                'modified': fcb.last_modification_time.strftime("%Y-%m-%d %H:%M:%S")            })
        return items
    
    def change_directory(self, path):
        """更改当前目录 - 支持绝对路径和相对路径"""
        # 使用新的路径解析功能
        target_node, success, msg = self._resolve_path(path)
        
        if not success:
            return False, msg
        
        if not target_node.fcb.is_directory:
            return False, f"'{path}' 不是目录"
        
        # 更新当前目录
        self.current_dir = target_node
        
        # 重建当前路径
        new_path = []
        current = target_node
        while current and current != self.root:
            new_path.insert(0, current.fcb.name)
            current = current.parent
        
        if not new_path:
            self.current_path = ["/"]
        else:            self.current_path = ["/"] + new_path
        
        current_path_str = self.get_current_path()
        return True, f"切换到目录: {current_path_str}"
    
    def create_file(self, name, content=""):
        """创建文件 - 现在支持路径"""
        # 检查是否包含路径分隔符，如果有则使用路径解析
        if "/" in name:
            return self.create_file_with_path(name, content)
        
        # 原有逻辑：在当前目录下创建
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
        """删除文件 - 现在支持路径"""
        # 检查是否包含路径分隔符，如果有则使用路径解析
        if "/" in name:
            return self.delete_file_with_path(name)
        
        # 原有逻辑：在当前目录下删除
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
    
    def _normalize_path(self, path):
        """标准化路径，处理 . 和 .. 以及多个连续的 /"""
        if not path:
            return ""
        
        # 将路径分割成组件
        if path.startswith("/"):
            is_absolute = True
            components = path[1:].split("/") if path != "/" else []
        else:
            is_absolute = False
            components = path.split("/")
        
        # 处理 . 和 .. 
        normalized = []
        for component in components:
            if component == "" or component == ".":
                continue  # 忽略空组件和当前目录
            elif component == "..":
                if normalized:
                    normalized.pop()  # 返回上级目录
            else:
                normalized.append(component)
        
        # 重建路径
        if is_absolute:            
            return "/" + "/".join(normalized) if normalized else "/"
        else:
            return "/".join(normalized)
    
    def _resolve_path(self, path):
        """解析路径，返回目标节点和路径信息"""
        # 对于相对路径，需要从当前路径开始计算
        if not path.startswith("/"):
            # 相对路径：基于当前路径构建完整路径
            current_path_str = "/".join(self.current_path[1:]) if len(self.current_path) > 1 else ""
            if current_path_str:
                full_path = "/" + current_path_str + "/" + path
            else:
                full_path = "/" + path
            normalized_path = self._normalize_path(full_path)
        else:
            # 绝对路径
            normalized_path = self._normalize_path(path)
        
        if not normalized_path:
            return self.current_dir, True, "当前目录"
        
        # 现在处理绝对路径
        if normalized_path == "/":
            return self.root, True, "根目录"
            
        # 从根开始查找
        current_node = self.root
        path_parts = normalized_path[1:].split("/")
        
        # 逐层查找
        for i, part in enumerate(path_parts):
            if not part:
                continue
            
            child = current_node.find_child(part)
            if not child:
                remaining_path = "/".join(path_parts[i:])
                return None, False, f"路径 '{remaining_path}' 不存在"
            
            current_node = child
        
        return current_node, True, f"路径解析成功"
    
    def _get_parent_directory_and_name(self, path):
        """从路径中分离出父目录和文件/目录名"""
        normalized_path = self._normalize_path(path)
        
        if not normalized_path or normalized_path == "/":
            return self.root, "/"
        
        if "/" not in normalized_path:
            # 当前目录下的文件/目录
            return self.current_dir, normalized_path
        
        # 分离路径和名称
        if normalized_path.startswith("/"):
            # 绝对路径
            parts = normalized_path[1:].split("/")
            if len(parts) == 1:
                return self.root, parts[0]
            
            parent_path = "/" + "/".join(parts[:-1])
            name = parts[-1]
        else:
            # 相对路径
            parts = normalized_path.split("/")
            if len(parts) == 1:
                return self.current_dir, parts[0]
            
            parent_path = "/".join(parts[:-1])
            name = parts[-1]
        
        parent_node, success, msg = self._resolve_path(parent_path)
        if not success:
            return None, None
        
        if not parent_node.fcb.is_directory:
            return None, None
        
        return parent_node, name

    def create_file_with_path(self, path, content=""):
        """支持路径的文件创建"""
        parent_node, filename = self._get_parent_directory_and_name(path)
        
        if parent_node is None:
            return False, f"路径 '{path}' 无效"
        
        if not parent_node.fcb.is_directory:
            return False, f"父路径不是目录"
        
        # 检查文件是否已存在
        if parent_node.find_child(filename):
            return False, f"文件 '{filename}' 已存在"
        
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
        file_fcb = FCB(filename, len(content), start_block if content else -1, is_directory=False)
        file_node = FileNode(file_fcb)
        parent_node.add_child(file_node)
        
        return True, f"文件 '{path}' 创建成功"
    
    def delete_file_with_path(self, path):
        """支持路径的文件删除"""
        parent_node, filename = self._get_parent_directory_and_name(path)
        
        if parent_node is None:
            return False, f"路径 '{path}' 无效"
        
        child = parent_node.find_child(filename)
        if not child:
            return False, f"文件 '{path}' 不存在"
        
        if child.fcb.is_directory:
            return False, f"'{path}' 是目录，请使用删除目录命令"
        
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
        
        parent_node.remove_child(filename)
        return True, f"文件 '{path}' 删除成功"
    
    def open_file_with_path(self, path, mode="r"):
        """支持路径的文件打开"""
        parent_node, filename = self._get_parent_directory_and_name(path)
        
        if parent_node is None:
            return None, f"路径 '{path}' 无效"
        
        child = parent_node.find_child(filename)
        if not child:
            return None, f"文件 '{path}' 不存在"
        
        if child.fcb.is_directory:
            return None, f"'{path}' 是目录，无法打开"
        
        if mode not in ["r", "w", "rw"]:
            return None, "无效的文件模式"
        
        file_id = self.next_file_id
        self.next_file_id += 1
        
        self.open_files[file_id] = {
            'node': child,
            'mode': mode,
            'position': 0        }
        
        child.fcb.last_access_time = datetime.now()
        return file_id, f"文件 '{path}' 打开成功"
    
    def create_directory_with_path(self, path):
        """支持路径的目录创建"""
        parent_node, dirname = self._get_parent_directory_and_name(path)
        
        if parent_node is None:
            return False, f"路径 '{path}' 无效"
        
        if not parent_node.fcb.is_directory:
            return False, f"父路径不是目录"
        
        if parent_node.find_child(dirname):
            return False, f"目录 '{dirname}' 已存在"
        
        dir_fcb = FCB(dirname, 0, -1, is_directory=True)
        dir_node = FileNode(dir_fcb)
        parent_node.add_child(dir_node)
        return True, f"目录 '{path}' 创建成功"
    
    def delete_directory_with_path(self, path, recursive=False, force=False, confirm_callback=None):
        """支持路径的目录删除 - 现在支持递归删除"""
        parent_node, dirname = self._get_parent_directory_and_name(path)
        
        if parent_node is None:
            return False, f"路径 '{path}' 无效"
        
        child = parent_node.find_child(dirname)
        if not child:
            return False, f"目录 '{path}' 不存在"
        
        if not child.fcb.is_directory:
            return False, f"'{path}' 不是目录"
        
        if child.children:
            if recursive:
                # 使用递归删除
                return self.delete_directory_recursive(path, force, confirm_callback)
            else:
                # 非递归模式，提供递归删除建议
                dir_info = self._get_directory_info(child, path)
                return False, {
                    'type': 'suggest_recursive',
                    'info': dir_info,
                    'message': f"目录 '{path}' 不为空，包含 {dir_info['total_files']} 个文件和 {dir_info['total_dirs']} 个子目录。使用 recursive=True 进行递归删除。"
                }
        
        parent_node.remove_child(dirname)
        return True, f"目录 '{path}' 删除成功"
    
    def list_directory_with_path(self, path=None):
        """支持路径的目录列表"""
        if path is None:
            # 使用当前目录
            target_node = self.current_dir
        else:
            target_node, success, msg = self._resolve_path(path)
            if not success:
                return None, msg
            
            if not target_node.fcb.is_directory:
                return None, f"'{path}' 不是目录"
        
        items = []
        for child in target_node.children:
            fcb = child.fcb
            item_type = "目录" if fcb.is_directory else "文件"
            items.append({
                'name': fcb.name,
                'type': item_type,
                'size': fcb.size,
                'created': fcb.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
                'modified': fcb.last_modification_time.strftime("%Y-%m-%d %H:%M:%S")
            })
        return items, "列表获取成功"
    
    def _get_directory_info(self, node, path=""):
        """获取目录信息，用于递归删除前的确认显示"""
        if not node.fcb.is_directory:
            return None
        
        info = {
            'path': path,
            'total_files': 0,
            'total_dirs': 0,
            'total_size': 0,
            'items': []
        }
        
        def count_recursive(current_node, current_path):
            for child in current_node.children:
                child_path = current_path + "/" + child.fcb.name if current_path else child.fcb.name
                
                if child.fcb.is_directory:
                    info['total_dirs'] += 1
                    info['items'].append(f"目录: {child_path}")
                    count_recursive(child, child_path)
                else:
                    info['total_files'] += 1
                    info['total_size'] += child.fcb.size
                    info['items'].append(f"文件: {child_path} ({child.fcb.size} bytes)")
        
        count_recursive(node, "")
        return info
    
    def _recursive_delete_directory(self, node):
        """内部递归删除目录的实现"""
        if not node.fcb.is_directory:
            return False, "不是目录"
        
        deleted_files = 0
        deleted_dirs = 0
        
        # 递归删除所有子项
        for child in list(node.children):  # 使用 list() 创建副本避免迭代时修改
            if child.fcb.is_directory:
                # 递归删除子目录
                success, msg = self._recursive_delete_directory(child)
                if success:
                    deleted_dirs += 1
                else:
                    return False, f"删除子目录 {child.fcb.name} 失败: {msg}"
            else:
                # 删除文件
                if child.fcb.start_block != -1:
                    blocks = self.fat.get_file_blocks(child.fcb.start_block)
                    for block in blocks:
                        self.bitmap.free_block(block)
                    self.fat.free_blocks(child.fcb.start_block)
                
                # 关闭打开的文件
                for file_id, file_info in list(self.open_files.items()):
                    if file_info['node'] == child:
                        del self.open_files[file_id]
                
                deleted_files += 1
            
            # 从父目录移除
            node.remove_child(child.fcb.name)
        
        return True, f"已删除 {deleted_files} 个文件和 {deleted_dirs} 个目录"
    
    def delete_directory_recursive(self, name, force=False, confirm_callback=None):
        """递归删除目录及其所有内容
        
        Args:
            name: 目录名或路径
            force: 是否强制删除（跳过确认）
            confirm_callback: 确认回调函数，接收目录信息，返回 True/False
        
        Returns:
            (success, message)
        """
        # 解析目标目录
        if "/" in name:
            parent_node, dirname = self._get_parent_directory_and_name(name)
            if parent_node is None:
                return False, f"路径 '{name}' 无效"
            target = parent_node.find_child(dirname)
            target_path = name
        else:
            target = self.current_dir.find_child(name)
            target_path = name
            parent_node = self.current_dir
        
        if not target:
            return False, f"目录 '{name}' 不存在"
        
        if not target.fcb.is_directory:
            return False, f"'{name}' 不是目录"
        
        # 如果目录为空，直接删除
        if not target.children:
            parent_node.remove_child(target.fcb.name)
            return True, f"空目录 '{name}' 删除成功"
        
        # 获取目录信息
        dir_info = self._get_directory_info(target, target_path)
        
        if not force:
            # 需要用户确认
            if confirm_callback:
                # 使用回调函数确认
                if not confirm_callback(dir_info):
                    return False, "用户取消删除操作"
            else:
                # 返回需要确认的信息
                return False, {
                    'type': 'confirmation_needed',
                    'info': dir_info,
                    'message': f"目录 '{name}' 不为空，包含 {dir_info['total_files']} 个文件和 {dir_info['total_dirs']} 个子目录"
                }
        
        # 执行递归删除
        success, msg = self._recursive_delete_directory(target)
        if success:
            # 删除目录本身
            parent_node.remove_child(target.fcb.name)
            return True, f"目录 '{name}' 及其内容递归删除成功: {msg}"
        else:
            return False, f"递归删除失败: {msg}"