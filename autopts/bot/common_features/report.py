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

import logging
import os
import re
import datetime
import zipfile
import shutil
from pathlib import Path
from xmlrpc.client import ServerProxy

import git
import yaml
import xlsxwriter

from autopts.bot.common_features import github
from autopts.bot import common
from autopts.client import PtsServer
from autopts.config import AUTOPTS_ROOT_DIR
from typing import Tuple, List, Optional

log = logging.debug


def get_errata(errata_files):
    errata = {}

    for file in errata_files:
        if os.path.exists(file):
            with open(file, 'r') as stream:
                loaded_errata = yaml.safe_load(stream)
                if loaded_errata:
                    errata.update(loaded_errata)
    return errata


def get_autopts_version():
    repo = git.Repo(AUTOPTS_ROOT_DIR)
    version = repo.git.show('-s', '--format=%H')

    if repo.is_dirty():
        version += '-dirty'

    return version


def make_repo_status(repos_info):
    status_list = []

    for name, info in list(repos_info.items()):
        status_list.append('{}={}'.format(name, info['commit']))

    return ', '.join(status_list)


# ****************************************************************************
# .xlsx spreadsheet file
# ****************************************************************************
def parse_result_column(full_result: str) -> Tuple[str, str]:
    """
    Helper function: Searches for fixed keywords in `full_result`.
    If found, returns (keyword, rest_text).
    If it doesn't find it, it returns (full_result, "").
    """
    # The order matters - if there is a possibility
    # of several matches, the first one in the list decides.
    patterns = [
        "PASS",
        "UNKNOWN VERDICT",
        "FAIL",
        "PTS TIMEOUT",
        "RUNNING",
        "BTP ERROR",
        "INDCSV",
        "BTP",
        "MiSSING WID ERROR",
        "ERROR"
    ]
    for pattern in patterns:
        if pattern in full_result:
            additional_text = full_result.replace(pattern, "", 1).strip()
            return pattern, additional_text
    return full_result, ""


def find_matching_xml_filename(test_case: str, xml_list: Optional[List[os.DirEntry]]) -> Optional[str]:
    """
    Finds first XML filename in `xml_list` matching the test_case string.
    Matching is based on replacing '/' and '-' with '_' in test_case.
    Returns the matched filename or None if not found or xml_list is None.
    """
    if xml_list is None:
        return None

    to_match = test_case.replace('/', '_').replace('-', '_')
    for entry in xml_list:
        if to_match in entry.name:
            return entry.name
    return None


