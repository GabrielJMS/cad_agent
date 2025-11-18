"""
Secure CAD Executor Tool

This tool provides secure execution of Build123D code in a dedicated Docker container
with all CAD dependencies properly installed. This is the production-ready solution
for CAD code execution that maintains security while providing full Build123D functionality.
"""

import docker
import tempfile
import os
import json
import tarfile
import io
from typing import Dict, Any, List, Optional
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import Field, PrivateAttr, model_validator


class SecureCADExecutor(BaseTool):
    """
    Secure CAD code executor using Docker container with Build123D.

    This tool provides a secure, isolated environment for executing Build123D code
    with all necessary dependencies pre-installed. It's designed for production use
    where security and reliability are paramount.
    """

    name: str = "Secure CAD Executor"
    description: str = """
    Execute Build123D CAD code in a secure Docker container with all dependencies.

    Use this tool to:
    - Test and validate Build123D sketch code
    - Execute 3D modeling operations
    - Generate CAD files (STEP, STL)
    - Perform engineering calculations
    - Validate geometry and exports

    The tool provides a secure, isolated environment with Build123D, numpy,
    and other CAD libraries pre-installed. All code execution is sandboxed
    and time-limited for security.
    """

    # Pydantic fields
    container_name: str = Field(default="cad-agent-executor")
    image_name: str = Field(default="cad-agent-executor:latest")
    output_dir: Path = Field(default_factory=lambda: Path("outputs/generated_code"))
    cad_dir: Path = Field(default_factory=lambda: Path("outputs/cad_files"))
    
    # Private attributes (not part of serialization)
    _docker_client: Optional[Any] = PrivateAttr(default=None)

    @model_validator(mode='after')
    def initialize_tool(self):
        """Initialize directories and Docker client after model validation."""
        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cad_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Docker client
        try:
            self._docker_client = docker.from_env()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Docker client: {e}")
        
        return self
    
    @property
    def docker_client(self):
        """Property to access the private Docker client."""
        if self._docker_client is None:
            self._docker_client = docker.from_env()
        return self._docker_client

    def _build_image_if_needed(self):
        """Build the Docker image if it doesn't exist."""
        try:
            self.docker_client.images.get(self.image_name)
        except docker.errors.ImageNotFound:
            # Build the image
            dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile.cad_executor"
            if not dockerfile_path.exists():
                raise FileNotFoundError(f"Dockerfile not found at {dockerfile_path}")

            print("Building CAD executor Docker image...")
            self.docker_client.images.build(
                path=str(dockerfile_path.parent),
                dockerfile="Dockerfile.cad_executor",
                tag=self.image_name
            )
            print("Docker image built successfully")

    def _run(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Execute CAD code in a secure Docker container.

        Args:
            code: The Build123D/Python code to execute

        Returns:
            Dictionary with execution results
        """
        try:
            # Ensure Docker image exists
            self._build_image_if_needed()

            # Prepare the complete code with setup
            full_code = self._prepare_code(code)

            # Create temporary directory for code exchange
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code to file
                code_file = Path(temp_dir) / "cad_code.py"
                with open(code_file, 'w') as f:
                    f.write(full_code)

                # Create a tar archive with the code
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    tar.add(code_file, arcname="cad_code.py")
                tar_stream.seek(0)

                # Remove any existing container
                self._cleanup_container()

                # Create and run container
                container = self.docker_client.containers.create(
                    image=self.image_name,
                    name=self.container_name,
                    working_dir="/app",
                    command=["python", "cad_code.py"],
                    volumes={
                        str(self.output_dir): {"bind": "/app/outputs/generated_code", "mode": "rw"},
                        str(self.cad_dir): {"bind": "/app/outputs/cad_files", "mode": "rw"}
                    },
                    mem_limit="512m",  # Memory limit
                    cpu_quota=50000,    # CPU limit (50% of one core)
                    network_mode="none",  # No network access for security
                    remove=True
                )

                # Copy code to container
                container.put_archive("/app", tar_stream)

                # Start the container
                container.start()

                # Wait for completion with timeout
                try:
                    result = container.wait(timeout=60)  # 60 second timeout
                except docker.errors.APIError:
                    container.stop()
                    container.remove()
                    return {
                        "success": False,
                        "output": "",
                        "error": "Execution timed out",
                        "files_created": [],
                        "return_code": -1
                    }

                # Get logs
                logs = container.logs().decode('utf-8')

                # Get created files
                files_created = self._get_created_files()

                return {
                    "success": result['StatusCode'] == 0,
                    "output": logs,
                    "error": None if result['StatusCode'] == 0 else f"Exit code: {result['StatusCode']}",
                    "files_created": files_created,
                    "return_code": result['StatusCode']
                }

        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Failed to execute CAD code: {str(e)}",
                "files_created": [],
                "return_code": -1
            }
        finally:
            self._cleanup_container()

    def _prepare_code(self, user_code: str) -> str:
        """Prepare user code with proper imports and error handling."""
        imports = [
            "import sys",
            "import os",
            "import traceback",
            "from pathlib import Path",
            "",
            "# CAD imports with error handling",
            "try:",
            "    from build123d import *",
            "    BUILD123D_AVAILABLE = True",
            "    print('Build123D imported successfully')",
            "except ImportError as e:",
            "    BUILD123D_AVAILABLE = False",
            "    print(f'Warning: Build123D not available: {e}')",
            "",
            "# Additional imports",
            "import numpy as np",
            "",
            "# Setup output directories",
            "output_dir = Path('/app/outputs/generated_code')",
            "cad_dir = Path('/app/outputs/cad_files')",
            "step_dir = cad_dir / 'step'",
            "stl_dir = cad_dir / 'stl'",
            "",
            "output_dir.mkdir(parents=True, exist_ok=True)",
            "cad_dir.mkdir(parents=True, exist_ok=True)",
            "step_dir.mkdir(parents=True, exist_ok=True)",
            "stl_dir.mkdir(parents=True, exist_ok=True)",
            "",
            "# User code:",
            "print('=' * 50)",
            "print('Executing CAD code...')",
            "print('=' * 50)",
        ]

        # Wrap user code in try-catch
        wrapped_code = [
            "try:",
        ]

        for line in user_code.split('\n'):
            wrapped_code.append(f"    {line}")

        wrapped_code.extend([
            "",
            "    print('✅ CAD code executed successfully')",
            "    ",
            "    # List generated files",
            "    for pattern in ['*.step', '*.stp', '*.stl', '*.brep', '*.py']:",
            "        for file_path in output_dir.glob(pattern):",
            "            if file_path.is_file():",
            "                print(f'📁 Generated: {file_path.name}')",
            "                ",
            "except Exception as e:",
            "    print(f'❌ Error in CAD code: {e}')",
            "    traceback.print_exc()",
            "    sys.exit(1)",
            "",
            "print('=' * 50)",
            "print('CAD execution completed')",
            "print('=' * 50)",
        ])

        return '\n'.join(imports) + '\n' + '\n'.join(wrapped_code)

    def _get_created_files(self) -> List[Dict[str, Any]]:
        """Get list of files created during execution."""
        files_created = []

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

    def _cleanup_container(self):
        """Clean up any existing container."""
        try:
            container = self.docker_client.containers.get(self.container_name)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            pass
        except Exception:
            pass

    async def _arun(self, code: str, **kwargs) -> Dict[str, Any]:
        """Async version of the run method."""
        return self._run(code, **kwargs)