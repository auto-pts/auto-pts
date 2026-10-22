#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, Nordic Semiconductor ASA.
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

"""NLC Profile Test Suites: ALSNLCP, BLCNLCP, BSSNLCP, DICNLCP, ENMNLCP,
HVINLCP and OCSNLCP.

The module provides the PIXITs and the Test Cases of all seven Profiles.
At the end of the file, it is registered under the name of every Profile
listed in NLCP_TS_LIST, so the Client finds it by the Test Case prefix.

We only have two different sets of preconditions applied at the beginning of
each NLC Profile Test Case: with the normal and with a longer Auto-PTS Client
Test Case timeout. In the init precondition step, after the IUT ready event is
received from the IUT, the IUT UUID is read and the corresponding PIXIT
(TSPX_device_uuid) is updated.

Performance Test Cases (*/GMIT/PERF/*) run longer than the default Auto-PTS
Client Test Case timeout, so a longer timeout is used for them.
"""


import sys
from fnmatch import fnmatchcase

from autopts.ptsprojects.stack import get_stack
from autopts.ptsprojects.testcase import TestFunc, TestFuncCleanUp
from autopts.ptsprojects.zephyr.nlcp_wid import nlcp_wid_hdl
from autopts.ptsprojects.zephyr.ztestcase import ZTestCase
from autopts.pybtp import btp

# Test Suites (Profiles) supported by this module.
NLCP_TS_LIST = ("ALSNLCP", "BLCNLCP", "BSSNLCP", "DICNLCP",
                "ENMNLCP", "HVINLCP", "OCSNLCP")

# Default PIXITs, applied to every Test Case of every Profile.
# PIXITs should always be updated according to the project and the newest
# version of PTS.
PROFILE_COMMON_PIXITS = {
    "TSPX_bd_addr_iut": "DEADBEEFDEAD",
    "TSPX_time_guard": "300000",
    "TSPX_use_implicit_send": "TRUE",
    "TSPX_mtu_size": "23",
    # FALSE: PTS keeps the keys from the previous Test Case and reuses them.
    # When a Test Case needs a new provisioning, PTS asks the IUT to remove
    # the keys itself.
    # TRUE: PTS removes the keys before each Test Case, so the IUT is
    # provisioned again in every Test Case (longer run time).
    "TSPX_delete_link_key": "FALSE",
    "TSPX_delete_ltk": "FALSE",
    "TSPX_security_enabled": "FALSE",
    "TSPX_iut_setup_att_over_br_edr": "FALSE",
    "TSPX_scan_interval": "30",
    "TSPX_scan_window": "30",
    "TSPX_scan_filter": "00",
    "TSPX_advertising_interval_min": "160",
    "TSPX_advertising_interval_max": "160",
    "TSPX_tester_OOB_information": "F87F",
    "TSPX_device_uuid2": "00000000000000000000000000000000",
    "TSPX_use_pb_gatt_bearer": "TRUE",
    "TSPX_iut_comp_data_page": "2",
    "TSPX_oob_state_change": "FALSE",
}
# Per-Profile PIXIT overrides, merged over the common ones.
# Pattern here: {"<NLC_PROFILE>": {"TSPX_...": "..."}}
# Example (values are for illustration only):
# {
#     "BSSNLCP": {"TSPX_scan_interval": "60", "TSPX_scan_window": "60"},
#     "HVINLCP": {"TSPX_time_guard": "600000"},
# }
PROFILE_EXTRA_PIXITS = {}

# Default Auto-PTS timeout duration for the Client, in ms.
TC_COMMON_CLI_TIMEOUT_MS = 300000
# Timeout duration for Performance Test Cases, in ms.
TC_PERF_CLI_TIMEOUT_MS = 900000


def _nlcp_pixit_update_identity(pts, profile):
    """Pass the IUT Device UUID to PTS (TSPX_device_uuid).

    PTS looks for Unprovisioned Device beacons with this UUID to start
    provisioning.
    """
    nlcp = get_stack().nlcp
    pts.update_pixit_param(profile, "TSPX_device_uuid", nlcp.get_identity_uuid())


