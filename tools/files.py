import os
import shutil

class FileTool:
    @staticmethod
    def read_file(file_path: str) -> str:
        """Safely reads the contents of a text file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    @staticmethod
    def write_file(file_path: str, content: str) -> str:
        """Writes content to a file, automatically creating parent directories if needed."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    @staticmethod
    def list_directory(dir_path: str = ".") -> list:
        """Lists files and folders within a given directory path."""
        try:
            return os.listdir(dir_path)
        except Exception as e:
            return [f"Error listing directory: {str(e)}"]

    @staticmethod
    def delete_file(file_path: str) -> str:
        """Deletes a specified file or directory."""
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            return f"Successfully deleted {file_path}"
        except Exception as e:
            return f"Error deleting path: {str(e)}"
          
