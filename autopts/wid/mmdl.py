#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2017, Intel Corporation.
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
import re
import struct
import time

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import btp
from autopts.pybtp.types import WIDParams

# MMDL ATS ver. 1.0
log = logging.debug


def iut_reset():
    # Wait a few seconds before resetting so that all settings are stored on the flash
    # Some models save from a callback that is triggered after a few seconds.
    time.sleep(5)
    zephyrctl = btp.get_iut_method()

    zephyrctl.wait_iut_ready_event()
    btp.core_reg_svc_gap()
    btp.core_reg_svc_mesh()
    btp.mesh_init()
    btp.gap_read_ctrl_info()
    btp.mesh_start()


def hdl_wid_13(_: WIDParams):
    """
    Implements: RE_PROVISIONING_PROVISIONER
    description: There is no shared security information. Please remove any
                 security information if any. PTS is waiting for beacon to
                 start provisioning from
    """
    stack = get_stack()

    if not stack.mesh.is_initialized:
        btp.mesh_config_prov()
        btp.mesh_start()

    if stack.mesh.is_provisioned.data:
        btp.mesh_reset()

    return True


def hdl_wid_303(_: WIDParams):
    """
    Implements:
    description: Please send Friend Request to initiate the Friendship Establishment procedure.
    """

    btp.mesh_lpn(True)
    return True


def hdl_wid_304(_: WIDParams):
    """
    Implements:
    description: Please click OK to send Friend Poll message.
    """

    btp.mesh_lpn_poll()
    return True


def hdl_wid_346(_: WIDParams):
    """
    Implements:
    description: Please send Friend Subscription List Add message to Lower Tester.
    """

    return True


def hdl_wid_515(_: WIDParams):
    """
    MMDL/SR/SCH/BV-01-C

    description: Please confirm the following message is correct.
    """
    return True


def hdl_wid_523(_: WIDParams):
    """
    MMDL/SR/LLC/BV-07-C

    description: Please change IUT's Light LC Occupancy state to 1,
                 simulating that occupancy has been reported by occupancy sensors.
    """
    return True


def hdl_wid_525(_: WIDParams):
    """
    MMDL/SR/LLC/BV-08-C

    description: Please change the IUT's Light LC Property states are set
                 such that the transitions of the Light LC Light OnOff state
                 are immediate by default (transition time of zero).
    """
    return True


def hdl_wid_526(_: WIDParams):
    """
    :param desc: Please remove application and network security on IUT.
                 Click OK to when the IUT is in unprovisioned state.
    """
    return True


def hdl_wid_630(_: WIDParams):
    iut_reset()
    return True


def hdl_wid_631(_: WIDParams):
    iut_reset()
    return True


def hdl_wid_652(_: WIDParams):
    """
    Implements: CONFIRM_GENERIC
    description: Please confirm the %s = %s.
    """
    # TODO: Confirm composition data
    return True


def parse_command_params(description):
    field_dict = {}
    txt = description.splitlines()[1:]
    for line in txt:
        line = line.strip()
        fields = line.split(': ', 1)
        if len(fields) < 2:
            continue
        field_name = fields[0]
        m = re.search(r"\[([\-A-Fa-f0-9x() ]+)]", fields[1])
        if not m:
            field_dict[field_name] = None
            continue
        value = m.group(1)

        m = re.search(r"\(([A-Fa-f0-9x]+)\)", value)
        if not m:
            field_dict[field_name] = int(value, 16)
            continue

        hex_value = m.group(1)
        field_dict[field_name] = int(hex_value, 16)

    return field_dict


def gen_onoff_get(_):
    btp.mmdl_gen_onoff_get()
    return True


def gen_onoff_set(params, ack):
    onoff = params['OnOff']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_gen_onoff_set(onoff, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [onoff])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_onoff_set_ack(params):
    return gen_onoff_set(params, ack=True)


def gen_onoff_set_unack(params):
    return gen_onoff_set(params, ack=False)


def gen_onoff_status(params):
    present_onoff = params['Present OnOff']
    stack = get_stack()
    return [present_onoff] == stack.mesh.recv_status_data_get('Status')


def gen_lvl_get(_):
    btp.mmdl_gen_lvl_get()
    return True


def gen_lvl_set(params, ack):
    lvl = params['Level']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_gen_lvl_set(lvl, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [lvl])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_lvl_set_ack(params):
    return gen_lvl_set(params, ack=True)


def gen_lvl_set_unack(params):
    return gen_lvl_set(params, ack=False)


def gen_lvl_delta_set(params, ack):
    lvl = params['Delta Level']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_gen_lvl_delta_set(lvl, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [lvl + 4352])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_lvl_set_delta_ack(params):
    return gen_lvl_delta_set(params, ack=True)


def gen_lvl_set_delta_unack(params):
    return gen_lvl_delta_set(params, ack=False)


def gen_lvl_move_set(params, ack):
    lvl = params['Delta Level Move']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_gen_lvl_move_set(lvl, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [lvl + 4352])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_lvl_set_move_ack(params):
    return gen_lvl_move_set(params, ack=True)


def gen_lvl_set_move_unack(params):
    return gen_lvl_move_set(params, ack=False)


def gen_lvl_status(params):
    current_lvl = params['Present Level']
    stack = get_stack()
    return [current_lvl] == stack.mesh.recv_status_data_get('Status')


def gen_dtt_get(_):
    btp.mmdl_gen_dtt_get()
    return True


def gen_dtt_set(params, ack):
    tt = params['Transition Time']
    btp.mmdl_gen_dtt_set(tt, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [tt])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_dtt_set_ack(params):
    return gen_dtt_set(params, ack=True)


def gen_dtt_set_unack(params):
    return gen_dtt_set(params, ack=False)


def gen_dtt_status(params):
    tt = params['Transition Time']
    stack = get_stack()
    return [tt] == stack.mesh.recv_status_data_get('Status')


def gen_ponoff_get(_):
    btp.mmdl_gen_ponoff_get()
    return True


def gen_ponoff_set(params, ack):
    on_power_up = params['OnPowerUp']
    btp.mmdl_gen_ponoff_set(on_power_up, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [on_power_up])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_ponoff_set_ack(params):
    return gen_ponoff_set(params, ack=True)


def gen_ponoff_set_unack(params):
    return gen_ponoff_set(params, ack=False)


def gen_ponoff_status(params):
    on_power_up = params['OnPowerUp']
    stack = get_stack()
    return [on_power_up] == stack.mesh.recv_status_data_get('Status')


def gen_plvl_get(_):
    btp.mmdl_gen_plvl_get()
    return True


def gen_plvl_set(params, ack):
    power_level = params['Present Power']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_gen_plvl_set(power_level, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [power_level])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_plvl_set_ack(params):
    return gen_plvl_set(params, ack=True)


def gen_plvl_set_unack(params):
    return gen_plvl_set(params, ack=False)


def gen_plvl_status(params):
    power_level = params['Present Power']
    stack = get_stack()
    return [power_level] == stack.mesh.recv_status_data_get('Status')


def gen_plvl_dflt_get(_):
    btp.mmdl_gen_plvl_dflt_get()
    return True


def gen_plvl_last_get(_):
    btp.mmdl_gen_plvl_last_get()
    return True


def gen_plvl_last_status(params):
    power_level = params['Power Last']
    stack = get_stack()
    return [power_level] == stack.mesh.recv_status_data_get('Status')


def gen_plvl_dflt_set(params, ack):
    power_default = params['Power Default']
    btp.mmdl_gen_plvl_dflt_set(power_default, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [power_default])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_plvl_dflt_set_ack(params):
    return gen_plvl_dflt_set(params, ack=True)


def gen_plvl_dflt_set_unack(params):
    return gen_plvl_dflt_set(params, ack=False)


def gen_plvl_dflt_status(params):
    power_default = params['Present Power']
    stack = get_stack()
    return [power_default] == stack.mesh.recv_status_data_get('Status')


