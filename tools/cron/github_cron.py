#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2023, Codecoup.
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

"""GitHub Cron for AutoPTS"""

import json
import logging
import re
import requests
from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from requests.structures import CaseInsensitiveDict

from autopts.utils import get_global_end

log = logging.info


def catch_connection_error(func):
    """Reruns REST API request in case of ConnectionError"""
    def _catch_exceptions(*args, **kwargs):
        while not get_global_end():
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                log('Internet connection error')
                sleep(1)
    return _catch_exceptions


class GitHubCron(Thread):
    """Implements some functions of the GitHub API and cyclic comment pulling
    for magic tags that will start a PR job.
    """
    base_url = 'https://api.github.com'

    def __init__(self, interval, magic_tags, repo_owner, repo_name,
                 permitted_logins, access_token=None, pull_time_offset=15,
                 schedule_delay=0, schedule_job_cb=None):
        super().__init__()
        self.config = {'base_url': self.base_url,
                       'owner': repo_owner,
                       'repo': repo_name,
                       'access_token': access_token
                       }
        # A flag to kill the pulling thread
        self.end = False
        # A flag to pause the pulling
        self.enabled = True
        # The repo address in GitHub
        self.name = f'{repo_owner}/{repo_name}'
        # The pulling interval
        self.interval = interval
        # A dictionary of magic tags that triggers PR jobs
        self.tags = magic_tags
        # Counter for skipping already processed comments
        self.last_comment_id = 0
        # A list of the authorized GitHub users for this repo
        self.permitted_logins = permitted_logins
        # How old may be the oldest comment (in minutes)
        self.pull_time_offset = pull_time_offset  # minutes before
        # Delay the start of the PR job (in minutes)
        self.schedule_delay = schedule_delay  # minutes after parsing GET response
        # Function to call when PR job needs to be scheduled
        self.schedule_job_cb = schedule_job_cb

    def check_token(self):
        if 'access_token' not in self.config or self.config['access_token'] is None:
            raise Exception('Github token was not provided')

    @catch_connection_error
    def get(self, url, params):
        # GET request (GitHub REST API)
        headers = CaseInsensitiveDict()
        if 'access_token' in self.config and self.config['access_token'] is not None:
            headers['Authorization'] = 'token {access_token}'.format(**self.config)

        resp = requests.get(url, params, headers=headers)

        return resp

    @catch_connection_error
    def post(self, url, params):
        # POST request (GitHub REST API)
        headers = CaseInsensitiveDict()
        if 'access_token' in self.config and self.config['access_token'] is not None:
            headers['Authorization'] = 'token {access_token}'.format(**self.config)

        resp = requests.post(url, data=json.dumps(params), headers=headers)

        return resp

    def post_pr_comment(self, pr_number, comment_body):
        self.check_token()
        url = '{base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments'.format(
            pr_number=pr_number, **self.config)

        params = {
            'body': comment_body,
            'accept': 'application/vnd.github.v3+json',
        }

        rsp = self.post(url, params)

        return rsp

    def get_pr_comments_with_magic_tag(self):
        tagged_comments = []

        since = datetime.utcnow() - timedelta(minutes=self.pull_time_offset)
        url = '{base_url}/repos/{owner}/{repo}/issues/comments'.format(**self.config)

        params = {
            'since': since.strftime('%Y%m%dT%H%M%SZ'),
            'accept': 'application/vnd.github.v3+json',
            'per_page': 100,
            'page': 1,
            'sort': 'updated',
            'direction': 'asc'
        }

        resp = self.get(url, params)
        try:
            comments = resp.json()
        except:
            comments = []

        for comment in comments:
            comment_id = comment['id']
            if comment_id <= self.last_comment_id:
                continue
            self.last_comment_id = comment_id

            if 'pull' not in comment['html_url']:
                continue

            login = comment['user']['login']
            if not any(login == perm_login for perm_login in self.permitted_logins):
                continue

            body = comment['body']
            for tag in self.tags:
                if body.startswith(tag):
                    comment['magic_tag'] = tag
                    break

            if 'magic_tag' not in comment:
                continue

            tagged_comments.append(comment)

        return tagged_comments

    def get_scheduled_post_text(self, pr_url, time):
        # You can monkey patch this method to inject your message
        return f'Scheduled PR #{pr_url} after {time}.'

    def run(self):
        i = self.interval
        while not self.end:
            if not self.enabled or i < self.interval:
                i += 1
                sleep(1)
                continue

            i = 0

            log(f'Github puller {self.name} is running')
            tagged_comments = self.get_pr_comments_with_magic_tag()

            for comment in tagged_comments:
                if not self.check_supported_profiles(comment):
                    continue

                github_pr_number = int(re.findall(r'(?<=pull\/)\d+?(?=#)', comment['html_url'])[0])
                url = '{base_url}/repos/{owner}/{repo}/pulls/{issue_nr}'.format(**self.config,
                                                                                issue_nr=github_pr_number)

                params = {'accept': 'application/vnd.github.v3+json'}
                resp = self.get(url, params)
                try:
                    pr = resp.json()
                except:
                    continue

                tag_cfg = self.tags[comment['magic_tag']]
                pr_cfg = {
                    'number': github_pr_number,
                    'source_repo_owner': pr['user']['login'],
                    'repo_name': pr['head']['repo']['name'],
                    'source_branch': pr['head']['ref'],
                    'head_sha': pr['head']['sha'],
                    'comment_body': comment['body'],
                    'magic_tag': comment['magic_tag'],
                    'autopts_selftest': tag_cfg.autopts_selftest if hasattr(tag_cfg, 'autopts_selftest') else False
                }

                start_time = self.schedule_job_cb(self, comment['html_url'], tag_cfg, pr_cfg,
                                                  timedelta(minutes=self.schedule_delay))
                today_str = start_time.strftime('%H:%M:%S')
                post_text = self.get_scheduled_post_text(comment['html_url'], today_str)
                self.post_pr_comment(github_pr_number, post_text)
                log(post_text)

    def set_pull_time_offset(self, offset):
        self.pull_time_offset = offset
        self.last_comment_id = 0

    def check_supported_profiles(self, comment):
        body = comment['body']
        magic_tag = comment['magic_tag']
        job_config = self.tags[magic_tag]

        if not job_config.included:
            # 'included' parameter not specified in job config. Assume
            # all profiles supported on this server.
            return True

        test_case_prefixes = re.sub(r'\s+', r' ', body[len(magic_tag):]).strip().split(' ')
        job_config_prefixes = re.sub(r'\s+', r' ', job_config.included).strip().split(' ')

        for prefix in test_case_prefixes:
            for profile in job_config_prefixes:
                if prefix.startswith(profile):
                    # At least one prefix matched
                    return True

        # Not even a single test case prefix is supported on this test server.
        # Ignore the command.
        return False
