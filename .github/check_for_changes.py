import os
import subprocess
import sys


def main():
    # Check if the target directory exists
    if not os.path.exists('autopts/wid/'):
        print("Target directory 'autopts/wid/' does not exist.")
        sys.exit(1)

    try:
        pr_number = os.environ.get('PR_NUMBER')
        fetch_str = f"refs/pull/{pr_number}/merge"

        subprocess.run(
            ['git', 'fetch', 'origin', fetch_str],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )

        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD', 'FETCH_HEAD', '--', 'autopts/wid/'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )

        print(f"git diff output: {result.stdout}")

        changed_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e.stderr}")
        sys.exit(1)

    # Check if the target directory exists
    if not changed_files or all(file == '' for file in changed_files):
        print("No changes detected in autopts/wid directory.")
        sys.exit(1)

    filenames = []

    for file in changed_files:
        stripped_file = file.strip()
        base_name = os.path.basename(stripped_file)
        name_wo_ext, ext = os.path.splitext(base_name)

        if name_wo_ext == "__init__":
            continue

        if name_wo_ext == "gatt_client":
            name_wo_ext = "gatt/cl"

        upper_name = name_wo_ext.upper()
        filenames.append(upper_name)

        # Debug: Print the formatted filenames
    print(f"Formatted filenames: {filenames}")

    with open('changed_files_formatted.txt', 'w') as f:
        f.write(' '.join(filenames))

    sys.exit(0)


if __name__ == "__main__":
    main()
