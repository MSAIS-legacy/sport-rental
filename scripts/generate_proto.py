import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "packages/runtime/src"
subprocess.run(
    [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{root}",
        f"--python_out={root}",
        f"--grpc_python_out={root}",
        str(root / "rental_runtime/proto/customers.proto"),
    ],
    check=True,
)