def gen_plvl_range_get(_):
    btp.mmdl_gen_plvl_range_get()
    return True


def gen_plvl_range_set(params, ack):
    range_min = params['Range Min']
    range_max = params['Range Max']
    btp.mmdl_gen_plvl_range_set(range_min, range_max, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [0, range_min, range_max])
    stack.mesh.expect_status_data_set('Ack', ack)
    return True


def gen_plvl_range_set_ack(params):
    return gen_plvl_range_set(params, ack=True)


def gen_plvl_range_set_unack(params):
    return gen_plvl_range_set(params, ack=False)


def gen_plvl_range_status(params):
    range_min = params['Range Min']
    range_max = params['Range Max']
    status = params['Status']
    stack = get_stack()
    return [status, range_min, range_max] == stack.mesh.recv_status_data_get('Status')


def gen_battery_get(_):
    btp.mmdl_gen_battery_get()
    return True


def gen_battery_status(params):
    power_default = params['Battery Level']
    discharge_min = params['Time to Discharge']
    charge_min = params['Time to Charge']
    flags = params['Flags']
    stack = get_stack()
    return [power_default, discharge_min, charge_min, flags] == stack.mesh.recv_status_data_get('Status')


def gen_loc_global_get(_):
    btp.mmdl_gen_loc_global_get()
    return True


def gen_loc_global_set(params, ack):
    lat = params['Global Latitude']
    lon = params['Global Longitude']
    alt = params['Global Altitude']

    btp.mmdl_gen_loc_global_set(lat, lon, alt, ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [lat, lon, alt])
    return True


def gen_loc_global_set_ack(params):
    return gen_loc_global_set(params, True)


def gen_loc_global_set_unack(params):
    return gen_loc_global_set(params, False)


def gen_loc_global_status(params):
    lat = params['Global Latitude']
    lon = params['Global Longitude']
    alt = params['Global Altitude']
    stack = get_stack()
    return [lat, lon, alt] == stack.mesh.recv_status_data_get('Status')


def gen_loc_local_get(_):
    btp.mmdl_gen_loc_local_get()
    return True


def gen_loc_local_set(params, ack):
    north = params['Local North']
    east = params['Local East']
    alt = params['Local Altitude']
    floor = params['Floor']
    location_uncert = params['Location Uncertainty']

    btp.mmdl_gen_loc_local_set(north, east, alt, floor, location_uncert, ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set(
        'Status', [north, east, alt, floor, location_uncert])
    return True


def gen_loc_local_set_ack(params):
    return gen_loc_local_set(params, True)


def gen_loc_local_set_unack(params):
    return gen_loc_local_set(params, False)


def gen_loc_local_status(params):
    north = params['Local North']
    east = params['Local East']
    alt = params['Local Altitude']
    floor = params['Floor']
    location_uncert = params['Location Uncertainty']

    stack = get_stack()
    return [north, east, alt, floor, location_uncert] == stack.mesh.recv_status_data_get('Status')


def gen_mfr_props_get(_):
    btp.mmdl_gen_props_get(kind=0x00)
    return True


def gen_mfr_props_status(params):
    prop_id = params['Property IDs']

    stack = get_stack()
    return [prop_id] == stack.mesh.recv_status_data_get('Status')


def gen_mfr_prop_get(params):
    prop_id = params['Property ID']
    btp.mmdl_gen_prop_get(kind=0x00, prop_id=prop_id)
    return True


def gen_mfr_prop_set(params, ack):
    prop_id = params['Property ID']
    access = params.get('Access', 3)
    btp.mmdl_gen_prop_set(0x00, prop_id, access, '', ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [prop_id, access, ''])
    return True


def gen_mfr_prop_set_ack(params):
    return gen_mfr_prop_set(params, ack=True)


def gen_mfr_prop_set_unack(params):
    return gen_mfr_prop_set(params, ack=False)


def gen_mfr_prop_status(params):
    prop_id = params['Property ID']
    val = params['Property Value']
    access = params['Access']

    stack = get_stack()
    return [prop_id, access, val] == stack.mesh.recv_status_data_get('Status')


def gen_admin_props_get(_):
    btp.mmdl_gen_props_get(kind=0x01)
    return True


def gen_admin_props_status(params):
    prop_id = params['Property IDs']

    stack = get_stack()
    return [prop_id] == stack.mesh.recv_status_data_get('Status')


def gen_admin_prop_get(params):
    prop_id = params['Property ID']
    btp.mmdl_gen_prop_get(kind=0x01, prop_id=prop_id)
    return True


def gen_admin_prop_set(params, ack):
    prop_id = params['Property ID']
    val = params['Property Value']
    access = params.get('Access', 3)
    payload = hex(val)[2:]
    btp.mmdl_gen_prop_set(0x01, prop_id, access, payload, ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [prop_id, access, val])
    return True


def gen_admin_prop_set_ack(params):
    return gen_admin_prop_set(params, ack=True)


def gen_admin_prop_set_unack(params):
    return gen_admin_prop_set(params, ack=False)


def gen_admin_prop_status(params):
    prop_id = params['Property ID']
    val = params['Property Value']
    access = params['Access']

    stack = get_stack()
    return [prop_id, access, val] == stack.mesh.recv_status_data_get('Status')


def gen_usr_props_get(_):
    btp.mmdl_gen_props_get(kind=0x02)
    return True


def gen_usr_prop_set(params, ack):
    prop_id = params['Property ID']
    val = params['Property Value']
    access = params.get('Access', 3)
    payload = hex(val)[2:]
    btp.mmdl_gen_prop_set(0x02, prop_id, access, payload, ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [prop_id, access, val])
    return True


def gen_usr_prop_set_ack(params):
    return gen_usr_prop_set(params, ack=True)


def gen_usr_prop_set_unack(params):
    return gen_usr_prop_set(params, ack=False)


def gen_usr_props_status(params):
    prop_id = params['Property IDs']

    stack = get_stack()
    return [prop_id] == stack.mesh.recv_status_data_get('Status')


def gen_usr_prop_get(params):
    prop_id = params['Property ID']
    btp.mmdl_gen_prop_get(kind=0x02, prop_id=prop_id)
    return True


def gen_usr_prop_status(params):
    prop_id = params['Property ID']
    val = params['Property Value']
    access = params['Access']
    stack = get_stack()
    return [prop_id, access, val] == stack.mesh.recv_status_data_get('Status')


def gen_cli_props_get(params):
    prop_id = params['Property ID']
    btp.mmdl_gen_props_get(kind=0x03, prop_id=prop_id)
    return True


def gen_cli_props_status(params):
    prop_id = params['Property IDs']

    stack = get_stack()
    return [prop_id] == stack.mesh.recv_status_data_get('Status')


def sensor_desc_get(params):
    if 'PropertyId' in params:
        sensor_id = 0x0042
    else:
        sensor_id = None
    btp.mmdl_sensor_desc_get(sensor_id)
    return True


def sensor_desc_status(params):
    stack = get_stack()
    return [params['Descriptor']] == stack.mesh.recv_status_data_get('Status')


def sensor_get(params):
    if 'PropertyId' in params:
        sensor_id = 0x0042
    else:
        sensor_id = None
    btp.mmdl_sensor_get(sensor_id)
    return True


def sensor_status(params):
    stack = get_stack()
    if '[0] Type' and '[1] Type' and '[2] Type' in params:
        sensor_id_0 = int('0042', 16)
        sensor_data_0 = 12
        sensor_id_1 = int('004E', 16)
        sensor_data_1 = 563412
        sensor_id_2 = int('006F', 16)
        sensor_data_2 = 563412
        stack.mesh.expect_status_data_set('Status', [
            sensor_id_0, sensor_data_0, sensor_id_1, sensor_data_1, sensor_id_2, sensor_data_2])
    elif '[0] Type' in params:
        sensor_id_0 = int('0042', 16)
        sensor_data_0 = 12
        stack.mesh.expect_status_data_set(
            'Status', [sensor_id_0, sensor_data_0])
    return stack.mesh.expect_status_data_get('Status') == stack.mesh.recv_status_data_get('Status')


def sensor_cadence_get(_):
    sensor_id = 0x0042
    btp.mmdl_sensor_cadence_get(sensor_id)
    return True


def sensor_cadence_set(_, ack):
    sensor_id = 0x0042
    cadence_data = "0100a00100a0"
    btp.mmdl_sensor_cadence_set(sensor_id, cadence_data, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [cadence_data])
    return True


def sensor_cadence_set_ack(params):
    return sensor_cadence_set(params, True)


def sensor_cadence_set_unack(params):
    return sensor_cadence_set(params, False)


def sensor_cadence_status(params):
    prop_id = params['PropertyId']
    cadence_data = params['CadenceData']

    stack = get_stack()
    return [prop_id, cadence_data] == stack.mesh.recv_status_data_get('Status')


def sensor_settings_get(_):
    sensor_id = 0x0042
    btp.mmdl_sensor_settings_get(sensor_id)
    return True


def sensor_settings_status(params):
    sensor_id = params['PropertyId']
    settings = params['SensorSettingPropertyIds']

    stack = get_stack()
    return [sensor_id, settings] == stack.mesh.recv_status_data_get('Status')


def sensor_setting_get(_):
    sensor_id = 0x004e
    setting_id = 0x006e
    btp.mmdl_sensor_setting_get(sensor_id, setting_id)
    return True


def sensor_setting_set(_, ack):
    sensor_id = 0x004e
    setting_id = 0x006e
    setting_raw = '00'
    btp.mmdl_sensor_setting_set(sensor_id, setting_id, setting_raw, ack)
    return True


def sensor_setting_set_ack(params):
    return sensor_setting_set(params, True)


def sensor_setting_set_unack(params):
    return sensor_setting_set(params, False)


def sensor_setting_status(_):
    return True


def sensor_column_get(_):
    sensor_id = 0x0042
    raw_value = '10'
    btp.mmdl_sensor_column_get(sensor_id, raw_value)
    return True


def sensor_column_status(params):
    sensor_id = params['PropertyId']
    column_data = 0
    if 'ColumnData' in params:
        column_data = params['ColumnData']

    stack = get_stack()
    status = stack.mesh.recv_status_data_get('Status')
    return [sensor_id, column_data] == status


def sensor_series_get(params):
    sensor_id = params['PropertyId']
    if params['RawValueA1'] is None:
        raw_value_x1 = '10'
    else:
        raw_value_x1 = hex(params['RawValueA1'])[2:]

    if params['RawValueA2'] is None:
        raw_value_x2 = '20'
    else:
        raw_value_x2 = hex(params['RawValueA2'])[2:]

    btp.mmdl_sensor_series_get(sensor_id, raw_value_x1 + raw_value_x2)
    return True


def sensor_series_status(params):
    sensor_id = params['PropertyId']
    column_data = params['ColumnData']

    stack = get_stack()
    status = stack.mesh.recv_status_data_get('Status')
    return [sensor_id, column_data] == status


ZONE_CHANGE_ZERO_POINT = 0x40
UTC_CHANGE_ZERO_POINT = 0x00FF


def time_get(_):
    btp.mmdl_time_get()
    return True


def time_set(params):
    tai = params['TAI Seconds']
    subsecond = params['Subsecond']
    uncertainty = params['Uncertainty']
    auth = params['Time Authority']
    tai_utc_delta = auth | ((params['TAI-UTC Delta']) << 1)
    time_zone_offset = params['Time Zone Offset']
    btp.mmdl_time_set(tai, subsecond, uncertainty,
                      tai_utc_delta, time_zone_offset)

    stack = get_stack()
    stack.mesh.expect_status_data_set(
        'Status', [tai, subsecond, uncertainty, tai_utc_delta, time_zone_offset])
    return True


def time_status(params):
    tai = params['TAI Seconds']
    subsecond = params['Subsecond']
    uncertainty = params['Uncertainty']
    auth = params['Time Authority']
    tai_utc_delta = auth | ((params['TAI-UTC Delta']) << 1)
    time_zone_offset = params['Time Zone Offset']
    stack = get_stack()
    return [tai, subsecond, uncertainty, tai_utc_delta, time_zone_offset] == stack.mesh.recv_status_data_get('Status')


def time_role_get(_):
    btp.mmdl_time_role_get()
    return True


def time_role_set(params):
    role = params['Time Role']
    btp.mmdl_time_role_set(role)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [role])
    return True


