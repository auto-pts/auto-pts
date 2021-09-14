#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2021, Intel Corporation.
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

supported_projects = ['zephyr']


def reset_cmd(iutctl):
    """Return reset command for nRF52 DUT

    Dependency: nRF5x command line tools
    """
    with_srn = ''

    if iutctl.debugger_snr:
        with_srn = ' -s {}'.format(iutctl.debugger_snr)

    return 'nrfjprog -f nrf52 -r {}'.format(with_srn)
