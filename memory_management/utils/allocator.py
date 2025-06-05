from .constants import AllocatingAlgorithm

class Allocator:
    def __init__(self, mem_size: int):
        self.mem_size = mem_size
        self.free_mem = [(0 , mem_size)]
        self.free_mem_sort_by_size = [(0 , mem_size)]
        self.allocated_mem = {}

    def FirstFit(self, size: int):
        success, start = False, -1
        for free_block in self.free_mem:
            if free_block[1] >= size:
                start = free_block[0]
                success = True
                break
        return success, start
    
    def BestFit(self, size: int):
        success, start = False, -1
        for free_block in self.free_mem_sort_by_size:
            if free_block[1] >= size:
                start = free_block[0]
                success = True
                break
        return success, start

    def allocate(self, pid, size: int, algorithm: AllocatingAlgorithm):
        if algorithm == AllocatingAlgorithm.FIRST_FIT:
            success, start = self.FirstFit(size)
        elif algorithm == AllocatingAlgorithm.BEST_FIT:
            success, start = self.BestFit(size)
        else:
            raise ValueError("Unknown allocation algorithm")
        if success:
            self.allocated_mem[pid] = (start, size)
            for free_block in self.free_mem:
                if free_block[0] <= start < free_block[0] + free_block[1]:
                    index = self.free_mem.index(free_block)
                    if size < free_block[1]:
                        if free_block[0] < start:
                            new_free_block1 = (free_block[0], start - free_block[0])           
                            self.free_mem.insert(index, new_free_block1)
                            index += 1
                        if start + size < free_block[0] + free_block[1]:
                            new_free_block2 = (start + size, free_block[0] + free_block[1] - (start + size))
                            self.free_mem.insert(index, new_free_block2)
                    self.free_mem.remove(free_block)
                    self.free_mem_sort_by_size= sorted(self.free_mem, key=lambda x: x[1])
                    return True
        return False
    
    def free(self, pid):
        if pid in self.allocated_mem:
            start, size = self.allocated_mem[pid]
            self.free_mem.append((start, size))
            self.free_mem.sort(key=lambda x: x[0])
            self.free_mem_sort_by_size = sorted(self.free_mem, key=lambda x: x[1])
            del self.allocated_mem[pid]
            self.merge_free_blocks()
            return True
        return False
    
    def merge_free_blocks(self):
        mem_len = len(self.free_mem)
        if mem_len <= 1:
            return
        
        merged = True
        while merged:
            merged = False
            for i in range(len(self.free_mem) - 1):
                if self.free_mem[i][0] + self.free_mem[i][1] == self.free_mem[i + 1][0]:
                    self.free_mem[i] = (self.free_mem[i][0], self.free_mem[i][1] + self.free_mem[i + 1][1])
                    del self.free_mem[i + 1]
                    merged = True
                    break
        self.free_mem_sort_by_size = sorted(self.free_mem, key=lambda x: x[1])
    
    def get_memory_status(self):
        """获取当前内存状态的详细信息"""
        total_free = sum(block[1] for block in self.free_mem)
        total_allocated = sum(block[1] for block in self.allocated_mem.values())
        
        return {
            'total_memory': self.mem_size,
            'total_free': total_free,
            'total_allocated': total_allocated,
            'free_blocks': sorted(self.free_mem, key=lambda x: x[0]),
            'allocated_blocks': dict(self.allocated_mem),
            'fragmentation_ratio': len(self.free_mem) / self.mem_size if self.mem_size > 0 else 0
        }
    
    def print_memory_layout(self):
        """打印内存布局的可视化表示"""
        print(f"总内存大小: {self.mem_size}")
        print(f"空闲块: {sorted(self.free_mem, key=lambda x: x[0])}")
        print(f"已分配块: {self.allocated_mem}")
        
        # 创建内存地址到进程ID的映射
        memory_map = ['FREE'] * self.mem_size
        for pid, (start, size) in self.allocated_mem.items():
            for i in range(start, start + size):
                memory_map[i] = f'P{pid}'
        
        # 打印简化的内存布局
        print("内存布局 (前100个单位):")
        if self.mem_size <= 100:
            layout = ''.join('█' if addr != 'FREE' else '░' for addr in memory_map)
            print(f"[{layout}]")
        else:
            # 对于大内存，只显示前100个单位
            layout = ''.join('█' if addr != 'FREE' else '░' for addr in memory_map[:100])
            print(f"[{layout}...]")
        print("█ = 已分配, ░ = 空闲")