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
import copy
import logging
import os
import pathlib
import re
import subprocess
import sys
import mimetypes
import shutil
import zipfile
import smtplib
import datetime
from pathlib import Path
from argparse import Namespace
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from xmlrpc.client import ServerProxy
import git
import yaml
import xlsxwriter

from googleapiclient import discovery, errors
from googleapiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file, client, tools

from autopts import bot
from autopts import client as autoptsclient
from autopts.client import CliParser, Client
from autopts.ptsprojects.testcase_db import DATABASE_FILE

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
REPORT_XLSX = "report.xlsx"
REPORT_TXT = "report.txt"
COMMASPACE = ', '

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERRATA_DIR_PATH = os.path.join(os.path.dirname(PROJECT_DIR), 'errata')
log = logging.debug


class BotCliParser(CliParser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_argument('--nb', dest='no_build', action='store_true',
                          help='Skip build and flash in bot mode.', default=False)

    def add_positional_args(self):
        pass


class BotConfigArgs(Namespace):
    """
    Translates arguments provided in 'config.py' file as dictionary
    into a namespace used by common Client.
    """

    def __init__(self, args, **kwargs):
        super().__init__(**kwargs)
        self.workspace = args['workspace']
        self.project_path = args['project_path']
        self.srv_port = args.get('srv_port', [65000])
        self.cli_port = args.get('cli_port', [65001])
        self.ip_addr = args.get('server_ip', ['127.0.0.1'] * len(self.srv_port))
        self.local_addr = args.get('local_ip', ['127.0.0.1'] * len(self.cli_port))
        self.tty_file = args.get('tty_file', None)
        self.debugger_snr = args.get('debugger_snr', None)
        self.kernel_image = args.get('kernel_image', None)
        self.database_file = args.get('database_file', DATABASE_FILE)
        self.store = args.get('store', False)
        self.rtt_log = args.get('rtt_log', False)
        self.btmon = args.get('btmon', False)
        self.test_cases = []
        self.excluded = []

        self.bd_addr = args.get('bd_addr', '')
        self.enable_max_logs = args.get('enable_max_logs', False)
        self.retry = args.get('retry', 0)
        self.stress_test = args.get('stress_test', False)
        self.ykush = args.get('ykush', None)
        self.recovery = args.get('recovery', False)
        self.superguard = float(args.get('superguard', 0))


class BotClient(Client):
    def __init__(self, get_iut, project, name, bot_config_class=BotConfigArgs,
                 parser_class=BotCliParser):
        # Please extend this bot client
        super().__init__(get_iut, project, name, parser_class)
        self.parse_config = bot_config_class
        self.config_default = "default.conf"
        self.iut_config = None

    def apply_config(self, args, config, value):
        pass

    def run_test_cases(self):
        results = {}
        status = {}
        descriptions = {}
        total_regressions = []
        total_progresses = []
        _args = {}

        config_default = self.config_default
        _args[config_default] = self.args

        excluded = _args[config_default].excluded
        included = _args[config_default].test_cases

        for config, value in list(self.iut_config.items()):
            if 'test_cases' not in value:
                # Rename default config
                _args[config] = _args.pop(config_default)
                config_default = config
                continue

            if config != config_default:
                _args[config] = copy.deepcopy(_args[config_default])
                _args[config].excluded = excluded

            _args[config].test_cases = autoptsclient.get_test_cases(
                self.ptses[0], value.get('test_cases', []), included, excluded)

            if 'overlay' in value:
                if len(_args[config].test_cases) > 0:
                    _args[config_default].excluded += _args[config].test_cases
                else:
                    _args.pop(config)
                    log('No test cases for {} config, ignored.'.format(config))
        _args[config_default].test_cases = autoptsclient.get_test_cases(
            self.ptses[0], self.ptses[0].get_project_list(), _args[config_default].test_cases, excluded)
        if len(_args[config_default].test_cases) == 0:
            _args.pop(config_default)
            log('No test cases for {} config, ignored.'.format(config_default))

        for config in _args.keys():
            if config not in self.iut_config.keys():
                continue

            self.apply_config(_args[config], config, self.iut_config[config])

            status_count, results_dict, regressions, progresses = \
                autoptsclient.run_test_cases(self.ptses, self.test_cases, _args[config])

            total_regressions += regressions
            total_progresses += progresses

            for k, v in list(status_count.items()):
                if k in list(status.keys()):
                    status[k] += v
                else:
                    status[k] = v

            results.update(results_dict)

            for test_case_name in list(results.keys()):
                project_name = test_case_name.split('/')[0]
                descriptions[test_case_name] = \
                    self.ptses[0].get_test_case_description(project_name, test_case_name)

        pts_ver = '{}'.format(self.ptses[0].get_version())
        platform = '{}'.format(self.ptses[0].get_system_model())

        return status, results, descriptions, total_regressions, total_progresses, pts_ver, platform

    def run_tests(self, args, iut_config):
        """Run test cases
            :param args: AutoPTS arguments
            :param iut_config: IUT configuration
            :return: tuple of (status, results) dictionaries
            """

        self.iut_config = iut_config

        return self.start(self.parse_config(args))


# ****************************************************************************
# Mail
# ****************************************************************************


def status_dict2summary_html(status_dict):
    """Creates HTML formatted summary from status dictionary
    :param status_dict: status dictionary, where key is status and value is
    status count
    :return: HTML formatted summary
    """
    summary = """<h3>Summary</h3>
                 <table>"""
    total_count = 0

    summary += """<tr>
                  <td style=\"width: 150px;\"><b>Status</b></td>
                  <td style=\"text-align: center;\"><b>Count</b></td>
                  </tr>"""

    for status in sorted(status_dict.keys()):
        count = status_dict[status]
        summary += """<tr>
                      <td style=\"width: 150px;\">{}</td>
                      <td style=\"text-align: center;\">{}</td>
                      </tr>""".format(status, count)
        total_count += count

    summary += """<tr>
                  <td style=\"width: 150px;\"><i>Total</i></td>
                  <td style=\"text-align: center;\"><i>{}</i></td>
                  </tr>""".format(total_count)
    summary += "</table>"

    if "PASS" in status_dict:
        pass_rate = \
            '{0:.2f}%'.format((status_dict["PASS"] / float(total_count) * 100))
    else:
        pass_rate = '{0:.2f}%'.format(0)
    summary += "<p><b>PassRate = {}</b></p>".format(pass_rate)

    return summary


def url2html(url, msg):
    """Creates HTML formatted URL with results
    :param url: URL
    :param msg: URL description
    :return: HTML formatted URL
    """
    return "<a href={}>{}</a>".format(url, msg)


def regressions2html(regressions, descriptions):
    """Creates HTML formatted message with regressions
    :param regressions: list of regressions found
    :param descriptions: dictionary of descriptions for regressions
    :return: HTML formatted message
    """
    msg = "<h3>Regressions</h3>"

    regressions_list = []
    for name in regressions:
        regressions_list.append(
            name + " - " + descriptions.get(name, "no description"))

    if regressions_list:
        for name in regressions_list:
            msg += "<p>{}</p>".format(name)
    else:
        msg += "<p>No regressions found</p>"

    return msg


def progresses2html(progresses, descriptions):
    """Creates HTML formatted message with regressions
    :param progresses: list of regressions found
    :return: HTML formatted message
    """
    msg = "<h3>Progresses</h3>"

    progresses_list = []
    for name in progresses:
        progresses_list.append(
            name + " - " + descriptions.get(name, "no description"))

    if progresses_list:
        for name in progresses_list:
            msg += "<p>{}</p>".format(name)
    else:
        msg += "<p>No progresses found</p>"

    return msg


def send_mail(cfg, subject, body, attachments=None):
    """
    :param cfg: Mailbox configuration
    :param subject: Mail subject
    :param body: Mail body
    :param attachments: Email attachments
    :return: None
    """

    msg = MIMEMultipart()
    msg['From'] = cfg['sender']
    msg['To'] = COMMASPACE.join(cfg['recipients'])
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'html'))

    # Attach the files if there is any
    if attachments:
        for filename in attachments:
            file_type = mimetypes.guess_type(filename)
            if file_type[0] is None:
                ext = os.path.splitext(filename)[1]
                print('MIME Error: File extension %s is unknown. '
                      'Try to associate it with app.' % ext)
                continue
            mimetype = file_type[0].split('/', 1)
            attachment = MIMEBase(mimetype[0], mimetype[1])
            attachment.set_payload(open(filename, 'rb').read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', 'attachment',
                                  filename=os.path.basename(filename))
            msg.attach(attachment)

    server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'])
    if 'start_tls' in cfg and cfg['start_tls']:
        server.starttls()
    if 'passwd' in cfg:
        server.login(cfg['sender'], cfg['passwd'])
    server.sendmail(cfg['sender'], cfg['recipients'], msg.as_string())
    server.quit()