def make_report_xlsx(report_xlsx_path: str,
                     results_dict: dict,
                     status_dict: dict,
                     regressions_list: list,
                     progresses_list: list,
                     descriptions: dict,
                     xmls: str,
                     errata: dict):
    """
    Creates xlsx file containing test cases results and summary pie chart.

    :param report_xlsx_path: Path where to create the report XLSX file
    :param results_dict: dictionary with test cases results
    :param status_dict: status dictionary, where key is status and value is
                        status count
    :param regressions_list: list of regressions found
    :param progresses_list: list of progresses found
    :param descriptions: dictionary with test cases descriptions
    :param xmls: directory where XML files are located
    :param errata: dictionary with errata notes for specific test cases
    :return: None
    """

    try:
        xml_list = list(os.scandir(xmls))
    except FileNotFoundError:
        print("No XMLs found")
        xml_list = None

    header = "AutoPTS Report: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    workbook = xlsxwriter.Workbook(report_xlsx_path)
    worksheet = workbook.add_worksheet("Report")
    chart = workbook.add_chart({'type': 'pie', 'subtype': 'percent_stacked'})

    bold_format = workbook.add_format({'bold': True})

    worksheet.write('A1', header)
    worksheet.write_row('A3', [
        'Test Case',
        'Result',
        'Result Additional Info',
        'XML',
        'Description',
        'Start Time',
        'End Time',
        'Duration'
    ])

    current_row = 3
    start_col = 0

    for test_case, result_data in results_dict.items():
        raw_result = result_data[0]
        parsed_result, additional_info = parse_result_column(raw_result)

        if parsed_result == 'PASS' and len(result_data) > 1:
            try:
                count_val = int(result_data[1])
                if count_val > 1:
                    parsed_result = f"{parsed_result} ({count_val})"
            except ValueError:
                pass

        if test_case in errata:
            if additional_info:
                additional_info += f" - ERRATA {errata[test_case]}"
            else:
                additional_info = f"ERRATA {errata[test_case]}"

        worksheet.write(current_row, start_col, test_case)
        worksheet.write(current_row, start_col + 1, parsed_result)
        worksheet.write(current_row, start_col + 2, additional_info)

        if parsed_result.startswith('PASS'):
            matched_xml = find_matching_xml_filename(test_case, xml_list)
            worksheet.write(current_row, start_col + 3, matched_xml or "")

        description = descriptions.get(test_case, "")
        worksheet.write(current_row, start_col + 4, description)

        if len(result_data) > 2 and result_data[2] is not None:
            worksheet.write(current_row, start_col + 5, result_data[2])
        if len(result_data) > 3 and result_data[3] is not None:
            worksheet.write(current_row, start_col + 6, result_data[3])
        if len(result_data) > 4 and result_data[4] is not None:
            try:
                duration_value = float(result_data[4])
                worksheet.write(current_row, start_col + 7, round(duration_value, 2))
            except ValueError:
                worksheet.write(current_row, start_col + 7, result_data[4])

        if test_case in regressions_list:
            worksheet.write(current_row, start_col + 9, "REGRESSION")
        if test_case in progresses_list:
            worksheet.write(current_row, start_col + 9, "PROGRESS")

        current_row += 1
    summary_row = 2
    summary_col = 10

    worksheet.write(summary_row, summary_col, 'Summary')
    end_row = summary_row

    for status in sorted(status_dict.keys()):
        count = status_dict[status]
        end_row += 1
        worksheet.write_row(end_row, summary_col, [status, count])

    total_count = len(results_dict)
    worksheet.write(end_row + 2, summary_col, "Total")
    worksheet.write(end_row + 2, summary_col + 1, f"{total_count}")

    worksheet.write(end_row + 3, summary_col, "PassRate", bold_format)
    pass_count = status_dict.get("PASS", 0)
    if total_count > 0:
        pass_rate = f"{(pass_count / float(total_count)) * 100:.2f}%"
    else:
        pass_rate = "0.00%"
    worksheet.write(end_row + 3, summary_col + 1, pass_rate, bold_format)

    chart.set_title({'name': 'AutoPTS test results'})
    chart.add_series({
        'categories': ['Report', summary_row + 1, summary_col, end_row, summary_col],
        'values':     ['Report', summary_row + 1, summary_col + 1, end_row, summary_col + 1],
    })

    worksheet.insert_chart('O2', chart)
    workbook.close()


# ****************************************************************************
# .txt result file
# ****************************************************************************
def make_report_txt(report_txt_path, results_dict, regressions_list,
                    progresses_list, repo_status, errata):
    """Creates txt file containing test cases results
    :param results_dict: dictionary with test cases results
    :param regressions_list: list of regressions found
    :param progresses_list: list of regressions found
    :param repo_status: information about current commit from all
    configured repositories
    :return: txt file path
    """

    f = open(report_txt_path, "w")

    f.write(f"{repo_status}, autopts={get_autopts_version()}\n")
    for tc, result in list(results_dict.items()):
        res = result[0]
        if result[0] == 'PASS':
            if int(result[1]) > 1:
                res = '{} ({})'.format(res, result[1])
            if tc in progresses_list:
                res = '{} - PROGRESS '.format(res)
        elif tc in regressions_list:
            res = '{} - REGRESSION '.format(res)

        result = res

        if tc in errata:
            result += ' - ERRATA ' + errata[tc]

        if result[0] == 'TIMEOUT':
            result += ' - Logs may not be available'

        # The first id in the test case is a test group
        tg = tc.split('/')[0]
        f.write("%s%s%s\n" % (tg.ljust(8, ' '), tc.ljust(32, ' '), result))

    f.close()


def report_parse_test_cases(report):
    if not os.path.exists(report):
        return None

    test_cases = []

    with open(report, 'r') as f:
        while True:
            line = f.readline()

            if not line:
                break

            tc = re.sub(' +', ' ', line).split(r' ')[1]
            test_cases.append(tc)

    # Ignore the first line filled with sha of sources
    return test_cases[1:]