def time_role_status(params):
    role = params['Time Role']
    stack = get_stack()
    return [role] == stack.mesh.recv_status_data_get('Status')


def time_zone_get(_):
    btp.mmdl_time_zone_get()
    return True


def time_zone_set(params):
    new_offset = params['Time Zone Offset New'] - ZONE_CHANGE_ZERO_POINT
    timestamp = params['TAI of Zone Change']
    btp.mmdl_time_zone_set(new_offset, timestamp)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [new_offset, timestamp])
    return True


def time_zone_status(params):
    current_offset = params['Time Zone Offset Current'] - \
        ZONE_CHANGE_ZERO_POINT
    new_offset = params['Time Zone Offset New'] - ZONE_CHANGE_ZERO_POINT
    timestamp = params['TAI of Zone Change']
    stack = get_stack()
    return [current_offset, new_offset, timestamp] == stack.mesh.recv_status_data_get('Status')


def time_tai_utc_delta_get(_):
    btp.mmdl_time_tai_utc_delta_get()
    return True


def time_tai_utc_delta_set(params):
    delta_new = params['TAI-UTC Delta New'] - UTC_CHANGE_ZERO_POINT
    timestamp = params['TAI of Delta Change']
    btp.mmdl_time_tai_utc_delta_set(delta_new, timestamp)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Status', [delta_new, timestamp])
    return True


def time_tai_utc_delta_status(params):
    delta_current = params['TAI-UTC Delta Current'] - UTC_CHANGE_ZERO_POINT
    delta_new = params['TAI-UTC Delta New'] - UTC_CHANGE_ZERO_POINT
    timestamp = params['TAI of Delta Change']

    stack = get_stack()
    return [delta_current, delta_new, timestamp] == stack.mesh.recv_status_data_get('Status')


def light_lightness_get(_):
    btp.mmdl_light_lightness_get()
    return True


def light_lightness_set(params, ack):
    power_level = params['Lightness']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_light_lightness_set(power_level, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [power_level])
    return True


def light_lightness_set_ack(params):
    return light_lightness_set(params, True)


def light_lightness_set_unack(params):
    return light_lightness_set(params, False)


def light_lightness_status(params):
    power_level = params['Present Lightness']
    stack = get_stack()
    return [power_level] == stack.mesh.recv_status_data_get('Status')


def light_lightness_linear_get(_):
    btp.mmdl_light_lightness_linear_get()
    return True


def light_lightness_linear_set(params, ack):
    power_level = params['Lightness']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_light_lightness_linear_set(power_level, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [power_level])
    return True


def light_lightness_linear_set_ack(params):
    return light_lightness_linear_set(params, True)


def light_lightness_linear_set_unack(params):
    return light_lightness_linear_set(params, False)


def light_lightness_linear_status(params):
    power_level = params['Present Lightness']
    stack = get_stack()
    return [power_level] == stack.mesh.recv_status_data_get('Status')


def light_lightness_last_get(_):
    btp.mmdl_light_lightness_last_get()
    return True


def light_lightness_last_status(params):
    power_level = params['Lightness']
    stack = get_stack()
    return [power_level] == stack.mesh.recv_status_data_get('Status')


def light_lightness_default_get(_):
    btp.mmdl_light_lightness_default_get()
    return True


def light_lightness_default_set(params, ack):
    dflt = params['Lightness']
    btp.mmdl_light_lightness_default_set(dflt, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [dflt])
    return True


