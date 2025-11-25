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

from datetime import datetime
from os.path import abspath, dirname

AUTOPTS_REPO = dirname(dirname(abspath(__file__)))
print(AUTOPTS_REPO)


def append_lines(file_path, change_id, new_lines):
    with open(file_path) as file:
        lines = file.readlines()

    # Find the index of the line with the "#GENERATOR" tag
    generator_index = None
    for i, line in enumerate(lines):
        if f"# GENERATOR append {change_id}" in line:
            generator_index = i
            break

    if generator_index is not None:
        # Insert the new line before the line with the "# GENERATOR" tag
        lines.insert(generator_index, new_lines)

        # Write the modified content back to the file
        with open(file_path, 'w', newline='') as file:
            file.writelines(lines)

    else:
        print(f"#GENERATOR tag not found in the {file} file.")


def create_file(path, content):
    with open(path, "w+", newline='') as file:
        file.write(content)


project_name = input('Enter project name (e.g. zephyr): ').strip() or 'zephyr'
project_path = f'{AUTOPTS_REPO}/autopts/ptsprojects/{project_name}'
profile_name = input('Enter profile name: ').strip() or 'profile'
profile_id = input('Enter new BTP service ID: ').strip() or 0xff
code_owner = input('Enter code owner name (e.g. Codecoup): ').strip() or 'Codecoup'
profile_name_lower = profile_name.lower()
profile_name_upper = profile_name.upper()


copyright_text = f'Copyright (c) {datetime.now().year}, {code_owner}.'
license_text = f"""#
# auto-pts - The Bluetooth PTS Automation Framework
#
# {copyright_text}
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

files_to_create = {
    # START of autopts/ptsprojects/zephyr/profile.py
    f'{project_path}/{profile_name_lower}.py':
f"""{license_text}
from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc
from autopts.ptsprojects.{project_name}.ztestcase import ZTestCase
from autopts.pybtp import btp
from autopts.ptsprojects.{project_name}.{profile_name_lower}_wid import {profile_name_lower}_wid_hdl
from autopts.client import get_unique_name
from autopts.pybtp.types import Addr


def set_pixits(ptses):
    pts = ptses[0]

    pts.set_pixit("{profile_name_upper}", "TSPX_time_guard", "180000")
    pts.set_pixit("{profile_name_upper}", "TSPX_use_implicit_send", "TRUE")


def test_cases(ptses):
    \"\"\"
    Returns a list of {profile_name_upper} test cases
    ptses -- list of PyPTS instances
    \"\"\"

    pts = ptses[0]
    pts_bd_addr = pts.q_bd_addr
    iut_device_name = get_unique_name(pts)
    stack = get_stack()

    # Generic preconditions for all test case in the profile
    pre_conditions = [
        TestFunc(btp.core_reg_svc_gap),
        TestFunc(stack.gap_init, iut_device_name),
        TestFunc(btp.gap_read_ctrl_info),
        TestFunc(lambda: pts.update_pixit_param(
                 "{profile_name_upper}", "TSPX_bd_addr_iut",
                 stack.gap.iut_addr_get_str())),
        TestFunc(btp.set_pts_addr, pts_bd_addr, Addr.le_public),
        TestFunc(btp.core_reg_svc_gatt),
        TestFunc(stack.gatt_init),
        TestFunc(btp.core_reg_svc_{profile_name_lower}),
        TestFunc(stack.{profile_name_lower}_init)
    ]

    test_case_name_list = pts.get_test_case_list('{profile_name_upper}')
    tc_list = []

    # Use the same preconditions and MMI/WID handler for all test cases of the profile
    for tc_name in test_case_name_list:
        instance = ZTestCase('{profile_name_upper}', tc_name, cmds=pre_conditions,
                             generic_wid_hdl={profile_name_lower}_wid_hdl)

        tc_list.append(instance)

    return tc_list
""",
    # END of autopts/ptsprojects/zephyr/profile.py

    # START of autopts/ptsprojects/zephyr/profile_wid.py
    f'{project_path}/{profile_name_lower}_wid.py':
f"""{license_text}

import logging