# ****************************************************************************
# Google Drive
# ****************************************************************************
class GDrive:
    def __init__(self, cfg):
        self.basedir_id = cfg['root_directory_id']
        self.cwd_id = self.basedir_id
        credentials = cfg['credentials_file']

        store = file.Storage(credentials)
        creds = store.get()
        if not creds or creds.invalid:
            path_abs = os.path.abspath(credentials)
            path = os.path.dirname(path_abs)

            flow = client.flow_from_clientsecrets(
                os.path.join(path, CLIENT_SECRET_FILE), SCOPES)
            creds = tools.run_flow(flow, store)
        self.service = discovery.build('drive', 'v3',
                                       http=creds.authorize(Http()))

    def pwd(self):
        return self.cwd_id

    def mkdir(self, name):
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [self.pwd()]
        }

        try:
            f = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink').execute()
        except errors.HttpError:
            sys.exit(1)

        return f

    def ls(self):
        results = {}

        page_token = None
        while True:
            try:
                response = self.service.files().list(
                    q="'{}' in parents".format(self.pwd()),
                    spaces='drive',
                    fields='nextPageToken, files(id, name)',
                    pageToken=page_token).execute()
            except errors.HttpError:
                sys.exit(1)

            for f in response.get('files', []):
                results[f.get('name')] = f
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return results

    def cp(self, name):
        if not os.path.exists(name):
            print("File not found")
            sys.exit(1)

        basename = os.path.basename(name)
        mime_type, encoding = mimetypes.guess_type(basename)

        file_metadata = {
            'name': basename,
            'parents': [self.pwd()]
        }

        media = MediaFileUpload(
            name,
            mimetype=mime_type)

        try:
            f = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name').execute()
        except errors.HttpError as err:
            print(err)
            sys.exit(1)

        return f

    def cd(self, dir_=None):
        """
            :param dir_: file object or id of the folder
        """
        if not dir_:
            self.cwd_id = self.basedir_id
        elif isinstance(dir_, str):
            self.cwd_id = dir_
        else:
            self.cwd_id = dir_.get('id')


