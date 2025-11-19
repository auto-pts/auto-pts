#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2018, Intel Corporation.
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

import os
import pathlib

import git

from autopts import bot


def describe_repo(repo_path):
    """GIT Update sources
    :param repo_path: git repository path
    :return: Commit SHA at HEAD
    """
    repo = git.Repo(repo_path)

    return repo.git.describe('--always'), repo.git.show('-s', '--format=%H')


def update_sources(repo_path, remote, branch, stash_changes=False):
    """GIT Update sources
    :param repo_path: git repository path
    :param remote: git repository remote name
    :param branch: git repository branch name
    :param stash_changes: stash non-committed changes
    :return: Commit SHA at HEAD
    """
    repo = git.Repo(repo_path)

    print('Updating ' + repo_path)

    dirty = repo.is_dirty()
    if dirty and (not stash_changes):
        print('Repo is dirty. Not updating')
        return repo.git.describe('--always'), repo.git.show('-s', '--format=%H') + '-dirty'

    if dirty and stash_changes:
        print('Repo is dirty. Stashing changes')
        repo.git.stash('--include-untracked')

    repo.git.fetch(remote)
    repo.git.checkout(f'{remote}/{branch}')

    return describe_repo(repo_path)


def update_repos(project_path, git_config):
    """GIT Update sources
    :param project_path: path to project root
    :param git_config: dictionary with configuration of repositories
    :return: repos_dict with {key=repo name, {commit, desc}}
    """
    project_path = os.path.abspath(project_path)
    repos_dict = {}

    for repo, conf in list(git_config.items()):
        repo_dict = {}
        if not os.path.isabs(conf["path"]):
            repo_path = os.path.join(project_path, conf["path"])
        else:
            repo_path = os.path.abspath(conf["path"])

        if conf.get('update_repo', False):
            desc, commit = update_sources(repo_path, conf["remote"],
                                          conf["branch"], conf["stash_changes"])
        else:
            desc, commit = describe_repo(repo_path)

        repo_dict["commit"] = commit
        repo_dict["desc"] = desc
        repos_dict[repo] = repo_dict

        if conf.get('west_update', False):
            env_cmd = conf.get('west_update_env', None)
            env_cmd = env_cmd.split() + ['&&'] if env_cmd else []
            bot.common.check_call(env_cmd + ['west', 'update'], cwd=repo_path)

        if conf.get('rm_pycache', False):
            for p in pathlib.Path(repo_path).rglob('*.py[co]'):
                p.unlink()
            for p in pathlib.Path(repo_path).rglob('__pycache__'):
                p.rmdir()

    return repos_dict
