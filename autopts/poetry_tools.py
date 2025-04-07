import subprocess
from pathlib import Path


def run_tool(name: str, command: list[str], log_path: Path) -> int:
    """Uruchamia narzędzie i zapisuje log do wskazanego pliku."""
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

    # ruff_log = logs_dir / "ruff_fix.log"
    isort_log = logs_dir / "isort_fix.log"

    # ruff_code = run_tool("Ruff (fix)", ["poetry", "run", "ruff", "check", ".", "--fix"], ruff_log)
    isort_code = run_tool("isort (fix)", ["poetry", "run", "isort", "."], isort_log)

    print("\n Summary:")
    # print(f"• Ruff exit code:  {ruff_code}")
    print(f"• isort exit code: {isort_code}")

    # if isort_code == 0 and ruff_code == 0:
    if isort_code == 0:
        print("\n All formatting and style fixes applied successfully!")
    else:
        print("\n Some tools reported issues. See logs in logs/pep8/ for details.")


def check_isort():
    logs_dir = Path("./logs/pep8")
    logs_dir.mkdir(parents=True, exist_ok=True)

    isort_check_log = logs_dir / "isort_check.log"
    check_isort = run_tool("isort (check-only)", ["poetry", "run", "isort", ".", "--check-only"], isort_check_log)

    print("\n Summary:")
    print(f"• Check sort exit code:  {check_isort}")

    if check_isort == 0:
        print("\n isort check passed.")
    else:
        print("\n isort check find a errors. See log for details.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Use: python poetry_tools.py [check|fix]")
        sys.exit(1)

    if sys.argv[1] == "check":
        check_isort()
    elif sys.argv[1] == "fix":
        fix_style()
    else:
        print(f"Unknow command: {sys.argv[1]}")
        sys.exit(1)
