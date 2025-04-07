#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, Codecoup.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#

"""
The compatibility.csv file contains 3 columns, PTS version, AutoPTS repo hash
and project repo hash. Each row denotes a compatible set of versions.
The script allows to match the compatible set for the given version/hash.

Example content of compatibility.csv:
PTS, AutoPTS, Zephyr
8.5.3.4 83d868cf2d6d2021e105077715e9c627d078532e 3247a1db81831c76f873258ac8646923d0271031
8.5.3.4 459e7613f362d85ed2569d9ab810e4f02e9819fb 8e20b80575b888468136dc2efbb230f66930b941
8.5.3.4 b3e76c407bd99cd22af10483f761e7509133de6e b802e42c6f930d94269d41432b2baed74856f4f0
8.5.2.5 d28f1237e3863eb220ab898ba9f864fe338b07b5 547ffdab6e16bfde8d9fc6d49872c110d46e099c

The rows have to be sorted so the first row after header contains the latest versions.
"""

import subprocess
import sys
from os.path import abspath, dirname

from dateutil import parser


def get_hash_from_reference(repo_path, reference):
    return subprocess.check_output(
        f"git rev-parse {reference}", shell=True, cwd=repo_path).decode().strip()


def get_commit_timestamp(commit_hash, repo_path):
    date_str = subprocess.check_output(f'git show -s --format=%cd --date=iso {commit_hash}',
                                       cwd=repo_path, shell=True, env=None).decode().strip()

    return parser.parse(date_str)


def get_top_commit(commit_hashes, repo_path):
    return subprocess.check_output(f'git rev-list -n1 --topo-order {" ".join(commit_hashes)}',
                                   cwd=repo_path).decode().strip()


def get_newer_commit(commit_hash1, commit_hash2, repo_path):
    timestamp1 = get_commit_timestamp(commit_hash1, repo_path)
    timestamp2 = get_commit_timestamp(commit_hash2, repo_path)

    if timestamp1 > timestamp2:
        return commit_hash1
    elif timestamp1 < timestamp2:
        return commit_hash2
    else:
        return get_top_commit([commit_hash1, commit_hash2], repo_path)


def next_version_generator(path):
    with open(path) as file:
        for line in file:
            if not line:
                continue

            pts_ver, autopts_hash, project_hash = line.split(' ')
            yield pts_ver, autopts_hash, project_hash


def find_latest(csv_file_path):
    generator = next_version_generator(csv_file_path)
    next(generator)  # Skip header
    return next(generator)


def find_by_pts_ver(csv_file_path, version):
    generator = next_version_generator(csv_file_path)
    next(generator)  # Skip header

    for pts_ver, autopts_hash, project_hash in generator:
        if pts_ver == version:
            return pts_ver, autopts_hash, project_hash

    return None, None, None


def find_by_autopts_hash(csv_file_path, autopts_repo, commit_hash):
    """
    Finds matching versions for the given auto-pts repo hash
    params: csv_file_path - path to compatibility.csv
    params: autopts_repo - path to local auto-pts repo
    params: commit_hash - auto-pts repo hash
    """
    generator = next_version_generator(csv_file_path)
    next(generator)  # Skip header

    for pts_ver, autopts_hash, project_hash in generator:
        newer_hash = get_newer_commit(autopts_hash, commit_hash, autopts_repo)

        if commit_hash == newer_hash:
            return pts_ver, autopts_hash, project_hash

    return None, None, None


def find_by_project_hash(csv_file_path, project_repo, commit_hash):
    """
    Finds matching versions for the given project repo hash
    params: csv_file_path - path to compatibility.csv
    params: project_repo - path to local project repo
    params: commit_hash - hash of the project repo
    """
    generator = next_version_generator(csv_file_path)
    next(generator)  # Skip header

    for pts_ver, autopts_hash, project_hash in generator:
        newer_hash = get_newer_commit(project_hash, commit_hash, project_repo)

        if commit_hash == newer_hash:
            return pts_ver, autopts_hash, project_hash

    return None, None, None


def main():
    autopts_repo = dirname(dirname(dirname(abspath(__file__))))
    sys.path.extend([autopts_repo])

    BY_PTS_VER = 0
    BY_AUTOPTS_HASH = 1
    BY_PROJECT_HASH = 2

    mode = int(input("""Select mode
0: Find by PTS version,
1: Find by auto-pts repo hash
2: Find by project repo hash
"""))

    csv_path = input('Path to the compatibility.csv: ')

    if mode == BY_PTS_VER:
        pts_version = input('Enter PTS version (e.g. 8.5.3.4): ')
        result = find_by_pts_ver(csv_path, pts_version)

    elif mode == BY_AUTOPTS_HASH:
        repo_path = input(f'Enter path to auto-pts repo [{autopts_repo}]: ') or autopts_repo
        commit_hash = input('Enter commit hash of auto-pts repo: ')
        result = find_by_autopts_hash(csv_path, repo_path, commit_hash)

    elif mode == BY_PROJECT_HASH:
        repo_path = input('Enter path to project repo: ')
        commit_hash = input('Enter commit hash of project repo: ')
        result = find_by_project_hash(csv_path, repo_path, commit_hash)

    else:
        print(f'Invalid mode {mode}')
        return

    print('PTS version | AutoPTS hash | Project hash')
    print(' | '.join(result))


if __name__ == '__main__':
    main()