def light_lightness_default_set_ack(params):
    return light_lightness_default_set(params, True)


def light_lightness_default_set_unack(params):
    return light_lightness_default_set(params, False)


def light_lightness_default_status(params):
    power_level = params['Lightness']
    stack = get_stack()
    return [power_level] == stack.mesh.recv_status_data_get('Status')


def light_lightness_range_get(_):
    btp.mmdl_light_lightness_range_get()
    return True


def light_lightness_range_set(params, ack):
    min_val = params['Range Min']
    max_val = params['Range Max']
    btp.mmdl_light_lightness_range_set(min_val, max_val, ack=ack)

    expect_status_code = 0
    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set(
        'Status', [expect_status_code, min_val, max_val])
    return True


def light_lightness_range_set_ack(params):
    return light_lightness_range_set(params, True)


def light_lightness_range_set_unack(params):
    return light_lightness_range_set(params, False)


def light_lightness_range_status(params):
    min_val = params['Range Min']
    max_val = params['Range Max']
    status = params['Status Code']
    stack = get_stack()
    return [status, min_val, max_val] == stack.mesh.recv_status_data_get('Status')


def light_lc_mode_get(_):
    btp.mmdl_light_lc_mode_get()
    return True


def light_lc_mode_set(params, ack):
    mode = params['Mode']
    btp.mmdl_light_lc_mode_set(mode, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [mode])
    return True


def light_lc_mode_set_ack(params):
    return light_lc_mode_set(params, True)


def light_lc_mode_set_unack(params):
    return light_lc_mode_set(params, False)


def light_lc_mode_status(params):
    mode = params['Mode']
    stack = get_stack()
    return [mode] == stack.mesh.recv_status_data_get('Status')


def light_lc_occupancy_mode_get(_):
    btp.mmdl_light_lc_occupancy_mode_get()
    return True


def light_lc_occupancy_mode_set(params, ack):
    occupancy_mode = params['Occupancy Mode']
    btp.mmdl_light_lc_occupancy_mode_set(occupancy_mode, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [occupancy_mode])
    return True


def light_lc_occupancy_mode_set_ack(params):
    return light_lc_occupancy_mode_set(params, True)


def light_lc_occupancy_mode_set_unack(params):
    return light_lc_occupancy_mode_set(params, False)


def light_lc_occupancy_mode_status(params):
    occupancy_mode = params['Occupancy Mode']
    stack = get_stack()
    return [occupancy_mode] == stack.mesh.recv_status_data_get('Status')


def light_lc_light_onoff_mode_get(_):
    btp.mmdl_light_lc_light_onoff_mode_get()
    return True


def light_lc_light_onoff_mode_set(params, ack):
    light_onoff_mode = params['Light OnOff']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_light_lc_light_onoff_mode_set(
        light_onoff_mode, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [light_onoff_mode])
    return True


def light_lc_light_onoff_mode_set_ack(params):
    return light_lc_light_onoff_mode_set(params, True)


def light_lc_light_onoff_mode_set_unack(params):
    return light_lc_light_onoff_mode_set(params, False)


def light_lc_light_onoff_mode_status(params):
    light_onoff_mode = params['Present Light OnOff']
    stack = get_stack()
    return [light_onoff_mode] == stack.mesh.recv_status_data_get('Status')


def light_lc_property_get(params):
    prop_id = params['Light LC Property ID']
    btp.mmdl_light_lc_property_get(prop_id)
    return True


def light_lc_property_set(params, ack):
    prop_id = params['Light LC Property ID']
    prop_val = params['Light LC Property Value']
    btp.mmdl_light_lc_property_set(prop_id, prop_val, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [prop_id, prop_val])
    return True


def light_lc_property_set_ack(params):
    return light_lc_property_set(params, True)


def light_lc_property_set_unack(params):
    return light_lc_property_set(params, False)


def light_lc_property_status(params):
    prop_val = params['Light LC Property Value']
    prop_id = params['Light LC Property ID']
    stack = get_stack()
    return [prop_id, prop_val] == stack.mesh.recv_status_data_get('Status')


def light_ctl_states_get(_):
    btp.mmdl_light_ctl_states_get()
    return True