class Drive(GDrive):
    def __init__(self, cfg):
        GDrive.__init__(self, cfg)
        self.url = None

    def new_workdir(self, iut):
        files = self.ls()
        if iut in list(files.keys()):
            dir_ = files[iut]
        else:
            dir_ = self.mkdir(iut)
        self.cd(dir_)
        dir_ = self.mkdir(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M"))
        self.cd(dir_)
        return "{}".format(dir_.get('webViewLink'))

    def upload(self, f):
        print("Uploading {} ...".format(f))
        self.cp(f)
        print("Done")

    def upload_folder(self, folder, excluded=None):
        def recursive(directory):
            for f in os.scandir(directory):
                if excluded and (f.name in excluded or
                                 os.path.splitext(f.name)[1] in excluded):
                    continue

                if f.is_dir():
                    parent = self.pwd()
                    dir_ = self.mkdir(f.name)
                    self.cd(dir_)
                    recursive(os.path.join(directory, f.name))
                    self.cd(parent)
                else:
                    filepath = os.path.relpath(os.path.join(directory, f.name))
                    self.upload(filepath)

        recursive(folder)


def get_errata(project_name):
    errata_common = os.path.join(ERRATA_DIR_PATH, 'common.yaml')
    errata_project = os.path.join(ERRATA_DIR_PATH, f'{project_name}.yaml')
    errata = {}

    for file in [errata_common, errata_project]:
        if os.path.exists(file):
            with open(file, 'r') as stream:
                loaded_errata = yaml.safe_load(stream)
                if loaded_errata:
                    errata.update(loaded_errata)
    return errata


# ****************************************************************************
# .xlsx spreadsheet file
# ****************************************************************************
# FIXME don't use statuses from status_dict, count it from results dict instead
def make_report_xlsx(results_dict, status_dict, regressions_list,
                     progresses_list, descriptions, xmls, project_name=''):
    """Creates excel file containing test cases results and summary pie chart
    :param results_dict: dictionary with test cases results
    :param status_dict: status dictionary, where key is status and value is
    status count
    :param regressions_list: list of regressions found
    :param progresses_list: list of regressions found
    :param descriptions: test cases
    :return:
    """

    try:
        xml_list = list(os.scandir(xmls))
    except FileNotFoundError as e:
        print("No XMLs found")
        xml_list = None
    matched_xml = ''

    def find_xml_by_case(case):
        if xml_list is None:
            return
        nonlocal matched_xml
        matched_xml = ''
        to_match = case.replace('/', '_').replace('-', '_')
        for xml in xml_list:
            if to_match in xml.name:
                matched_xml = xml.name
                break

    errata = get_errata(project_name)

    header = "AutoPTS Report: " \
             "{}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    workbook = xlsxwriter.Workbook(REPORT_XLSX)
    worksheet = workbook.add_worksheet()
    chart = workbook.add_chart({'type': 'pie',
                                'subtype': 'percent_stacked'})

    # Add a bold format to use to highlight cells.
    bold = workbook.add_format({'bold': True})

    # Write data headers.
    worksheet.write('A1', header)
    worksheet.write_row('A3', ['Test Case', 'Result', 'XML'])

    row = 3
    col = 0

    for k, v in list(results_dict.items()):
        worksheet.write(row, col, k)
        if v[0] == 'PASS':
            find_xml_by_case(k)
            worksheet.write(row, col + 2, matched_xml)
        if v[0] == 'PASS' and int(v[1]) > 1:
            v = '{} ({})'.format(v[0], v[1])
        else:
            v = v[0]
        if k in errata:
            v += ' - ERRATA ' + errata[k]
        worksheet.write(row, col + 1, v)
        if k in list(descriptions.keys()):
            worksheet.write(row, col + 3, descriptions[k])
        if k in regressions_list:
            worksheet.write(row, col + 4, "REGRESSION")
        if k in progresses_list:
            worksheet.write(row, col + 4, "PROGRESS")
        row += 1

    summary_row = 2
    summary_col = 5

    worksheet.write(summary_row, summary_col, 'Summary')
    end_row = summary_row
    for status in sorted(status_dict.keys()):
        count = status_dict[status]
        end_row += 1
        worksheet.write_row(end_row, summary_col, [status, count])

    # Total TCS
    row = end_row + 2
    col = summary_col
    total_count = len(results_dict)
    worksheet.write(row, col, "Total")
    worksheet.write(row, col + 1, "{}".format(total_count))
    worksheet.write(row + 1, col, "PassRate", bold)
    if "PASS" in status_dict:
        pass_rate = \
            '{0:.2f}%'.format((status_dict["PASS"] / float(total_count) * 100))
    else:
        pass_rate = '{0:.2f}%'.format(0)
    worksheet.write(row + 1, col + 1, pass_rate, bold)

    chart.set_title({'name': 'AutoPTS test results'})
    chart.add_series({
        'categories': ['Sheet1', summary_row + 1, summary_col,
                       end_row, summary_col],
        'values': ['Sheet1', summary_row + 1, summary_col + 1,
                   end_row, summary_col + 1],
    })

    worksheet.insert_chart('H2', chart)
    workbook.close()

    return os.path.join(os.getcwd(), REPORT_XLSX)


# ****************************************************************************
# .txt result file
# ****************************************************************************
def make_report_txt(results_dict, regressions_list,
                    progresses_list, repo_status, project_name=''):
    """Creates txt file containing test cases results
    :param results_dict: dictionary with test cases results
    :param regressions_list: list of regressions found
    :param progresses_list: list of regressions found
    :param repo_status: information about current commit from all
    configured repositories
    :return: txt file path
    """

    filename = os.path.join(os.getcwd(), REPORT_TXT)
    f = open(filename, "w")

    errata = get_errata(project_name)

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

        # The first id in the test case is test group
        tg = tc.split('/')[0]
        f.write("%s%s%s\n" % (tg.ljust(8, ' '), tc.ljust(32, ' '), result))

    f.close()

    return filename


# ****************************************************************************
# .txt result file
# ****************************************************************************
def make_report_folder(iut_logs, pts_logs, xmls, report_xlsx, report_txt,
                       readme_file, database_file, tag=''):
    """Creates folder containing .txt and .xlsx reports, pulled logs
    from autoptsserver, iut logs and additional README.md.
    """

    def get_deepest_dirs(logs_tree, dst_tree, max_depth):
        def recursive(directory, depth=3):
            depth -= 1

            for file in os.scandir(directory):
                if file.is_dir():
                    if depth > 0:
                        recursive(file.path, depth)
                    else:
                        dst_file = os.path.join(dst_tree, file.name)
                        try:
                            shutil.move(file.path, dst_file)
                        except:  # skip waiting for BPV to release the file
                            shutil.copy(file.path, dst_file)

        recursive(logs_tree, max_depth)

    report_dir = 'tmp/autopts_report'
    shutil.rmtree(report_dir, ignore_errors=True)
    Path(report_dir).mkdir(parents=True, exist_ok=True)

    shutil.copy(report_txt, os.path.join(report_dir, 'report{}.txt'.format(tag)))
    shutil.copy(report_xlsx, os.path.join(report_dir, 'report{}.xlsx'.format(tag)))
    shutil.copy(readme_file, os.path.join(report_dir, 'README.md'))
    shutil.copy(database_file, os.path.join(report_dir, os.path.basename(database_file)))

    iut_logs_new = os.path.join(report_dir, 'iut_logs')
    pts_logs_new = os.path.join(report_dir, 'pts_logs')
    xmls_new = os.path.join(report_dir, 'XMLs/')

    get_deepest_dirs(iut_logs, iut_logs_new, 3)
    get_deepest_dirs(pts_logs, pts_logs_new, 3)
    try:
        shutil.move(xmls, xmls_new)
    except FileNotFoundError:
        print('XMLs directory doesn\'t exist')

    return os.path.join(os.getcwd(), report_dir)


def github_push_report(report_folder, log_git_conf, commit_msg):
    """Commits and pushes report folder to Github repo
    param: report_folder path to the report folder
    param: log_git_conf git settings from githubdrive field of config.py
    param: commit_msg ready commit message
    """
    update_sources(log_git_conf['path'], log_git_conf['remote'],
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


# ****************************************************************************
# Miscellaneous
# ****************************************************************************


def check_call(cmd, env=None, cwd=None, shell=True):
    """Run command with arguments.  Wait for command to complete.
    :param cmd: command to run
    :param env: environment variables for the new process
    :param cwd: sets current directory before execution
    :param shell: if true, the command will be executed through the shell
    :return: returncode
    """
    executable = '/bin/bash'
    cmd = subprocess.list2cmdline(cmd)

    if sys.platform == 'win32':
        executable = None

    return subprocess.check_call(cmd, env=env, cwd=cwd, shell=shell, executable=executable)


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


def pull_server_logs(args):
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

    logs_folder = 'tmp/' + workspace_name
    xml_folder = 'tmp/XMLs'
    shutil.rmtree(logs_folder, ignore_errors=True)
    shutil.rmtree(xml_folder, ignore_errors=True)
    Path(xml_folder).mkdir(parents=True, exist_ok=True)

    server_addr = args.ip_addr
    server_port = args.srv_port

    for i in range(len(server_addr)):
        if i != 0 and server_addr[i] in server_addr[0:i]:
            continue
        last_xml = ('', '')

        with ServerProxy("http://{}:{}/".format(server_addr[i], server_port[i]),
                         allow_none=True, ) as proxy:
            file_list = proxy.list_workspace_tree(workspace_dir)
            if len(file_list) == 0:
                continue

            workspace_root = file_list.pop()
            while len(file_list) > 0:
                file_path = file_list.pop(0)
                xml_file_path = file_path
                try:
                    file_bin = proxy.copy_file(file_path)

                    if not any(file_path.endswith(ext) for ext in ['.pts', '.pqw6', '.xlsx', '.gitignore']):
                        proxy.delete_file(file_path)

                    if file_bin is None:
                        continue

                    file_path = '/'.join([logs_folder,
                                          file_path[len(workspace_root) + 1:]
                                         .replace('\\', '/')])
                    Path(os.path.dirname(file_path)).mkdir(parents=True,
                                                           exist_ok=True)

                    with open(file_path, 'wb') as handle:
                        handle.write(file_bin.data)

                    if file_path.endswith('.xml') and not 'tc_log' in file_path \
                            and b'Final Verdict:PASS' in file_bin.data:
                        (test_name, timestamp) = split_xml_filename(file_path)
                        if test_name in last_xml[0]:
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

    return logs_folder, xml_folder


def get_workspace(workspace):
    for root, dirs, files in os.walk(os.path.join(PROJECT_DIR, 'workspaces'),
                                     topdown=True):
        for name in dirs:
            if name == workspace:
                return os.path.join(root, name)
    return None


def get_autopts_version():
    repo = git.Repo(os.path.dirname(PROJECT_DIR))
    version = repo.git.show('-s', '--format=%H')

    if repo.is_dirty():
        version += '-dirty'

    return version


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
    repo.git.checkout('{}/{}'.format(remote, branch))

    return describe_repo(repo_path)


def make_repo_status(repos_info):
    status_list = []

    for name, info in list(repos_info.items()):
        status_list.append('{}={}'.format(name, info['commit']))

    return ', '.join(status_list)


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

        project_path.join(repo_path)

        if conf.get('update_repo', False):
            desc, commit = update_sources(repo_path, conf["remote"],
                                          conf["branch"], conf["stash_changes"])
        else:
            desc, commit = describe_repo(repo_path)

        repo_dict["commit"] = commit
        repo_dict["desc"] = desc
        repos_dict[repo] = repo_dict

        if conf.get('west_update', False):
            bot.common.check_call(['west', 'update'], cwd=repo_path)

        if conf.get('rm_pycache', False):
            for p in pathlib.Path(repo_path).rglob('*.py[co]'):
                p.unlink()
            for p in pathlib.Path(repo_path).rglob('__pycache__'):
                p.rmdir()

    return repos_dict


def get_tty_path(name):
    """Returns tty path (eg. /dev/ttyUSB0) of serial device with specified name
    :param name: device name
    :return: tty path if device found, otherwise None
    """
    serial_devices = {}
    ls = subprocess.Popen(["ls", "-l", "/dev/serial/by-id"],
                          stdout=subprocess.PIPE)

    awk = subprocess.Popen("awk '{if (NF > 5) print $(NF-2), $NF}'",
                           stdin=ls.stdout,
                           stdout=subprocess.PIPE,
                           shell=True)

    end_of_pipe = awk.stdout
    for line in end_of_pipe:
        device, serial = line.decode().rstrip().split(" ")
        serial_devices[device] = serial

    for device, serial in list(serial_devices.items()):
        if name in device:
            tty = os.path.basename(serial)
            return "/dev/{}".format(tty)

    return None


def pre_cleanup():
    """Perform cleanup before test run
    :return: None
    """
    try:
        shutil.copytree("logs", "oldlogs", dirs_exist_ok=True)
        shutil.rmtree("logs")
    except OSError:
        pass


def cleanup():
    """Perform cleanup
    :return: None
    """
    try:
        pass
    except OSError:
        pass
