from typing import Dict, List, Tuple

class FSNode:
    """Base class for all filesystem entities."""
    def __init__(self, name: str, is_dir: bool):
        self.name = name
        self.is_dir = is_dir

class File(FSNode):
    def __init__(self, name: str):
        super().__init__(name, is_dir=False)
        self.content: str = ""

class Directory(FSNode):
    def __init__(self, name: str):
        super().__init__(name, is_dir=True)
        # Maps child name -> FSNode
        self.children: Dict[str, FSNode] = {}

class FileSystemManager:
    def __init__(self):
        self.root = Directory("/")

    def _parse_path(self, path: str) -> List[str]:
        if not path.startswith("/"):
            raise ValueError("Only absolute paths starting with '/' are supported.")
        # Filter out empty strings caused by consecutive or trailing slashes
        return [p for p in path.split("/") if p]

    def _resolve_parent(self, path: str) -> Tuple[Directory, str]:
        """
        Traverses the path to find the target's parent directory.
        Returns (ParentDirectory, TargetName).
        """
        parts = self._parse_path(path)
        if not parts:
            raise ValueError("Cannot resolve parent of the root directory.")

        target_name = parts[-1]
        current_node = self.root

        for part in parts[:-1]:
            if part not in current_node.children:
                raise FileNotFoundError(f"Path not found: '{part}'")
            
            next_node = current_node.children[part]
            if not next_node.is_dir:
                raise NotADirectoryError(f"'{part}' is a file, not a directory.")
            
            # Safe to cast because of the is_dir check
            current_node = next_node  # type: ignore

        return current_node, target_name

    def mkdir(self, path: str) -> None:
        """Creates a new directory."""
        parent_dir, target_name = self._resolve_parent(path)
        
        if target_name in parent_dir.children:
            raise FileExistsError(f"'{target_name}' already exists.")
            
        parent_dir.children[target_name] = Directory(target_name)

    def create(self, path: str) -> None:
        """Creates a new empty file."""
        parent_dir, target_name = self._resolve_parent(path)
        
        if target_name in parent_dir.children:
            raise FileExistsError(f"'{target_name}' already exists.")
            
        parent_dir.children[target_name] = File(target_name)

    def write(self, path: str, content: str) -> None:
        """Overwrites the content of a file."""
        parent_dir, target_name = self._resolve_parent(path)
        
        if target_name not in parent_dir.children:
            raise FileNotFoundError(f"'{target_name}' not found.")
            
        target_node = parent_dir.children[target_name]
        if target_node.is_dir:
            raise IsADirectoryError(f"'{target_name}' is a directory.")
            
        target_node.content = content  # type: ignore

    def read(self, path: str) -> str:
        """Reads and returns the content of a file."""
        parent_dir, target_name = self._resolve_parent(path)
        
        if target_name not in parent_dir.children:
            raise FileNotFoundError(f"'{target_name}' not found.")
            
        target_node = parent_dir.children[target_name]
        if target_node.is_dir:
            raise IsADirectoryError(f"'{target_name}' is a directory.")
            
        return target_node.content  # type: ignore

    def delete(self, path: str) -> None:
        """Deletes a file or an empty directory."""
        parent_dir, target_name = self._resolve_parent(path)
        
        if target_name not in parent_dir.children:
            raise FileNotFoundError(f"'{target_name}' not found.")
            
        target_node = parent_dir.children[target_name]
        
        if target_node.is_dir and len(target_node.children) > 0: # type: ignore
            raise OSError(f"Directory '{target_name}' is not empty.")
            
        del parent_dir.children[target_name]

    def ls(self, path: str = "/") -> List[str]:
        """Lists the names of files and directories in the given path."""
        if path == "/":
            return list(self.root.children.keys())
            
        parent_dir, target_name = self._resolve_parent(path)
        
        if target_name not in parent_dir.children:
            raise FileNotFoundError(f"'{target_name}' not found.")
            
        target_node = parent_dir.children[target_name]
        if not target_node.is_dir:
            raise NotADirectoryError(f"'{target_name}' is not a directory.")
            
        return list(target_node.children.keys()) # type: ignore