def _nlcp_get_profiles(pts):
    """Return the NLC Profiles, which are present in the PTS workspace."""
    profiles_list = pts.get_project_list()
    return [profile for profile in NLCP_TS_LIST if profile in profiles_list]


def _nlcp_get_cli_default_timeout_ms():
    """Return the default Test Case timeout of the Auto-PTS Client, in ms."""
    client = sys.modules.get("autopts.client")
    return getattr(client, "TEST_CASE_TIMEOUT_MS", TC_COMMON_CLI_TIMEOUT_MS)


def _nlcp_preconditions_default(pts, profile, stack):
    """Default precondition set."""
    return [
        TestFunc(stack.nlcp_init),
        TestFunc(btp.nlcp_read_identity_report),
        TestFunc(lambda: _nlcp_pixit_update_identity(pts, profile)),
    ]


def _nlcp_preconditions_performance(pts, profile, stack):
    """Performance Test Case: default preconditions with a longer Auto-PTS
    Client Test Case timeout (see TC_PERF_CLI_TIMEOUT_MS).
    """
    return (_nlcp_preconditions_default(pts, profile, stack) +
            _nlcp_tc_launch(pts, TC_PERF_CLI_TIMEOUT_MS))


# Test Cases with preconditions different from _nlcp_preconditions_default().
# Each entry is a Test Case name pattern and the function with its preconditions.
# The first matching pattern is used.
# To add a new case, write a _nlcp_preconditions_*() function and add it here,
# e.g. ("BSSNLCP/*", _nlcp_preconditions_bss).
TC_PRECONDITIONS = (
    ("*/GMIT/PERF/*", _nlcp_preconditions_performance),
)


def _nlcp_preconditions_build(pts, profile, stack, tc_name):
    """Build and return the set of preconditions tailored for the given Test
    Case.
    """
    for pattern, build in TC_PRECONDITIONS:
        if fnmatchcase(tc_name, pattern):
            return build(pts, profile, stack)
    return _nlcp_preconditions_default(pts, profile, stack)


def _nlcp_tc_launch(pts, timeout_ms):
    """Set a longer PTS Client timeout for this specific Test Case.

    The timeout is set back to default after the Test Case, even if it fails.
    """
    return [
        TestFunc(lambda: pts.set_call_timeout(timeout_ms)),
        TestFuncCleanUp(lambda: pts.set_call_timeout(_nlcp_get_cli_default_timeout_ms())),
    ]


def set_pixits(ptses):
    """Set up the default PIXITs of the NLC Profiles in the PTS workspace.

    For each Profile, PROFILE_COMMON_PIXITS are applied, with the overrides
    from PROFILE_EXTRA_PIXITS. These values are used for a Test Case, if they
    are not updated within the Test Case.

    ptses -- list of PyPTS instances
    """

    pts = ptses[0]

    for profile in _nlcp_get_profiles(pts):
        pixits = {**PROFILE_COMMON_PIXITS, **PROFILE_EXTRA_PIXITS.get(profile, {})}
        for name, value in pixits.items():
            pts.set_pixit(profile, name, value)


def test_cases(ptses):
    """
    Returns the list of NLC Profiles Test Cases.

    The Test Case list of each Profile is taken from the PTS workspace.

    ptses -- list of PyPTS instances
    """

    pts = ptses[0]
    stack = get_stack()

    tc_list = []

    # Cycle all of the supported Profiles.
    for profile in _nlcp_get_profiles(pts):
        # Build a list of the Test Cases for the Profile with preconditions.
        tc_list.extend(
            ZTestCase(profile, tc_name,
                      cmds=_nlcp_preconditions_build(pts, profile, stack, tc_name),
                      generic_wid_hdl=nlcp_wid_hdl)
            for tc_name in pts.get_test_case_list(profile)
        )

    return tc_list


# Register this module under the name of every NLC Profile, so the client
# lookup by the Test Case prefix (e.g. HVINLCP -> hvinlcp) finds this file.
_this = sys.modules[__name__]
_pkg = sys.modules[__package__]
for _p in NLCP_TS_LIST:
    _alias = _p.lower()
    setattr(_pkg, _alias, _this)                      # getattr(zephyr, 'hvinlcp')
    sys.modules[f"{__package__}.{_alias}"] = _this    # import_module('...zephyr.hvinlcp')