def light_ctl_states_set(params, ack):
    ctl_lightness = params['CTL Lightness']
    ctl_temperature = params['CTL Temperature']
    ctl_delta_uv = params['CTL Delta UV']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)

    btp.mmdl_light_ctl_states_set(
        ctl_lightness, ctl_temperature, ctl_delta_uv, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set(
        'Status', [ctl_lightness, ctl_temperature])
    return True


def light_ctl_states_set_ack(params):
    return light_ctl_states_set(params, True)


def light_ctl_states_set_unack(params):
    return light_ctl_states_set(params, False)


def light_ctl_states_status(params):
    current_light = params['Present CTL Lightness']
    current_temp = params['Present CTL Temperature']
    stack = get_stack()

    return [current_light, current_temp] == stack.mesh.recv_status_data_get('Status')


def light_ctl_temperature_get(_):
    btp.mmdl_light_ctl_temperature_get()
    return True


def light_ctl_temperature_set(params, ack):
    ctl_temperature = params['CTL Temperature']
    ctl_delta_uv = params['CTL Delta UV']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)

    btp.mmdl_light_ctl_temperature_set(
        ctl_temperature, ctl_delta_uv, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set(
        'Status', [ctl_temperature, ctl_delta_uv])
    return True


def light_ctl_temperature_set_ack(params):
    return light_ctl_temperature_set(params, True)


def light_ctl_temperature_set_unack(params):
    return light_ctl_temperature_set(params, False)


def light_ctl_temperature_status(params):
    current_temp = params['Present CTL Temperature']
    current_delta = params['Present CTL Delta UV']
    stack = get_stack()

    return [current_temp, current_delta] == stack.mesh.recv_status_data_get('Status')


def light_ctl_default_get(_):
    btp.mmdl_light_ctl_default_get()
    return True


def light_ctl_default_set(params, ack):
    ctl_lightness = params['CTL Lightness']
    ctl_temperature = params['CTL Temperature']
    ctl_delta_uv = params['CTL Delta UV']

    btp.mmdl_light_ctl_default_set(
        ctl_lightness, ctl_temperature, ctl_delta_uv, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set(
        'Status', [ctl_lightness, ctl_temperature, ctl_delta_uv])
    return True


def light_ctl_default_set_ack(params):
    return light_ctl_default_set(params, True)


def light_ctl_default_set_unack(params):
    return light_ctl_default_set(params, False)


def light_ctl_default_status(params):
    ctl_lightness = params['CTL Lightness']
    ctl_temp = params['CTL Temperature']
    ctl_delta = params['CTL Delta UV']
    stack = get_stack()

    return [ctl_lightness, ctl_temp, ctl_delta] == stack.mesh.recv_status_data_get('Status')


def light_ctl_temp_range_get(_):
    btp.mmdl_light_ctl_temp_range_get()
    return True


def light_ctl_temp_range_set(params, ack):
    range_min = params['Range Min']
    range_max = params['Range Max']

    btp.mmdl_light_ctl_temp_range_set(range_min, range_max, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [range_min, range_max])
    return True


def light_ctl_temp_range_set_ack(params):
    return light_ctl_temp_range_set(params, True)


def light_ctl_temp_range_set_unack(params):
    return light_ctl_temp_range_set(params, False)


def light_ctl_temp_range_status(params):
    range_min = params['Range Min']
    range_max = params['Range Max']
    status = params['Status Code']
    stack = get_stack()

    return [status, range_min, range_max] == stack.mesh.recv_status_data_get('Status')


def scene_get(_):
    btp.mmdl_scene_get()
    return True


def scene_status(params):
    expect_status_code = params['Status Code']
    scene = params['Current Scene']

    stack = get_stack()
    return [expect_status_code, scene] == stack.mesh.recv_status_data_get('Status')


def scene_register_get(_):
    btp.mmdl_scene_register_get()
    return True


def scene_register_status(params):
    expect_status_code = params['Status Code']
    scene = params['Current Scene']

    stack = get_stack()
    return [expect_status_code, scene] == stack.mesh.recv_status_data_get('Status')


def scene_store_procedure(params, ack):
    scene_num = params['Scene Number']
    btp.mmdl_scene_store_procedure(scene_num, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [scene_num])
    return True


def scene_store_procedure_ack(params):
    return scene_store_procedure(params, True)


def scene_store_procedure_unack(params):
    return scene_store_procedure(params, False)


def scene_recall(params, ack):
    scene_num = params['Scene Number']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_scene_recall(scene_num, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [scene_num])
    return True


def scene_recall_ack(params):
    return scene_recall(params, True)


def scene_recall_unack(params):
    return scene_recall(params, False)


def light_xyl_get(_):
    btp.mmdl_light_xyl_get()
    return True


def light_xyl_set(params, ack):
    lightness = params['xyL Lightness']
    x_value = params['xyL x']
    y_value = params['xyL y']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_light_xyl_set(lightness, x_value, y_value, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [lightness, x_value, y_value])

    remaining_time = stack.mesh.recv_status_data_get('Remaining Time')
    if remaining_time:
        stack.mesh.expect_status_data_set(
            'Status', stack.mesh.recv_status_data_get('Status'))
        stack.mesh.expect_status_data_set(
            'Remaining Time', remaining_time)
    return True


def light_xyl_set_ack(params):
    return light_xyl_set(params, True)


def light_xyl_set_unack(params):
    return light_xyl_set(params, False)


def light_xyl_status(params):
    lightness = params['xyL Lightness']
    x_value = params['xyL x']
    y_value = params['xyL y']

    stack = get_stack()
    return [lightness, x_value, y_value] == stack.mesh.recv_status_data_get('Status')


def light_xyl_target_get(_):
    btp.mmdl_light_xyl_target_get()
    return True


def light_xyl_target_status(params):
    lightness = params['Target xyL Lightness']
    x_value = params['Target xyL x']
    y_value = params['Target xyL y']

    stack = get_stack()
    return [lightness, x_value, y_value] == stack.mesh.recv_status_data_get('Status')


def light_xyl_default_get(_):
    btp.mmdl_light_xyl_default_get()
    return True


def light_xyl_default_set(params, ack):
    lightness = params['Lightness']
    x_value = params['xyL x']
    y_value = params['xyL y']

    btp.mmdl_light_xyl_default_set(lightness, x_value, y_value, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [lightness, x_value, y_value])
    return True


def light_xyl_default_set_ack(params):
    return light_xyl_default_set(params, True)


def light_xyl_default_set_unack(params):
    return light_xyl_default_set(params, False)


def light_xyl_default_status(params):
    lightness = params['Lightness']
    x_value = params['xyL x']
    y_value = params['xyL y']

    stack = get_stack()
    return [lightness, x_value, y_value] == stack.mesh.recv_status_data_get('Status')


def light_xyl_range_get(_):
    btp.mmdl_light_xyl_range_get()
    return True


def light_xyl_range_set(params, ack):
    min_x = params['xyL x Range Min']
    min_y = params['xyL y Range Min']
    max_x = params['xyL x Range Max']
    max_y = params['xyL y Range Max']

    btp.mmdl_light_xyl_range_set(min_x, min_y, max_x, max_y, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [min_x, min_y, max_x, max_y])
    return True


def light_xyl_range_set_ack(params):
    return light_xyl_range_set(params, True)


def light_xyl_range_set_unack(params):
    return light_xyl_range_set(params, False)


def light_xyl_range_status(params):
    expect_status_code = params['Status Code']
    min_x = params['xyL x Range Min']
    min_y = params['xyL y Range Min']
    max_x = params['xyL x Range Max']
    max_y = params['xyL y Range Max']

    stack = get_stack()
    return [expect_status_code, min_x, min_y, max_x, max_y] == stack.mesh.recv_status_data_get('Status')


def light_hsl_get(_):
    btp.mmdl_light_hsl_get()
    return True


def light_hsl_set(params, ack):
    lightness = params['HSL Lightness']
    hue = params['HSL Hue']
    saturation = params['HSL Saturation']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_light_hsl_set(lightness, hue, saturation, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [lightness, hue, saturation])

    remaining_time = stack.mesh.recv_status_data_get('Remaining Time')
    if remaining_time:
        stack.mesh.expect_status_data_set(
            'Status', stack.mesh.recv_status_data_get('Status'))
        stack.mesh.expect_status_data_set(
            'Remaining Time', remaining_time)
    return True


def light_hsl_set_ack(params):
    return light_hsl_set(params, True)


def light_hsl_set_unack(params):
    return light_hsl_set(params, False)


def light_hsl_status(params):
    lightness = params['HSL Lightness']
    hue = params['HSL Hue']
    saturation = params['HSL Saturation']

    stack = get_stack()
    return [lightness, hue, saturation] == stack.mesh.recv_status_data_get('Status')


def light_hsl_target_get(_):
    btp.mmdl_light_hsl_target_get()
    return True


def light_hsl_target_status(params):
    lightness = params['HSL Lightness']
    hue = params['HSL Hue']
    saturation = params['HSL Saturation']

    stack = get_stack()
    return [lightness, hue, saturation] == stack.mesh.recv_status_data_get('Status')


def light_hsl_default_get(_):
    btp.mmdl_light_hsl_default_get()
    return True


def light_hsl_default_set(params, ack):
    lightness = params['HSL Lightness']
    hue = params['HSL Hue']
    saturation = params['HSL Saturation']
    btp.mmdl_light_hsl_default_set(lightness, hue, saturation, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [lightness, hue, saturation])
    return True


def light_hsl_default_set_ack(params):
    return light_hsl_default_set(params, True)


def light_hsl_default_set_unack(params):
    return light_hsl_default_set(params, False)


def light_hsl_default_status(params):
    lightness = params['HSL Lightness']
    hue = params['HSL Hue']
    saturation = params['HSL Saturation']

    stack = get_stack()
    return [lightness, hue, saturation] == stack.mesh.recv_status_data_get('Status')


def light_hsl_range_get(_):
    btp.mmdl_light_hsl_range_get()
    return True


def light_hsl_range_set(params, ack):
    hue_min = params['Hue Range Min']
    saturation_min = params['Saturation Range Min']
    hue_max = params['Hue Range Max']
    saturation_max = params['Saturation Range Max']
    btp.mmdl_light_hsl_range_set(hue_min, saturation_min, hue_max, saturation_max, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [hue_min, saturation_min, hue_max, saturation_max])
    return True


def light_hsl_range_set_ack(params):
    return light_hsl_range_set(params, True)


def light_hsl_range_set_unack(params):
    return light_hsl_range_set(params, False)


def light_hsl_range_status(params):
    status_code = params['Status Code']
    hue_min = params['Hue Range Min']
    saturation_min = params['Saturation Range Min']
    hue_max = params['Hue Range Max']
    saturation_max = params['Saturation Range Max']

    stack = get_stack()
    return [status_code, hue_min, saturation_min, hue_max, saturation_max] == stack.mesh.recv_status_data_get('Status')


def light_hsl_hue_get(_):
    btp.mmdl_light_hsl_hue_get()
    return True


def light_hsl_hue_set(params, ack):
    hue = params['HSL Hue']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_light_hsl_hue_set(hue, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [hue])
    return True


def light_hsl_hue_set_ack(params):
    return light_hsl_hue_set(params, True)


def light_hsl_hue_set_unack(params):
    return light_hsl_hue_set(params, False)


def light_hsl_saturation_get(_):
    btp.mmdl_light_hsl_saturation_get()
    return True


def light_hsl_hue_status(params):
    hue = params['Present Hue']

    stack = get_stack()
    return [hue] == stack.mesh.recv_status_data_get('Status')


def light_hsl_saturation_set(params, ack):
    saturation = params['HSL Saturation']
    tt = params.get('Transition Time', None)
    delay = params.get('Delay', None)
    btp.mmdl_light_hsl_saturation_set(saturation, tt, delay, ack=ack)

    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [saturation])
    return True


def light_hsl_saturation_set_ack(params):
    return light_hsl_saturation_set(params, True)


def light_hsl_saturation_set_unack(params):
    return light_hsl_saturation_set(params, False)


def light_hsl_saturation_status(params):
    saturation = params['Present Saturation']

    stack = get_stack()
    return [saturation] == stack.mesh.recv_status_data_get('Status')


def scheduler_get(_):
    btp.mmdl_scheduler_get()
    return True


def scheduler_action_get(params):
    index = params['Index']

    btp.mmdl_scheduler_action_get(index)
    return True


def scheduler_action_set(params, ack):
    index = params['Index4']
    year = params['Year']
    month = params['Month']
    day = params['Day']
    hour = params['Hour']
    minute = params['Minute']
    second = params['Second']
    day_of_week = params['DayOfWeek']
    action = params['Action']
    scene_num = params['Scene Number']
    transition_time = params['Transition Time']

    btp.mmdl_scheduler_action_set(index, year, month, day, hour, minute, second, day_of_week, action,
                                  transition_time, scene_num, ack=ack)
    stack = get_stack()
    stack.mesh.expect_status_data_set('Ack', ack)
    stack.mesh.expect_status_data_set('Status', [index, year, month, day, hour, minute, second, day_of_week, action,
                                                 transition_time, scene_num])
    return True


def scheduler_action_set_ack(params):
    return scheduler_action_set(params, True)


def scheduler_action_set_unack(params):
    return scheduler_action_set(params, False)


def scheduler_status(params):
    schedules = params['Schedules']

    stack = get_stack()
    return [schedules] == stack.mesh.recv_status_data_get('Status')


def scheduler_action_status(params):
    year = params['Year']
    month = params['Month']
    day = params['Day']
    hour = params['Hour']
    minute = params['Minute']
    second = params['Second']
    day_of_week = params['DayOfWeek']
    action = params['Action']
    scene_num = params['Scene Number']
    transition_time = params['Transition Time']

    stack = get_stack()
    return [year, month, day, hour, minute, second, day_of_week, action, transition_time,
            scene_num] == stack.mesh.recv_status_data_get('Status')


def parse_send(params):
    opcode = params['Op Code']
    cmds = {
        0x8201: gen_onoff_get,
        0x8202: gen_onoff_set_ack,
        0x8203: gen_onoff_set_unack,
        0x8204: gen_onoff_status,
        0x8205: gen_lvl_get,
        0x8206: gen_lvl_set_ack,
        0x8207: gen_lvl_set_unack,
        0x8208: gen_lvl_status,
        0x8209: gen_lvl_set_delta_ack,
        0x820a: gen_lvl_set_delta_unack,
        0x820b: gen_lvl_set_move_ack,
        0x820c: gen_lvl_set_move_unack,
        0x820d: gen_dtt_get,
        0x820e: gen_dtt_set_ack,
        0x820f: gen_dtt_set_unack,
        0x8210: gen_dtt_status,
        0x8211: gen_ponoff_get,
        0x8213: gen_ponoff_set_ack,
        0x8214: gen_ponoff_set_unack,
        0x8212: gen_ponoff_status,
        0x8215: gen_plvl_get,
        0x8216: gen_plvl_set_ack,
        0x8217: gen_plvl_set_unack,
        0x8218: gen_plvl_status,
        0x8219: gen_plvl_last_get,
        0x821a: gen_plvl_last_status,
        0x821b: gen_plvl_dflt_get,
        0x821c: gen_plvl_dflt_status,
        0x821d: gen_plvl_range_get,
        0x821e: gen_plvl_range_status,
        0x821f: gen_plvl_dflt_set_ack,
        0x8220: gen_plvl_dflt_set_unack,
        0x8221: gen_plvl_range_set_ack,
        0x8222: gen_plvl_range_set_unack,
        0x8223: gen_battery_get,
        0x8224: gen_battery_status,
        0x8225: gen_loc_global_get,
        0x40: gen_loc_global_status,
        0x8226: gen_loc_local_get,
        0x8227: gen_loc_local_status,
        0x41: gen_loc_global_set_ack,
        0x42: gen_loc_global_set_unack,
        0x8228: gen_loc_local_set_ack,
        0x8229: gen_loc_local_set_unack,
        0x822a: gen_mfr_props_get,
        0x43: gen_mfr_props_status,
        0x822b: gen_mfr_prop_get,
        0x44: gen_mfr_prop_set_ack,
        0x45: gen_mfr_prop_set_unack,
        0x46: gen_mfr_prop_status,
        0x822c: gen_admin_props_get,
        0x47: gen_admin_props_status,
        0x822d: gen_admin_prop_get,
        0x48: gen_admin_prop_set_ack,
        0x49: gen_admin_prop_set_unack,
        0x4a: gen_admin_prop_status,
        0x822e: gen_usr_props_get,
        0x4b: gen_usr_props_status,
        0x822f: gen_usr_prop_get,
        0x4c: gen_usr_prop_set_ack,
        0x4d: gen_usr_prop_set_unack,
        0x4e: gen_usr_prop_status,
        0x4f: gen_cli_props_get,
        0x50: gen_cli_props_status,
        0x8230: sensor_desc_get,
        0x51: sensor_desc_status,
        0x8231: sensor_get,
        0x52: sensor_status,
        0x8232: sensor_column_get,
        0x53: sensor_column_status,
        0x8233: sensor_series_get,
        0x54: sensor_series_status,
        0x8234: sensor_cadence_get,
        0x55: sensor_cadence_set_ack,
        0x56: sensor_cadence_set_unack,
        0x57: sensor_cadence_status,
        0x8235: sensor_settings_get,
        0x58: sensor_settings_status,
        0x8236: sensor_setting_get,
        0x59: sensor_setting_set_ack,
        0x5a: sensor_setting_set_unack,
        0x5b: sensor_setting_status,
        0x8237: time_get,
        0x5c: time_set,
        0x5d: time_status,
        0x8238: time_role_get,
        0x8239: time_role_set,
        0x823a: time_role_status,
        0x823b: time_zone_get,
        0x823c: time_zone_set,
        0x823d: time_zone_status,
        0x823e: time_tai_utc_delta_get,
        0x823f: time_tai_utc_delta_set,
        0x8240: time_tai_utc_delta_status,
        0x824b: light_lightness_get,
        0x824c: light_lightness_set_ack,
        0x824d: light_lightness_set_unack,
        0x824e: light_lightness_status,
        0x824f: light_lightness_linear_get,
        0x8250: light_lightness_linear_set_ack,
        0x8251: light_lightness_linear_set_unack,
        0x8252: light_lightness_linear_status,
        0x8253: light_lightness_last_get,
        0x8254: light_lightness_last_status,
        0x8255: light_lightness_default_get,
        0x8256: light_lightness_default_status,
        0x8257: light_lightness_range_get,
        0x8258: light_lightness_range_status,
        0x8259: light_lightness_default_set_ack,
        0x825a: light_lightness_default_set_unack,
        0x825b: light_lightness_range_set_ack,
        0x825c: light_lightness_range_set_unack,
        0x8291: light_lc_mode_get,
        0x8292: light_lc_mode_set_ack,
        0x8293: light_lc_mode_set_unack,
        0x8294: light_lc_mode_status,
        0x8295: light_lc_occupancy_mode_get,
        0x8296: light_lc_occupancy_mode_set_ack,
        0x8297: light_lc_occupancy_mode_set_unack,
        0x8298: light_lc_occupancy_mode_status,
        0x8299: light_lc_light_onoff_mode_get,
        0x829a: light_lc_light_onoff_mode_set_ack,
        0x829b: light_lc_light_onoff_mode_set_unack,
        0x829c: light_lc_light_onoff_mode_status,
        0x829d: light_lc_property_get,
        0x62: light_lc_property_set_ack,
        0x63: light_lc_property_set_unack,
        0x64: light_lc_property_status,
        0x825D: light_ctl_states_get,
        0x825E: light_ctl_states_set_ack,
        0x825F: light_ctl_states_set_unack,
        0x8260: light_ctl_states_status,
        0x8261: light_ctl_temperature_get,
        0x8262: light_ctl_temp_range_get,
        0x8263: light_ctl_temp_range_status,
        0x8264: light_ctl_temperature_set_ack,
        0x8265: light_ctl_temperature_set_unack,
        0x8266: light_ctl_temperature_status,
        0x8267: light_ctl_default_get,
        0x8268: light_ctl_default_status,
        0x8269: light_ctl_default_set_ack,
        0x826a: light_ctl_default_set_unack,
        0x826b: light_ctl_temp_range_set_ack,
        0x826c: light_ctl_temp_range_set_unack,
        0x8241: scene_get,
        0x5e: scene_status,
        0x8244: scene_register_get,
        0x8245: scene_register_status,
        0x8246: scene_store_procedure_ack,
        0x8247: scene_store_procedure_unack,
        0x8242: scene_recall_ack,
        0x8243: scene_recall_unack,
        0x8283: light_xyl_get,
        0x8284: light_xyl_set_ack,
        0x8285: light_xyl_set_unack,
        0x8286: light_xyl_status,
        0x8287: light_xyl_target_get,
        0x8288: light_xyl_target_status,
        0x8289: light_xyl_default_get,
        0x828A: light_xyl_default_status,
        0x828D: light_xyl_default_set_ack,
        0x828E: light_xyl_default_set_unack,
        0x828B: light_xyl_range_get,
        0x828C: light_xyl_range_status,
        0x828F: light_xyl_range_set_ack,
        0x8290: light_xyl_range_set_unack,
        0x826D: light_hsl_get,
        0x8276: light_hsl_set_ack,
        0x8277: light_hsl_set_unack,
        0x8278: light_hsl_status,
        0x8279: light_hsl_target_get,
        0x827A: light_hsl_target_status,
        0x827B: light_hsl_default_get,
        0x827C: light_hsl_default_status,
        0x827F: light_hsl_default_set_ack,
        0x8280: light_hsl_default_set_unack,
        0x827D: light_hsl_range_get,
        0x8281: light_hsl_range_set_ack,
        0x8282: light_hsl_range_set_unack,
        0x827E: light_hsl_range_status,
        0x826E: light_hsl_hue_get,
        0x826F: light_hsl_hue_set_ack,
        0x8270: light_hsl_hue_set_unack,
        0x8271: light_hsl_hue_status,
        0x8272: light_hsl_saturation_get,
        0x8273: light_hsl_saturation_set_ack,
        0x8274: light_hsl_saturation_set_unack,
        0x8275: light_hsl_saturation_status,
        0x8248: scheduler_action_get,
        0x8249: scheduler_get,
        0x824A: scheduler_status,
        0x5F: scheduler_action_status,
        0x60: scheduler_action_set_ack,
        0x61: scheduler_action_set_unack,
    }

    if opcode not in cmds:
        return False

    return cmds[opcode](params)


def hdl_wid_660(params: WIDParams):
    command_params = parse_command_params(params.description)
    log("%r", command_params)
    if params.description.startswith('Please send') or params.description.startswith('Please confirm the received'):
        return parse_send(command_params)
    if params.description.startswith('Please confirm IUT has successfully set the new state.'):
        if command_params:
            parse_send(command_params)
            return True
        stack = get_stack()
        if stack.mesh.expect_status_data_get("Ack") is False:
            return True
        if stack.mesh.expect_status_data.data == stack.mesh.recv_status_data.data:
            return True
        return False
    return False


def hdl_wid_661(_: WIDParams):
    iut_reset()
    return True


def hdl_wid_663(_: WIDParams):
    iut_reset()
    return True


def hdl_wid_664(params: WIDParams):
    """
    Please set the IUT's property 0x0069 outside the range (4008, BFF8).

    PTS will wait for Sensor Status messages being published at a new 8-second interval.
    """
    prop_id = re.findall(r'0x([0-9A-F]{2,})', params.description)[0]
    range_values = re.findall(r'\(([0-9A-F]{2,}), ([0-9A-F]{2,})\)', params.description)[0]
    sensor_val = int(range_values[0], 16) - 1
    btp.mmdl_sensor_data_set(int(prop_id, 16), struct.pack("<I", sensor_val))
    return True


def hdl_wid_665(params: WIDParams):
    """
    Please set the IUT's property 0x0069 inside the range (4008, BFF8).

    PTS will wait for Sensor Status messages being published at a new 2-second interval.
    """
    prop_id = re.findall(r'0x([0-9A-F]{2,})', params.description)[0]
    range_values = re.findall(r'\(([0-9A-F]{2,}), ([0-9A-F]{2,})\)', params.description)[0]
    sensor_val = int(range_values[0], 16) + 1
    btp.mmdl_sensor_data_set(int(prop_id, 16), struct.pack("<I", sensor_val))
    return True


global sensor_value


def hdl_wid_666(params: WIDParams):
    """
    Please set the property 0x0069 at a convenient value that allows for future increments/decrements.
    """
    global sensor_value
    # Wait a few seconds before publishing a new state to satisfy a
    # requirement for Min Interval between published messages.
    time.sleep(5)

    prop_id = int(re.findall(r'0x([0-9A-F]{2,})', params.description)[0], 16)
    sensor_value = int(0xffff / 2)
    btp.mmdl_sensor_data_set(prop_id, struct.pack("<I", sensor_value))
    return True


def hdl_wid_667(params: WIDParams):
    """
    Please increase the value of the property 0x0069 with a quantity smaller than 332C.

    PTS expects the IUT not to publish any message.

    Please increase the value of the property 0x0069 with a quantity smaller than 20 percent.

    PTS expects the IUT not to publish any message.
    """
    global sensor_value
    # Wait a few seconds before publishing a new state to satisfy a
    # requirement for Min Interval between published messages.
    time.sleep(5)

    prop_id = int(re.findall(r'0x([0-9A-F]{2,})', params.description)[0], 16)
    if 'percent' in params.description:
        percent = int(re.findall(r'(\d+) percent.', params.description)[0])
        sensor_value = int(sensor_value * ((100.0 + (percent - 1)) / 100.0))
    else:
        quantity = int(re.findall(r'([0-9A-F]{2,})\.', params.description)[0], 16)
        sensor_value += (quantity - 1)
    btp.mmdl_sensor_data_set(prop_id, struct.pack("<I", sensor_value))
    return True


def hdl_wid_668(params: WIDParams):
    """
    Please increase the value of the property 0x0069 with a quantity larger than 332C.

    PTS expects the IUT to publish the new state.

    Please increase the value of the property 0x0069 with a quantity larger than 20 percent.

    PTS expects the IUT to publish the new state.
    """
    global sensor_value
    # Wait a few seconds before publishing a new state to satisfy a
    # requirement for Min Interval between published messages.
    time.sleep(5)

    prop_id = int(re.findall(r'0x([0-9A-F]{2,})', params.description)[0], 16)
    if 'percent' in params.description:
        percent = int(re.findall(r'(\d+) percent.', params.description)[0])
        sensor_value = int(sensor_value * ((100.0 + (percent + 1)) / 100.0))
    else:
        quantity = int(re.findall(r'([0-9A-F]{2,})\.', params.description)[0], 16)
        sensor_value += (quantity + 1)

    btp.mmdl_sensor_data_set(prop_id, struct.pack("<I", sensor_value))
    return True


def hdl_wid_669(params: WIDParams):
    """
    Please decrease the value of the property 0x0069 with a quantity smaller than 332C.

    PTS expects the IUT not to publish any message.

    Please decrease the value of the property 0x0069 with a quantity smaller than 20 percent.

    PTS expects the IUT not to publish any message.
    """
    global sensor_value
    # Wait a few seconds before publishing a new state to satisfy a
    # requirement for Min Interval between published messages.
    time.sleep(5)

    prop_id = int(re.findall(r'0x([0-9A-F]{2,})', params.description)[0], 16)
    if 'percent' in params.description:
        percent = int(re.findall(r'(\d+) percent.', params.description)[0])
        sensor_value = int(sensor_value * ((100.0 - (percent - 1)) / 100.0))
    else:
        quantity = int(re.findall(r'([0-9A-F]{2,})\.', params.description)[0], 16)
        sensor_value -= (quantity - 1)
    btp.mmdl_sensor_data_set(prop_id, struct.pack("<I", sensor_value))
    return True


def hdl_wid_670(params: WIDParams):
    """
    Please decrease the value of the property 0x0069 with a quantity larger than 332C.

    PTS expects the IUT to publish the new state.
    """
    global sensor_value
    # Wait a few seconds before publishing a new state to satisfy a
    # requirement for Min Interval between published messages.
    time.sleep(5)

    prop_id = int(re.findall(r'0x([0-9A-F]{2,})', params.description)[0], 16)
    if 'percent' in params.description:
        percent = int(re.findall(r'(\d+) percent.', params.description)[0])
        sensor_value = int(sensor_value * ((100.0 - (percent + 1)) / 100.0))
    else:
        quantity = int(re.findall(r'([0-9A-F]{2,})\.', params.description)[0], 16)
        sensor_value -= (quantity + 1)
    btp.mmdl_sensor_data_set(prop_id, struct.pack("<I", sensor_value))
    return True


def hdl_wid_671(_: WIDParams):
    return True


def hdl_wid_850(params: WIDParams):
    """
    Please initiate the transfer of the test object to the Lower Tester.
    """
    # Do not execute this wid, it's automatically send as part of FU procedure
    if params.test_case_name == 'DFUM/CL/FU/BV-02-C':
        return True

    stack = get_stack()
    timeout_base = stack.mesh.timeout_base_get()
    ttl = stack.mesh.transfer_ttl_get()
    addr = ["0001"]
    blob_id = 0x1100000000000011
    block_size = 6
    chunk_size = 8
    blob_data_size = 80

    btp.mmdl_blob_info_get(addr)

    time.sleep(5)

    btp.mmdl_blob_transfer_start(blob_id, block_size, chunk_size, timeout_base, ttl, blob_data_size)

    return True


def hdl_wid_851(_: WIDParams):
    """
    Please initiate the transfer of the test object to the Lower Tester.
    """
    stack = get_stack()
    timeout_base = stack.mesh.timeout_base_get()
    ttl = stack.mesh.transfer_ttl_get()
    addr = ["0001"]
    blob_id = 0x1100000000000011
    block_size = 6
    chunk_size = 65
    blob_data_size = 80

    btp.mmdl_blob_info_get(addr)

    time.sleep(5)

    btp.mmdl_blob_transfer_start(blob_id, block_size, chunk_size, timeout_base, ttl, blob_data_size)

    return True


def hdl_wid_852(params: WIDParams):
    """
    'Please confirm IUT has received 0x1000 bytes of data.'
    """
    stack = get_stack()

    to_rx = int(re.findall(r'0x([0-9A-F]{2,})', params.description)[0], 16)
    # Give some time so last mesh_model_recv_ev's are processed
    time.sleep(5)

    return stack.mesh.blob_rxed_bytes == to_rx


def hdl_wid_853(_: WIDParams):
    stack = get_stack()
    timeout_base = stack.mesh.timeout_base_get()
    ttl = stack.mesh.transfer_ttl_get()
    blob_id = 0x1100000000000011

    btp.mesh_store_model_data()
    btp.mmdl_blob_srv_recv(blob_id, timeout_base, ttl)

    return True


def hdl_wid_854(_: WIDParams):
    """
    Please wait for PTS to timeout. Lower Tester should not receive any messages regarding BLOB transfer.
    """
    return True


def hdl_wid_855(_: WIDParams):
    """
    Please query the state of BLOB transfer by sending Lower Tester BLOB_TRANSFER_GET message.
    """
    btp.mmdl_blob_info_get(["0001"])
    time.sleep(5)
    btp.mmdl_blob_transfer_get()
    return True


def hdl_wid_856(params: WIDParams):
    stack = get_stack()
    timeout_base = stack.mesh.timeout_base_get()
    ttl = stack.mesh.transfer_ttl_get()
    addrs = re.findall(r'(0x[0-9a-fA-F]{1,2})', params.description)
    addrs = [e[2:].rjust(4, '0') for e in addrs]
    blob_id = 0x1100000000000011
    block_size = 18
    chunk_size = 11
    blob_data_size = 80

    btp.mmdl_blob_info_get(addrs)
    time.sleep(5)
    btp.mmdl_blob_transfer_start(blob_id, block_size, chunk_size, timeout_base, ttl, blob_data_size)

    return True


def hdl_wid_857(_: WIDParams):
    """
    Please check BLOB data matched value in TSPX_Client_BLOB_Data.
    """
    return True


def hdl_wid_858(_: WIDParams):
    return True


def hdl_wid_859(_: WIDParams):
    """
    Please confirm that the IUT has reported BLOB transfer procedure failure.
    """
    stack = get_stack()
    return stack.mesh.wait_for_blob_target_lost(67)


def hdl_wid_860(_: WIDParams):
    btp.mmdl_blob_transfer_cancel()
    return True


def hdl_wid_861(_: WIDParams):
    """
    Please send BLOB_PARTIAL_BLOCK_REPORT after 31 seconds timeout. Repeat up to max retry count.
    """
    return True


def hdl_wid_970(_: WIDParams):
    """
   :param desc: Please updates firmware.Click Yes after update is complete and device is up and running.
   :return:
   """
    btp.mmdl_dfu_srv_apply()
    return True


def hdl_wid_977(_: WIDParams):
    limit = 0x01

    btp.mmdl_dfu_info_get(limit)
    return True


def hdl_wid_989(_: WIDParams):
    index = 0x00
    slot_size = 0x01
    slot_idx = 0x00

    fwid = "11000011"
    metadata = "1100000000000011"

    btp.mmdl_dfu_update_firmware_check(index, slot_idx, slot_size, fwid, metadata)
    return True


def hdl_wid_990(params: WIDParams):
    stack = get_stack()
    addrs = re.findall(r'(0x[0-9a-fA-F]{4})', params.description)
    addrs = [e[2:] for e in addrs]

    slot_idx = 0x00
    slot_size = 80
    block_size = 6
    chunk_size = 8

    fwid = "11000011"
    metadata = "1100000000000011"
    btp.mesh_store_model_data()

    btp.mmdl_dfu_update_firmware_start(addrs, slot_idx, slot_size, block_size, chunk_size, fwid, metadata)
    # wait for Firmware Update Status for every address
    for _e in addrs:
        stack.mesh.wait_for_model_added_op(5, b'b72b')

    return True


def hdl_wid_991(_: WIDParams):
    """
    Please send FIRMWARE_UPDATE_APPLY.
    """
    # Give some time so LT side can finish verifying image before calling apply
    # as IUT has to receive Firmware Update Status with
    # phase 0x04 Verification Succeeded first
    time.sleep(20)
    btp.mmdl_dfu_update_firmware_apply()
    return True


def hdl_wid_992(_: WIDParams):
    btp.mmdl_dfu_update_firmware_get()
    return True


def hdl_wid_993(_: WIDParams):
    btp.mmdl_dfu_update_firmware_cancel()
    return True