from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def {profile_name_lower}_wid_hdl(wid, description, test_case_name):
"""
"    log(f'{" + profile_name_lower + "_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')\n"
f"    return generic_wid_hdl(wid, description, test_case_name, [__name__, 'autopts.wid.{profile_name_lower}'])\n",
    # END of autopts/ptsprojects/zephyr/profile_wid.py

    # START of autopts/wid/profile.py
    f'{AUTOPTS_REPO}/autopts/wid/{profile_name_lower}.py':
f"""{license_text}
import logging
from autopts.pybtp.types import WIDParams
from autopts.wid import generic_wid_hdl

log = logging.debug


def {profile_name_lower}_wid_hdl(wid, description, test_case_name):
"""
"    log(f'{" + profile_name_lower + "_wid_hdl.__name__}, {wid}, {description}, {test_case_name}')\n"
"""    return generic_wid_hdl(wid, description, test_case_name, [__name__])


# wid handlers section begin
def hdl_wid_1(params: WIDParams):
    # Example WID

    return True
""",
    # END of autopts/wid/profile.py

    # START of autopts/pybtp/btp/profile.py
    f'{AUTOPTS_REPO}/autopts/pybtp/btp/{profile_name_lower}.py':
f"""{license_text}
import binascii
import logging
import struct

from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut, \\
    btp_hdr_check
from autopts.pybtp.types import BTPError

log = logging.debug


{profile_name_upper} = """ + "{" + f"""
    'read_supported_cmds': (defs.BTP_SERVICE_ID_{profile_name_upper},
                            defs.BTP_{profile_name_upper}_CMD_READ_SUPPORTED_COMMANDS,
                            CONTROLLER_INDEX),
""" + "}" + f"""


def {profile_name_lower}_command_rsp_succ(timeout=20.0):
    logging.debug("%s", {profile_name_lower}_command_rsp_succ.__name__)

    iutctl = get_iut()

    tuple_hdr, tuple_data = iutctl.btp_socket.read(timeout)
    logging.debug("received %r %r", tuple_hdr, tuple_data)

    btp_hdr_check(tuple_hdr, defs.BTP_SERVICE_ID_{profile_name_upper})

    return tuple_data


# An example event, to be changed or deleted
def {profile_name_lower}_ev_dummy_completed({profile_name_lower}, data, data_len):
    logging.debug('%s %r', {profile_name_lower}_ev_dummy_completed.__name__, data)

    fmt = '<B6sB'
    if len(data) < struct.calcsize(fmt):
        raise BTPError('Invalid data length')

    addr_type, addr, status = struct.unpack_from(fmt, data)

    addr = binascii.hexlify(addr[::-1]).lower().decode('utf-8')

    logging.debug(f'{profile_name_upper} Dummy event completed: addr {'{'}addr{'}'} addr_type '
                  f'{'{'}addr_type{'}'} status {'{'}status{'}'}')

    {profile_name_lower}.event_received(defs.BTP_{profile_name_upper}_EV_DUMMY_COMPLETED, (addr_type, addr, status))


{profile_name_upper}_EV = {'{'}
    defs.BTP_{profile_name_upper}_EV_DUMMY_COMPLETED: {profile_name_lower}_ev_dummy_completed,
{'}'}
""",
    # END of autopts/pybtp/btp/profile.py

    # START of autopts/ptsprojects/stack/layers/profile.py
    f'{AUTOPTS_REPO}/autopts/ptsprojects/stack/layers/{profile_name_lower}.py':
f"""{license_text}
from autopts.ptsprojects.stack.common import wait_event_with_condition
from autopts.pybtp import defs


class {profile_name_upper}:
    def __init__(self):
        self.event_queues = {'{'}
            defs.BTP_{profile_name_upper}_EV_DUMMY_COMPLETED: [],
        {'}'}

    def event_received(self, event_type, event_data):
        self.event_queues[event_type].append(event_data)

    def wait_dummyevent_completed_ev(self, addr_type, addr, timeout, remove=True):
        return wait_event_with_condition(
            self.event_queues[defs.BTP_{profile_name_upper}_EV_DUMMY_COMPLETED],
            lambda _addr_type, _addr, *_:
                (addr_type, addr) == (_addr_type, _addr),
            timeout, remove)
""",
    # END of autopts/ptsprojects/stack/layers/profile.py

    # START of doc/btp_profile.txt
    f'{AUTOPTS_REPO}/doc/btp_{profile_name_lower}.txt':
f"""{profile_name_upper} Service (ID {profile_id})
=====================

