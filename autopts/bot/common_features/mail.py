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
import mimetypes
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import autopts.bot.common as common

COMMASPACE = ', '


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
        summary += f"""<tr>
                      <td style=\"width: 150px;\">{status}</td>
                      <td style=\"text-align: center;\">{count}</td>
                      </tr>"""
        total_count += count

    summary += f"""<tr>
                  <td style=\"width: 150px;\"><i>Total</i></td>
                  <td style=\"text-align: center;\"><i>{total_count}</i></td>
                  </tr>"""
    summary += "</table>"

    if "PASS" in status_dict:
        pass_rate = status_dict["PASS"] / float(total_count) * 100
    else:
        pass_rate = 0

    if pass_rate < 75:
        rate_color = 'red'
    elif pass_rate < 100:
        rate_color = 'black'
    else:
        rate_color = 'green'

    summary += f'<p style="color:{rate_color};"><b>PassRate = {pass_rate:.2f}%</b></p>'

    return summary


def html_profile_summary(tc_results):
    """Creates HTML formatted table with summarized profile results"""
    test_groups = {}
    common.get_tc_res_data(tc_results, test_groups)

    for tg in test_groups.values():
        tg.get_pass_rate()

    table_rows = ""
    for suite, stats in test_groups.items():
        table_rows += f"""
            <tr>
                <td>{suite}</td>
                <td>{stats.total}</td>
                <td>{stats.passed}</td>
                <td>{stats.failed}</td>
                <td>{stats.pass_rate:.2f} %</td>
            </tr>
            """

    suite_summary = f"""
        <div>
            <h3>Test Group/Profile Summary</h3>
            <table border="1" style="border-collapse: collapse; text-align: center; width: 35em">
                <thead>
                    <tr>
                        <th style="width: 20%">Suite</th>
                        <th style="width: 20%">Total</th>
                        <th style="width: 20%">Pass</th>
                        <th style="width: 20%">Fail</th>
                        <th style="width: 20%">Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
    return suite_summary


def url2html(url, msg):
    """Creates HTML formatted URL with results
    :param url: URL
    :param msg: URL description
    :return: HTML formatted URL
    """
    return f"<a href={url}>{msg}</a>"


def test_cases2html(title, not_found_msg, test_cases, descriptions):
    """Creates HTML formatted message with test cases
    :param title: Title of email subsection
    :param not_found_msg: Text to use if no test cases
    :param test_cases: A list of test cases
    :param descriptions: A list of test case descriptions
    :return: HTML formatted message
    """
    msg = f"<h3>{title}</h3>"

    progresses_list = [
        name + " - " + descriptions.get(name, "no description")
        for name in test_cases
    ]

    if progresses_list:
        for name in progresses_list:
            msg += f"<p>{name}</p>"
    else:
        msg += f"<p>{not_found_msg}</p>"

    return msg


def regressions2html(regressions, descriptions):
    return test_cases2html('Regressions', 'No regressions found',
                           regressions, descriptions)


def progresses2html(progresses, descriptions):
    return test_cases2html('Progresses', 'No progresses found',
                           progresses, descriptions)


def new_cases2html(new_cases, descriptions):
    return test_cases2html('New cases', 'No new cases found',
                           new_cases, descriptions)


def deleted_cases2html(deleted_cases, descriptions):
    return test_cases2html('Deleted cases', 'No deleted cases found',
                           deleted_cases, descriptions)


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
                print(f'MIME Error: File extension {ext} is unknown. Try to associate it with app.')
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
