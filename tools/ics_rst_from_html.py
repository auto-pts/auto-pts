#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Codecoup.
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

"""ICS Launch Studio html to rst file parser

Log into your bluetooth.com account. Go to
https://launchstudio.bluetooth.com/MyProjects/DraftProjects/
and select your project. Go to ICS Selection tab and select profile, e.g. GAP.
Save the page of the profile as html file.

Run this script as follows:

cd auto-pts
python3 ics_rst_from_html.py GAP path/to/Launch-Studio-ICS-Selection.html

In directory of run will be created gap-pics.rst file.
"""

import sys
import os
import re
import pandas as pd


def make_table(table, profile):
    grid = [['Parameter Name', 'Selected', 'Description']]

    for i in range(len(table.values)):
        new_row = []
        parameter_name = 'TSPC_{}_{}'.format(profile, table.Item[i].replace('/', '_'))
        selected = 'True' if table.Support[i] else 'False'
        description = '{} ({})'.format(table.Capability[i], table.Status[i])

        new_row.append(parameter_name)
        new_row.append(selected)
        new_row.append(description)
        grid.append(new_row)

    # Get widths of table cells, put them into matrix
    width_matrix = []
    for row in grid:
        column_widths_in_row = [len(str(item)) for item in row]
        width_matrix.append(column_widths_in_row)

    # matrix transposition, columns became rows
    width_matrix = map(list, zip(*width_matrix))

    max_width_per_column = [max(column_width) for column_width in width_matrix]

    rst = table_div(max_width_per_column, 1)
    rst += normalize_row(grid[0], max_width_per_column)

    rst += table_div(max_width_per_column, 1)
    for row in grid[1:]:
        rst += normalize_row(row, max_width_per_column)
    rst += table_div(max_width_per_column, 1)
    return rst


def table_div(max_width_per_column, header_flag=1):
    out = ""
    if header_flag == 1:
        style = "="
    else:
        style = "-"

    for col_width in max_width_per_column:
        out += col_width * style + " "

    out = out.strip() + "\n"
    return out


def normalize_row(row, max_width_per_column):
    r = ""
    for i, max_col in enumerate(max_width_per_column):
        r += row[i] + (max_col - len(row[i]) + 1) * " "

    return r.strip() + "\n"


if __name__ == '__main__':

    if len(sys.argv) < 3:
        sys.exit('Please pass profile name and html file path as arguments, e.g.:\n'
                 '$ python3 {} GAP path/to/Launch-Studio-ICS-Selection.html\n'
                 'html file - save https://launchstudio.bluetooth.com/ICS/<some id> '
                 'page as html file'.format(sys.argv[0]))

    profile_name = sys.argv[1]
    path = sys.argv[2]

    if not os.path.isfile(path):
        sys.exit(path + ' is not a file!')

    with open(path, 'r') as f:
        content = f.read()

    tcrl_ver = re.findall(r'(?<="TCRLVersionName":").+?(?=")', content)[0]

    # Pandas does not parse checkboxes, but in generated from Launch Studio html it looks like checked="checked"
    # occurs only when checkbox is really checked
    content = re.sub(r'<input[^>]+?checkbox[^>]+?checked.+?>', 'True', content)
    content = re.sub(r'<input[^>]+?checked[^>]+?checkbox.+?>', 'True', content)

    # The rest should be unchecked:
    content = re.sub(r'<input[^>]+?checkbox.+?>', 'False', content)

    # Fix what broke above
    content = re.sub(r'(False|True) Support', 'Support', content)

    table_titles = re.findall(r'(?=<h4>\s*Table\s*.+:\s*).+?(?=</h4>)', content)
    for i in range(len(table_titles)):
        table_titles[i] = table_titles[i].split(r':')[1].strip()

    # Returns list of all tables on page
    tables = pd.read_html(content)

    head_title = profile_name + ' ICS'

    rst_content = '''.. _{}-pics:

{}
{}

TCRL version: {}

M - mandatory

O - optional


'''.format(profile_name.lower(), head_title, len(head_title) * '*', tcrl_ver)

    for table, table_title in zip(tables, table_titles):
        rst_content += table_title + '\n'
        rst_content += len(table_title) * '=' + '\n\n'
        rst_content += make_table(table, profile_name) + '\n'

    rst_content = rst_content.strip() + '\n'

    with open(profile_name.lower() + '-pics.rst', 'w') as f:
        f.write(rst_content)
