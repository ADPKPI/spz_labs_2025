from virtfs import vf_const
from virtfs.file_category import FileCategory
from virtfs.data_unit import DataUnit
class VirtualFileDesc:
    id_counter = 0
    ZERO_UNIT = DataUnit()
    def __init__(self, file_cat):
        self.desc_id = VirtualFileDesc.id_counter
        VirtualFileDesc.id_counter += 1
        self.file_cat = file_cat
        self.link_count = 1
        self.file_size = 0
        self.units = []
    def __str__(self):
        return "ID=" + str(self.desc_id) + ", Cat=" + str(self.file_cat) + ", Links=" + str(self.link_count) + ", Size=" + str(self.file_size) + ", Units=" + str(len(self.units))
    def retrieve_data(self, length, offset):
        unit_index = offset // vf_const.VFS_BLOCK_SIZE
        unit_offset = offset % vf_const.VFS_BLOCK_SIZE
        result = bytearray(length)
        got = 0
        while got < length:
            rem = vf_const.VFS_BLOCK_SIZE - unit_offset
            current_unit = self.units[unit_index] if unit_index < len(self.units) and self.units[unit_index] is not None else VirtualFileDesc.ZERO_UNIT
            if rem >= length - got:
                current_unit.fetch_unit(result, got, unit_offset, length - got)
                got = length
            else:
                current_unit.fetch_unit(result, got, unit_offset, rem)
                got += rem
                unit_index += 1
                unit_offset = 0
            if unit_index >= len(self.units):
                break
        return result
    def store_data(self, in_bytes, offset):
        if offset + len(in_bytes) >= len(self.units) * vf_const.VFS_BLOCK_SIZE:
            print("Недостатньо місця для збереження.")
            return False
        stored = 0
        unit_index = offset // vf_const.VFS_BLOCK_SIZE
        unit_offset = offset % vf_const.VFS_BLOCK_SIZE
        while stored < len(in_bytes):
            if unit_index >= len(self.units):
                break
            current_unit = self.units[unit_index]
            if current_unit is None:
                from virtfs.data_unit import DataUnit
                self.units[unit_index] = DataUnit()
                current_unit = self.units[unit_index]
            rem = vf_const.VFS_BLOCK_SIZE - unit_offset
            if rem >= len(in_bytes) - stored:
                current_unit.update_unit(in_bytes, len(in_bytes) - stored, unit_offset, len(in_bytes) - stored)
                stored = len(in_bytes)
            else:
                current_unit.update_unit(in_bytes, rem, unit_offset, rem)
                stored += rem
                unit_index += 1
                unit_offset = 0
        return True
    def adjust_size(self, new_size):
        new_count = new_size // vf_const.VFS_BLOCK_SIZE + 1
        if len(self.units) < new_count:
            self.units.extend([None]*(new_count - len(self.units)))
        elif len(self.units) > new_count:
            self.units = self.units[:new_count]
        self.file_size = new_size
