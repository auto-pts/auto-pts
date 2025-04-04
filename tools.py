import subprocess
from pathlib import Path


def check_style():
    logs_dir = Path("logs/pep8")
    logs_dir.mkdir(parents=True, exist_ok=True)

    def run_tool(name, command, log_path):
        print(f"🔧 Running {name}...")
        with open(log_path, "w") as log_file:
            result = subprocess.run(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True
            )
        return result.returncode

    ruff_code = run_tool("Ruff", ["poetry", "run", "ruff", "check", ".", "--fix"], logs_dir / "ruff.log")
    isort_code = run_tool("isort", ["poetry", "run", "isort", "."], logs_dir / "isort.log")

    print("\n Summary:")
    print(f"• Ruff exit code:  {ruff_code}")
    print(f"• isort exit code: {isort_code}")

    if isort_code == 0 and ruff_code == 0:
        print("\n All formatting and style checks passed!")
    else:
        print("\n Some tools reported issues. See logs in logs/pep8/ for details.")
