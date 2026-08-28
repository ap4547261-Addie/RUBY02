import subprocess
import sys

class ActionTool:
    @staticmethod
    def run_shell_command(command: str) -> dict:
        """Executes a local shell command and returns output logs, error status, and return code."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": "Command execution timed out.",
                "code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "code": -1
            }

    @staticmethod
    def run_python_script(script_path: str) -> dict:
        """Executes a target Python file using the current system interpreter."""
        cmd = f"{sys.executable} {script_path}"
        return ActionTool.run_shell_command(cmd)
      
