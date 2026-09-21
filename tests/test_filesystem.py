import unittest
from filesystem.fs import FileSystemManager

class TestFileSystemManager(unittest.TestCase):

    def setUp(self):
        self.fs = FileSystemManager()

    def test_mkdir_and_ls(self):
        self.fs.mkdir("/home")
        self.fs.mkdir("/home/user")
        self.fs.mkdir("/home/user/docs")
        
        # Check root
        self.assertEqual(self.fs.ls("/"), ["home"])
        # Check nested
        self.assertEqual(self.fs.ls("/home/user"), ["docs"])

    def test_file_create_read_write(self):
        self.fs.mkdir("/etc")
        self.fs.create("/etc/config.txt")
        
        # Read empty file
        self.assertEqual(self.fs.read("/etc/config.txt"), "")
        
        # Write and read
        self.fs.write("/etc/config.txt", "DEBUG=True")
        self.assertEqual(self.fs.read("/etc/config.txt"), "DEBUG=True")

        # Files should appear in ls
        self.assertIn("config.txt", self.fs.ls("/etc"))

    def test_delete_file_and_empty_directory(self):
        self.fs.mkdir("/tmp")
        self.fs.create("/tmp/cache.bin")
        
        # Delete file
        self.fs.delete("/tmp/cache.bin")
        self.assertEqual(self.fs.ls("/tmp"), [])
        
        # Delete empty directory
        self.fs.delete("/tmp")
        self.assertEqual(self.fs.ls("/"), [])

    def test_error_create_existing(self):
        self.fs.mkdir("/var")
        with self.assertRaises(FileExistsError):
            self.fs.mkdir("/var")

    def test_error_path_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.fs.mkdir("/usr/local/bin") # Parent /usr/local doesn't exist

    def test_error_not_a_directory(self):
        self.fs.create("/file.txt")
        with self.assertRaises(NotADirectoryError):
            # Attempting to make a directory inside a file
            self.fs.mkdir("/file.txt/nested")

        with self.assertRaises(NotADirectoryError):
            # Attempting to ls a file
            self.fs.ls("/file.txt")

    def test_error_is_a_directory(self):
        self.fs.mkdir("/home")
        with self.assertRaises(IsADirectoryError):
            self.fs.write("/home", "data")
            
        with self.assertRaises(IsADirectoryError):
            self.fs.read("/home")

    def test_error_delete_non_empty_directory(self):
        self.fs.mkdir("/home")
        self.fs.create("/home/file.txt")
        
        with self.assertRaises(OSError):
            self.fs.delete("/home")

    def test_error_relative_paths(self):
        with self.assertRaises(ValueError):
            self.fs.mkdir("home/user")

if __name__ == '__main__':
    unittest.main()