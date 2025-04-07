import subprocess
from pathlib import Path


def run_tool(name: str, command: list[str], log_path: Path) -> int:
    print(f"🔧 Running {name}...")
    with open(log_path, "w") as log_file:
        result = subprocess.run(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True
        )
    return result.returncode


def fix_style():
    logs_dir = Path("./logs/pep8")
    logs_dir.mkdir(parents=True, exist_ok=True)

    ruff_log = logs_dir / "ruff_fix.log"

    ruff_code = run_tool("ruff (fix)", ["poetry", "run", "ruff", "check", ".", "--fix"], ruff_log)

    print("\n Summary:")
    print(f"• ruff exit code:  {ruff_code}")

    if ruff_code == 0:
        print("\n All formatting and style fixes applied successfully!")
    else:
        print("\n Some tools reported issues. See logs in logs/pep8/ for details.")

def check_style():
    logs_dir = Path("./logs/pep8")
    logs_dir.mkdir(parents=True, exist_ok=True)

    ruff_check_log = logs_dir / "ruff_check.log"
    check_ruff = run_tool("ruff (check-only)", ["poetry", "run", "ruff", "check", "."], ruff_check_log)

    if check_ruff == 0:
        print("\n All style checks passed.")
    else:
        print("\nStyle issues detected. Please check the logs in logs/pep8/.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python style_tools.py [fix|check]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "fix":
        fix_style()
    elif command == "check":
        check_style()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python style_tools.py [fix|check]")
        sys.exit(1)
