#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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
import logging
import threading
from time import sleep

from autopts.utils import ResultWithFlag

log = logging.debug


class SynchPoint:
    def __init__(self, test_case, wid, delay=None):
        self.test_case = test_case
        self.wid = wid
        self.delay = delay
        self.done = None

    def set_done(self):
        self.done.set(True)

    def clear(self):
        self.done.clear()

    def wait(self):
        self.done.wait()


class SynchElem:
    def __init__(self, sync_points):
        self.sync_points = sync_points
        self.active_synch_point = None
        count = len(sync_points)
        self._start_barrier = threading.Barrier(count, self.clear_flags)
        self._end_barrier = threading.Barrier(count, self.clear_flags)

    def find_matching(self, test_case, wid):
        matching_items = [item for item in self.sync_points if
                          item.test_case == test_case and item.wid == wid]
        if matching_items:
            return matching_items[0]
        return None

    def clear_flags(self):
        for point in self.sync_points:
            point.clear()

    def wait_for_start(self):
        # While debugging, do not step over Barrier.wait() or other
        # waits from threading module. This may cause the GIL deadlock.
        self._start_barrier.wait()

    def wait_for_end(self):
        self._end_barrier.wait()

    def wait_for_your_turn(self, synch_point):
        for point in self.sync_points:
            if point == synch_point:
                self.active_synch_point = synch_point
                return

            point.wait()

            if self._start_barrier.broken or self._end_barrier.broken:
                raise threading.BrokenBarrierError

    def cancel_synch(self):
        self._end_barrier.abort()
        self._start_barrier.abort()

        for point in self.sync_points:
            point.set_done()


class Synch:
    def __init__(self):
        self._synch_table = []
        self._synch_condition = threading.Condition()

    def reinit(self):
        self.cancel_synch()
        self._synch_table.clear()

    def add_synch_element(self, elem):
        for sync_point in elem:
            # If a test case has to be repeated, its SyncPoints will be reused.
            # Reinit done-flags to renew potentially broken locks.
            sync_point.done = ResultWithFlag()

        self._synch_table.append(SynchElem(elem))

    def wait_for_start(self, wid, tc_name):
        synch_point = None
        elem = None

        for _i, elem in enumerate(self._synch_table):
            synch_point = elem.find_matching(tc_name, wid)
            if synch_point:
                # Found a sync point matching the test case and wid
                break

        if not synch_point:
            # No synch point found
            return None

        log(f'SYNCH: Waiting at barrier for start, tc {tc_name} wid {wid}')
        elem.wait_for_start()
        log(f'SYNCH: Waiting for turn to start, tc {tc_name} wid {wid}')

        elem.wait_for_your_turn(synch_point)
        log(f'SYNCH: Started tc {tc_name} wid {wid}')

        return elem

    def wait_for_end(self, synch_elem):
        synch_point = synch_elem.active_synch_point

        if synch_point.delay:
            sleep(synch_point.delay)

        # Let other LT-threads know that this one completed the wid
        synch_point.set_done()
        tc_name = synch_point.test_case
        wid = synch_point.wid

        log(f'SYNCH: Waiting at end barrier, tc {tc_name} wid {wid}')
        synch_elem.wait_for_end()
        log(f'SYNCH: Finished waiting at end barrier, tc {tc_name} wid {wid}')

        # Remove the synch element
        try:
            self._synch_table.remove(synch_elem)
        except ValueError:
            # Already cleaned up by other thread
            pass
        return None

    def cancel_synch(self):
        for elem in self._synch_table:
            elem.cancel_synch()
        self._synch_table = []
