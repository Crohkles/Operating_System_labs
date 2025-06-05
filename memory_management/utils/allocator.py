from constants import AllocatingAlgorithm

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
                    if size < free_block[1]:
                        if free_block[0] < start:
                            new_free_block1 = (free_block[0], start - free_block[0])           
                            index = self.free_mem.index(free_block)
                            self.free_mem.insert(index, new_free_block1)
                        if start + size < free_block[0] + free_block[1]:
                            new_free_block2 = (start + size, free_block[0] + free_block[1] - (start + size))
                            index+=1
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
        len = len(self.free_mem)
        if len <= 1:
            return
        merged = False
        while True:
            for i in range(len - 2):
                if self.free_mem[i][0] + self.free_mem[i][1] == self.free_mem[i + 1][0]:
                    self.free_mem[i] = (self.free_mem[i][0], self.free_mem[i][1] + self.free_mem[i + 1][1])
                    del self.free_mem[i + 1]
                    merged = True
                    break
            if not merged:
                break
        self.free_mem_sort_by_size = sorted(self.free_mem, key=lambda x: x[1])