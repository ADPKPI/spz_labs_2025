import unittest
from virtfs.virt_filesys import VirtualFS

class NewVFSTestSuite(unittest.TestCase):
    def test_file_creation_and_status(self):
        vfs = VirtualFS()
        vfs.make_file("alpha.txt")
        vfs.status_report("alpha.txt")
        vfs.status_report("/")

    def test_directory_navigation(self):
        vfs = VirtualFS()
        vfs.make_directory("docs")
        vfs.make_file("report.doc")
        vfs.make_file("./docs/chapter1.txt")
        vfs.make_file("./docs/chapter2.txt")
        vfs.switch_directory("docs")
        vfs.list_directory()
        vfs.switch_directory("..")
        vfs.status_report("docs")

    def test_hardlink_and_read_consistency(self):
        vfs = VirtualFS()
        vfs.make_file("data.bin")
        vfs.make_hardlink("data.bin", "backup.bin")
        vfs.status_report("data.bin")
        vfs.open_item("data.bin")
        vfs.write_data(0, 5)
        vfs.open_item("backup.bin")
        vfs.read_data(1, 5)

    def test_file_opening_closing(self):
        vfs = VirtualFS()
        vfs.make_file("log.txt")
        vfs.open_item("log.txt")
        vfs.close_item(0)
        vfs.open_item("log.txt")
        vfs.close_item(0)

    def test_offset_adjustment_and_writing(self):
        vfs = VirtualFS()
        vfs.make_file("temp.dat")
        vfs.open_item("temp.dat")
        vfs.move_offset(0, 4)
        vfs.write_data(0, 4)
        vfs.move_offset(0, 2)

    def test_resize_and_status_change(self):
        vfs = VirtualFS()
        vfs.make_file("image.png")
        vfs.status_report("image.png")
        vfs.resize_item("image.png", 16)
        vfs.status_report("image.png")

    def test_directory_deletion_after_file_removal(self):
        vfs = VirtualFS()
        vfs.make_directory("obsolete")
        vfs.make_file("./obsolete/old.log")
        vfs.switch_directory("obsolete")
        vfs.list_directory()
        vfs.switch_directory("..")
        vfs.delete_hardlink("./obsolete/old.log")
        vfs.delete_directory("obsolete")

    def test_symlink_creation_and_access(self):
        vfs = VirtualFS()
        vfs.make_directory("project")
        vfs.make_symlink("project", "proj_link")
        vfs.status_report("proj_link")
        vfs.list_directory()

    def test_handling_invalid_paths(self):
        vfs = VirtualFS()
        vfs.open_item("nonexistent_file")
        vfs.switch_directory("nonexistent_dir")

    def test_multiple_file_descriptors(self):
        vfs = VirtualFS()
        vfs.make_file("a.txt")
        vfs.make_file("b.txt")
        vfs.make_file("c.txt")
        vfs.open_item("a.txt")
        vfs.open_item("b.txt")
        vfs.open_item("c.txt")
        vfs.close_item(0)
        vfs.close_item(1)
        vfs.close_item(2)

if __name__ == '__main__':
    unittest.main()

