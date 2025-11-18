"""
Local Python Executor Tool

This tool provides Python code execution in the local environment
where Build123D and other CAD dependencies are already installed.
It replaces the Docker-based CodeInterpreterTool for CAD-specific tasks.
"""

import subprocess
import sys
import os
import tempfile
import traceback
from typing import Dict, Any
from pathlib import Path
from crewai_tools import BaseTool


class LocalPythonExecutor(BaseTool):
    """
    Executes Python code in the local environment with access to Build123D.

    This tool is specifically designed for CAD generation tasks where
    Build123D and related dependencies need to be available.
    """

    name: str = "Local Python Executor"
    description: str = """
    Execute Python code in the local environment where Build123D is installed.
    Use this tool to test and validate Build123D CAD code, perform calculations,
    and generate CAD models. The code has access to all installed packages
    including build123d, numpy, and other CAD libraries.

    Example usage:
    - Test Build123D sketch code
    - Validate 3D operations
    - Export CAD files to STEP/STL formats
    - Perform engineering calculations
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure output directories exist
        self.output_dir = Path("outputs/generated_code")
        self.cad_dir = Path("outputs/cad_files")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cad_dir.mkdir(parents=True, exist_ok=True)

    def _run(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Execute Python code in the local environment.

        Args:
            code: The Python code to execute

        Returns:
            Dictionary with execution results including:
            - success: Boolean indicating if execution succeeded
            - output: Standard output from execution
            - error: Error message if execution failed
            - files_created: List of generated files
        """
        try:
            # Create a temporary file for the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Write the code with proper imports and setup
                full_code = self._prepare_code(code)
                f.write(full_code)
                temp_file = f.name

            try:
                # Execute the code in the local environment
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30 second timeout
                    cwd=str(Path.cwd())
                )

                # Check for generated files
                files_created = self._find_generated_files()

                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None,
                    "files_created": files_created,
                    "return_code": result.returncode
                }

            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "output": "",
                    "error": "Code execution timed out after 30 seconds",
                    "files_created": [],
                    "return_code": -1
                }

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Failed to execute code: {str(e)}\n{traceback.format_exc()}",
                "files_created": [],
                "return_code": -1
            }

    def _prepare_code(self, user_code: str) -> str:
        """
        Prepare the user's code with necessary imports and setup.

        Args:
            user_code: The code provided by the user/agent

        Returns:
            Complete code ready for execution
        """
        # Prepare imports and setup
        imports = [
            "import sys",
            "import os",
            "from pathlib import Path",
            "import traceback",
            "",
            "# CAD imports",
            "try:",
            "    from build123d import *",
            "    BUILD123D_AVAILABLE = True",
            "except ImportError:",
            "    BUILD123D_AVAILABLE = False",
            "    print('Warning: build123d not available')",
            "",
            "# Set up output directories",
            "output_dir = Path('outputs/generated_code')",
            "cad_dir = Path('outputs/cad_files')",
            "step_dir = cad_dir / 'step'",
            "stl_dir = cad_dir / 'stl'",
            "",
            "output_dir.mkdir(parents=True, exist_ok=True)",
            "cad_dir.mkdir(parents=True, exist_ok=True)",
            "step_dir.mkdir(parents=True, exist_ok=True)",
            "stl_dir.mkdir(parents=True, exist_ok=True)",
            "",
            "# User code:",
        ]

        # Wrap user code in try-catch for better error handling
        wrapped_code = [
            "try:",
            "    # Execute user code with proper indentation",
        ]

        # Add user code with proper indentation
        for line in user_code.split('\n'):
            wrapped_code.append(f"    {line}")

        wrapped_code.extend([
            "except Exception as e:",
            "    print(f'Error in CAD code execution: {e}')",
            "    traceback.print_exc()",
            "    sys.exit(1)",
            "",
            "print('Code execution completed successfully')",
        ])

        return '\n'.join(imports) + '\n' + '\n'.join(wrapped_code)

    def _find_generated_files(self) -> list:
        """
        Find files created during code execution.

        Returns:
            List of dictionaries with file information
        """
        files_created = []

        # Check for CAD files
        for pattern in ["*.step", "*.stp", "*.stl", "*.brep", "*.py"]:
            for directory in [self.output_dir, self.cad_dir]:
                if directory.exists():
                    for file_path in directory.glob(pattern):
                        if file_path.is_file():
                            files_created.append({
                                "name": file_path.name,
                                "path": str(file_path),
                                "type": file_path.suffix,
                                "size": file_path.stat().st_size
                            })

        return files_created

    async def _arun(self, code: str, **kwargs) -> Dict[str, Any]:
        """Async version of the run method."""
        return self._run(code, **kwargs)