def make_report_diff(old_report_txt, report_diff_txt_path, results,
                     regressions, progresses, new_cases):
    f = open(report_diff_txt_path, "w")

    deleted_cases = []
    old_test_cases = []
    test_cases = list(results.keys())

    if os.path.exists(old_report_txt):
        old_test_cases = report_parse_test_cases(old_report_txt)

    for tc in old_test_cases:
        if tc not in test_cases:
            deleted_cases.append(tc)

    f.write(f"Regressions:\n")
    for tc in regressions:
        f.write(f"{tc}\n")

    f.write(f"\nProgresses:\n")
    for tc in progresses:
        f.write(f"{tc}\n")

    f.write(f"\nNew cases:\n")
    for tc in new_cases:
        f.write(f"{tc}\n")

    f.write(f"\nDeleted cases:\n")
    for tc in deleted_cases:
        f.write(f"{tc}\n")

    f.close()

    return deleted_cases


def make_error_txt(msg, error_txt_path):
    with open(error_txt_path, "w") as f:
        f.write(msg)


def github_push_report(report_folder, log_git_conf, commit_msg):
    """Commits and pushes report folder to Github repo
    param: report_folder path to the report folder
    param: log_git_conf git settings from githubdrive field of config.py
    param: commit_msg ready commit message
    """
    github.update_sources(log_git_conf['path'], log_git_conf['remote'],
                          log_git_conf['branch'], True)

    dst_folder = os.path.join(log_git_conf['path'], log_git_conf['subdir'], os.path.basename(report_folder))

    if os.path.exists(dst_folder):
        shutil.rmtree(dst_folder)

    shutil.move(report_folder, dst_folder)

    repo = git.Repo(log_git_conf['path'])
    repo.git.add(dst_folder)
    remote = repo.remotes[log_git_conf['remote']]

    repo.index.commit(commit_msg)
    remote.push('HEAD:' + log_git_conf['branch'])

    head_sha = repo.head.object.hexsha
    remote_url = remote.config_reader.get('url')
    repo_name = re.findall(r'(?<=/).+(?=\.git)', remote_url)[0]
    repo_owner = re.findall(r'(?<=\/|:).+(?=\/.+?\.git)', remote_url)[0]

    return 'https://github.com/{}/{}/tree/{}'.format(repo_owner, repo_name, head_sha), dst_folder


def archive_recursive(dir_path):
    """Archive directory recursively
    :return: newly created zip file path
    """
    zip_file_path = os.path.join(os.path.dirname(dir_path),
                                 os.path.basename(dir_path) + '.zip')
    with zipfile.ZipFile(zip_file_path, 'w', allowZip64=True) as zf:
        for root, dirs, files in os.walk(dir_path):
            for file_or_dir in files + dirs:
                zf.write(
                    os.path.join(root, file_or_dir),
                    os.path.relpath(os.path.join(root, file_or_dir),
                                    os.path.join(dir_path, os.path.pardir)))

    return zip_file_path


def archive_testcases(dir_path, depth=3):
    def recursive(directory, depth):
        depth -= 1
        for f in os.scandir(directory):
            if f.is_dir():
                if depth > 0:
                    recursive(os.path.join(directory, f.name), depth)
                else:
                    filepath = os.path.relpath(os.path.join(directory, f.name))
                    archive_recursive(filepath)
                    shutil.rmtree(filepath)

    recursive(dir_path, depth)
    return dir_path


def split_xml_filename(file_path):
    file_name = os.path.basename(file_path)
    file_name, _ = os.path.splitext(file_name)
    test_name, timestamp = file_name.split("_C_")
    return test_name, timestamp


def copy_server_log_file(tmp_dir, pts, ports):
    try:
        autopts_dir = pts.get_path()

        tag = '_'.join(str(x) for x in ports)
        file_name = f'autoptsserver_{tag}.log'
        file_path = f'{autopts_dir}\\{file_name}'
        file_bin = pts.copy_file(file_path)

        file_path = os.path.join(tmp_dir, file_name)
        Path(tmp_dir).mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as handle:
            handle.write(file_bin.data)
    except BaseException as e:
        logging.exception(e)