Commands and responses:

	Opcode 0x00 - Error response

	Opcode 0x01 - Read Supported Commands command/response

		Controller Index:	<controller id>
		Command parameters:	<none>
		Response parameters:	<supported commands> (variable)

		Each bit in response is a flag indicating if command with
		opcode matching bit number is supported. Bit set to 1 means
		that command is supported. Bit 0 is reserved and shall always
		be set to 0. If specific bit is not present in response (less
		than required bytes received) it shall be assumed that command
		is not supported.

		In case of an error, the error response will be returned.

Events:
	Opcode 0x80 - Dummy event

		Controller Index:	<controller id>
		Event parameters:	Address_Type (1 octet)
					Address (6 octets)
					Status  (1 octet)

        This dummy event indicates something that happens asynchronously
        e.g. IUT finished discovery, a notification arrived, etc.
"""
    # END of doc/btp_profile.txt
}

changes_to_prepend = {
    f"{project_path}/__init__.py": {
        1: (
            f"               {profile_name_lower},\n"
        ),
        2: (
            f"""    "{profile_name_lower}",\n"""
        ),
    },
    f"{AUTOPTS_REPO}/autopts/pybtp/defs.py": {
        1: f"BTP_SERVICE_ID_{profile_name_upper} = {hex(int(profile_id))}\n",
        2: (
            f"BTP_{profile_name_upper}_CMD_READ_SUPPORTED_COMMANDS = 0x01\n"
            f"BTP_{profile_name_upper}_EV_DUMMY_COMPLETED = 0x80\n\n"
        ),
    },
    f'{AUTOPTS_REPO}/autopts/ptsprojects/stack/layers/__init__.py': {1: f"from .{profile_name_lower} import *"
    "  # noqa: F403 # used in many files : TODO import directly in files not with *\n"},
    f'{AUTOPTS_REPO}/autopts/ptsprojects/stack/stack.py': {
        1: f"from autopts.ptsprojects.stack.layers.{profile_name_lower} import {profile_name_upper}\n",
        2: f"        self.{profile_name_lower} = None\n",
        3: f"    def {profile_name_lower}_init(self):\n        self.{profile_name_lower} = {profile_name_upper}()\n\n",
        4: f"        if self.{profile_name_lower}:\n            self.{profile_name_lower}_init()\n\n",
    },
    f'{AUTOPTS_REPO}/autopts/wid/__init__.py': {
        1: f"from .{profile_name_lower} import {profile_name_lower}_wid_hdl\n",
        2: f'    "{profile_name_lower}_wid_hdl",\n'
    },
    f'{AUTOPTS_REPO}/autopts/pybtp/btp/btp.py': {
        1: f"""def core_reg_svc_{profile_name_lower}():
    core_reg_svc_univ("{profile_name_lower}_reg", "{profile_name_upper}")


""",
        2: f"        {profile_name_upper}_EV,\n",
        3: f"        defs.BTP_SERVICE_ID_{profile_name_upper}: ({profile_name_upper}_EV, stack.{profile_name_lower}),\n",
    },
    f'{AUTOPTS_REPO}/autopts/pybtp/btp/__init__.py': {1: f"from autopts.pybtp.btp.{profile_name_lower} import *"
    "  # noqa: F403 # used in many files : TODO import directly in files not with *\n"},
    f'{AUTOPTS_REPO}/doc/overview.txt': {1: f" {hex(int(profile_id))} {profile_name_upper} Service\n"},
    f'{AUTOPTS_REPO}/autopts/pybtp/common.py': {
        1: f"""    "{profile_name_upper}": {'{'}
        "supported_commands": defs.BTP_{profile_name_upper}_CMD_READ_SUPPORTED_COMMANDS
    {'}'},
""",
        2: f"""    "{profile_name_lower}_reg": (defs.BTP_SERVICE_ID_{profile_name_upper}, defs.BTP_CORE_CMD_REGISTER_SERVICE,
                defs.BTP_INDEX_NONE, defs.BTP_SERVICE_ID_{profile_name_upper}),
""",
    },
    f'{AUTOPTS_REPO}/autopts/pybtp/btp/event_map.py': {
        1: f"from .{profile_name_lower} import {profile_name_upper}_EV\n",
        2: f'    "{profile_name_upper}_EV",\n'
    },
}


for file in files_to_create:
    create_file(file, files_to_create[file])


for file in changes_to_prepend:
    for change_id in changes_to_prepend[file]:
        lines_to_prepend = changes_to_prepend[file][change_id]
        append_lines(file, change_id, lines_to_prepend)
