class DataBlock:
    def __init__(self, size, prev_size=0, start_addr=0, used=False, terminal=False):
        self.size = size
        self.prev_size = prev_size
        self.start_addr = start_addr
        self.used = used
        self.terminal = terminal

def divide_block(segment, amount, META=24, MIN=16):
    segment.used = True
    remain = segment.size - amount
    if remain >= META + MIN:
        remain -= META
        segment.size = amount
        new_seg = DataBlock(remain)
        new_seg.start_addr = segment.start_addr + amount + META
        new_seg.prev_size = amount
        new_seg.terminal = segment.terminal
        if segment.terminal:
            segment.terminal = False
        return new_seg
    return None

def combine_blocks(base, target, META=24):
    base.size += target.size + META
    if target.terminal:
        base.terminal = True

def hint_unused(segment, PAGE=4096, META=24, NODE_SIZE=16):
    if (segment.size - NODE_SIZE) < PAGE:
        return
    addr_start = segment.start_addr
    page_start = (addr_start + META + NODE_SIZE + PAGE - 1) & ~(PAGE - 1)
    page_end = (addr_start + segment.size + META) & ~(PAGE - 1)
    if page_start == page_end:
        return
    dummy = bytearray(page_end - page_start)
    from kernel_core import reset_area
    reset_area(dummy, len(dummy))