def pull_server_logs(args, tmp_dir, xml_folder):
    """Copy Bluetooth Protocol Viewer logs from auto-pts servers.
    :param args: args
    """

    workspace_name = os.path.basename(args.workspace)
    pqw6_ext = '.pqw6'
    if workspace_name.endswith(pqw6_ext):
        workspace_name = workspace_name[:-len(pqw6_ext)]
        workspace_dir = os.path.dirname(args.workspace)
    else:
        workspace_dir = workspace_name

    logs_folder = os.path.join(tmp_dir, workspace_name)
    shutil.rmtree(logs_folder, ignore_errors=True)
    shutil.rmtree(xml_folder, ignore_errors=True)
    Path(xml_folder).mkdir(parents=True, exist_ok=True)

    def _pull_logs(_pts):
        last_xml = ('', '')
        file_list = _pts.list_workspace_tree(workspace_dir)

        if args.cron_optim:
            _pts.shutdown_pts_bpv()

        if len(file_list) == 0:
            return

        # Last path will be workspace directory
        workspace_root = file_list.pop()

        while len(file_list) > 0:
            file_path = file_list.pop(0)
            xml_file_path = file_path
            try:
                file_bin = _pts.copy_file(file_path)

                if not any(file_path.endswith(ext) for ext in
                           ['.pts', '.pqw6', '.xlsx', '.gitignore', '.bls']):
                    _pts.delete_file(file_path)

                if file_bin is None:
                    continue

                file_path = '/'.join([logs_folder,
                                      file_path[len(workspace_root) + 1:]
                                     .replace('\\', '/')])
                Path(os.path.dirname(file_path)).mkdir(parents=True,
                                                       exist_ok=True)

                with open(file_path, 'wb') as handle:
                    handle.write(file_bin.data)

                # Include PTS .xml logs of test cases with PASS verdict
                # into a separate "XMLs" folder. Those will have reference
                # entries in report.xlsx
                if file_path.endswith('.xml') and not 'tc_log' in file_path \
                        and b'Final Verdict:PASS' in file_bin.data:
                    (test_name, timestamp) = split_xml_filename(file_path)
                    if test_name in last_xml[0]:
                        # When single test passes multiple times
                        # (e.g. when 'stress-test' parameter is used)
                        # include only the latest one in report.
                        if timestamp <= last_xml[1]:
                            continue
                        os.remove(last_xml[0])
                    xml_file_path = \
                        '/'.join([xml_folder,
                                  xml_file_path[
                                  xml_file_path.rfind('\\') + 1:]
                                 .replace('\\', '/')])
                    Path(os.path.dirname(xml_file_path)).mkdir(
                        parents=True,
                        exist_ok=True)
                    with open(xml_file_path, 'wb') as handle:
                        handle.write(file_bin.data)
                    last_xml = (xml_file_path, timestamp)
            except BaseException as e:
                logging.exception(e)

    if args.server_args:
        # Logs available locally
        _pull_logs(PtsServer)
    else:
        # Use xmlrpc proxy to pull logs
        server_addr = args.ip_addr
        server_port = args.srv_port

        servers = {}
        for address, port in zip(server_addr, server_port):
            if address in servers:
                servers[address].append(port)
            else:
                servers[address] = [port]

        for addr in servers:
            with ServerProxy(f"http://{addr}:{servers[addr][0]}/",
                             allow_none=True) as proxy:
                _pull_logs(proxy)
                copy_server_log_file(tmp_dir, proxy, servers[addr])

    return logs_folder, xml_folder


def ascii_profile_summary(tc_results):
    """Creates ASCII formatted table with summarized profile results"""
    test_groups = {}
    common.get_tc_res_data(tc_results, test_groups)

    for tg in test_groups.values():
        tg.get_pass_rate()

    header = "|  Suite  | Total | Pass | Fail | Pass Rate|"
    separator = "|---------|-------|------|------|----------|"
    rows = []
    for suite, stats in test_groups.items():
        rows.append(
            f"\n|{suite:<9}|{stats.total:<7}|{stats.passed:<6}|{stats.failed:<6}|{stats.pass_rate:>7.2f} % |")
    table = f"\n{header}\n{separator}" + "".join(rows)

    return table
