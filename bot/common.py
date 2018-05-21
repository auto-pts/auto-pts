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

from __future__ import print_function
import os
import sys
import mimetypes
import datetime
import xlsxwriter
import sqlite3 as sql
import git
import shutil
import zipfile

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from apiclient import discovery, errors
from apiclient.http import MediaFileUpload
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
REPORT_XLSX = "report.xlsx"
COMMASPACE = ', '


# ****************************************************************************
# Mail
# ****************************************************************************
def status_dict2summary_html(status_dict):
    """Creates HTML formatted summary from status dictionary
    :param status_dict: status dictionary, where key is status and value is
    status count
    :return: HTML formatted summary
    """
    summary = ""
    total_count = 0

    summary += "<h4>2. Test results summary</h4>"
    summary += "<table>"
    summary += "<tr><th>Status</th><th>Count</th></tr>"

    for status in sorted(status_dict.keys()):
        count = status_dict[status]
        summary += "<tr><td>{}</td><td>{}</td></tr>".format(status, count)
        total_count += count
    summary += \
        "<tr><td><i>Total</i></td><td><i>{}</i></td></tr>".format(total_count)
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


def regressions2html(regressions_list=[]):
    """Creates HTML formatted message with regressions
    :param regressions_list: list of regressions found
    :return: HTML formatted message
    """
    msg = "<h4>Regressions</h4>"

    if regressions_list:
        for name in regressions_list:
            msg += "<p>{}</p>".format(name)
    else:
        msg += "<p>No regressions found</p>"

    return msg


def send_mail(cfg, autopts_sha, zephyr_sha, iut, msg_list):
    """
    :param cfg: Mailbox configuration
    :param autopts_sha: AutoPTS Git SHA
    :param zephyr_sha: Zephyr Git SHA
    :param iut: IUT
    :param msg_list: HTML formatted messages to enclose
    :return: None
    """
    msg_str = "".join(msg_list)
    body = '''
    <p>Hello,</p>
    <p>Here's summary from weekly test session</p>
    <h4>1. Setup</h4>
    <p> Zephyr  HEAD is on {} </p>
    <p> IUT used {} </p>
    {}
    <p>Sincerely,</p>
    <p> {}</p>
    '''.format(zephyr_sha, iut, msg_str, cfg['name'])

    msg = MIMEMultipart()
    msg['From'] = cfg['sender']
    msg['To'] = COMMASPACE.join(cfg['recipients'])
    msg['Subject'] = "AutoPTS test session results"

    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'])
    server.starttls()
    server.login(cfg['sender'], cfg['passwd'])
    server.sendmail(cfg['sender'], cfg['recipients'], msg.as_string())
    server.quit()


# ****************************************************************************
# Google Drive
# ****************************************************************************
class GDrive(object):
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
            file = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink').execute()
        except errors.HttpError:
            sys.exit(1)

        return file

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

            for file in response.get('files', []):
                results[file.get('name')] = file
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
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name').execute()
        except errors.HttpError as err:
            print(err)
            sys.exit(1)

        return file

    def cd(self, dir_=None):
        if not dir_:
            self.cwd_id = self.basedir_id
        else:
            self.cwd_id = dir_.get('id')


class Drive(GDrive):
    def __init__(self, cfg):
        GDrive.__init__(self, cfg)
        self.url = None

    def new_workdir(self, iut):
        files = self.ls()
        if iut in files.keys():
            dir_ = files[iut]
        else:
            dir_ = self.mkdir(iut)
        self.cd(dir_)
        dir_ = self.mkdir(datetime.datetime.now().strftime("%Y_%m_%d"))
        self.cd(dir_)
        return "{}".format(dir_.get('webViewLink'))

    def upload(self, file):
        print("Uploading {} ...".format(file))
        self.cp(file)
        print("Done")


# ****************************************************************************
# .xlsx spreadsheet file
# ****************************************************************************
# FIXME don't use statuses from status_dict, count it from results dict instead
def make_report_xlsx(results_dict, status_dict, regressions_list,
                     descriptions):
    """Creates excel file containing test cases results and summary pie chart
    :param results_dict: dictionary with test cases results
    :param status_dict: status dictionary, where key is status and value is
    status count
    :param regressions_list: list of regressions found
    :return:
    """
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
    worksheet.write_row('A3', ['Test Case', 'Result'])

    row = 3
    col = 0

    for k, v in results_dict.items():
        worksheet.write(row, col, k)
        worksheet.write(row, col + 1, v)
        if k in descriptions.keys():
            worksheet.write(row, col + 2, descriptions[k])
        if k in regressions_list:
            worksheet.write(row, col + 3, "REGRESSION")
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
# sqlite database
# ****************************************************************************
def db_test_case_lookup_result(project, board, name):
    table_name = "{}_{}".format(project, board)

    with sql.connect('results.db') as con:
        cur = con.cursor()

        try:
            cur.execute("SELECT Result FROM {} WHERE Name=:Name"
                        .format(table_name), {"Name": name})
            con.commit()
            row = cur.fetchone()
            if row:
                return row[0]
        except sql.OperationalError:  # no such table
            pass

    return None


def db_test_case_store_results(project, board, results):
    table_name = "{}_{}".format(project, board)

    if not results:
        return

    with sql.connect('results.db') as con:
        cur = con.cursor()

        cur.execute("DROP TABLE IF EXISTS {};".format(table_name))
        cur.execute("CREATE TABLE {}(Name TEXT, Result TEXT);"
                    .format(table_name))
        for name, result in results.items():
            cur.execute("INSERT INTO {} VALUES(?, ?);".format(table_name),
                        (name, result))


def lookup_regressions(board, results):
    """Lookup for regressions compared to previous run
    :param board: board name
    :param results: current results
    :return: regressions list
    """
    regressions = []

    for name, result in results.items():
        old_result = db_test_case_lookup_result('zephyr', board, name)
        if result != old_result and old_result == "PASS":
            regressions.append(name)

    return regressions


# ****************************************************************************
# Miscellaneous
# ****************************************************************************
def archive_recursive(dir_path):
    """Archive directory recursively
    :return: newly created zip file path
    """
    zip_file_path = os.path.join(os.path.dirname(dir_path),
                                 os.path.basename(dir_path)+'.zip')
    with zipfile.ZipFile(zip_file_path, 'w') as zf:
        for root, dirs, files in os.walk(dir_path):
            for file_or_dir in files + dirs:
                zf.write(
                    os.path.join(root, file_or_dir),
                os.path.relpath(os.path.join(root, file_or_dir),
                                os.path.join(dir_path, os.path.pardir)))

    return zip_file_path


def update_sources(repo, remote):
    """GIT Update sources
    :param repo: project git repository path
    :param remote: remote name
    :return:
    """
    repo = git.Repo(repo)
    repo.git.fetch(remote)
    repo.git.checkout('master')
    repo.git.reset('--hard', '{}/master'.format(remote))
    repo.git.clean('-fd')

    return repo.git.show('-s', '--format=%H')


def cleanup():
    """Perform cleanup
    :return: None
    """
    try:
        shutil.rmtree("logs")
    except OSError:
        pass
