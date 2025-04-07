#!/usr/bin/env python3

#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2024, BlueKitchen GmbH.
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

"""Script to sort protocols and profiles in PTS workspace

Usage:
$ python3 sort_workspace_projects path\to\pts\workspace\workspace.pqw6

It generates a new workspace_sorted.pqw6 file.
"""

import sys
import xml.etree.ElementTree as ET


def sort_projects_by_name(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    projects_info = root.find('PROJECTS_INFORMATION')
    
    sorted_projects = sorted(projects_info.findall('PROJECT_INFORMATION'), key=lambda x: x.get('NAME'))
    
    for project_info in projects_info.findall('PROJECT_INFORMATION'):
        projects_info.remove(project_info)
    
    for sorted_project in sorted_projects:
        projects_info.append(sorted_project)
    
    sorted_xml_file = xml_file.replace('.pqw6', '_sorted.pqw6')
    tree.write(sorted_xml_file)

    print(f"Sorted PTS Workspace written to: {sorted_xml_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Sort Projects (protocols/profiles) in PTS Workspace by name")
        print("Usage: ./%s <path_to_pts_workspace>/<workspace>.pqw6" % sys.argv[0])
        sys.exit(1)
    
    xml_file_path = sys.argv[1]
    sort_projects_by_name(xml_file_path)
