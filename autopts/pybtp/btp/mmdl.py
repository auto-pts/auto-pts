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

"""Wrapper around btp messages. The functions are added as needed."""

import binascii
import logging
import struct

from autopts.ptsprojects.stack import get_stack
from autopts.pybtp import defs
from autopts.pybtp.btp.btp import CONTROLLER_INDEX, get_iut_method as get_iut

MMDL = {
    "read_supp_cmds": (defs.BTP_SERVICE_ID_MMDL,
                       defs.MMDL_READ_SUPPORTED_COMMANDS,
                       CONTROLLER_INDEX, ""),
    "gen_onoff_get": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_GEN_ONOFF_GET,
                      CONTROLLER_INDEX, ""),
    "gen_onoff_set": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_GEN_ONOFF_SET,
                      CONTROLLER_INDEX),
    "gen_lvl_get": (defs.BTP_SERVICE_ID_MMDL,
                    defs.MMDL_GEN_LVL_GET,
                    CONTROLLER_INDEX, ""),
    "gen_lvl_set": (defs.BTP_SERVICE_ID_MMDL,
                    defs.MMDL_GEN_LVL_SET,
                    CONTROLLER_INDEX),
    "gen_lvl_delta_set": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_GEN_LVL_DELTA_SET,
                          CONTROLLER_INDEX),
    "gen_lvl_move_set": (defs.BTP_SERVICE_ID_MMDL,
                         defs.MMDL_GEN_LVL_MOVE_SET,
                         CONTROLLER_INDEX),
    "gen_dtt_get": (defs.BTP_SERVICE_ID_MMDL,
                    defs.MMDL_GEN_DTT_GET,
                    CONTROLLER_INDEX, ""),
    "gen_dtt_set": (defs.BTP_SERVICE_ID_MMDL,
                    defs.MMDL_GEN_DTT_SET,
                    CONTROLLER_INDEX),
    "gen_ponoff_get": (defs.BTP_SERVICE_ID_MMDL,
                       defs.MMDL_GEN_PONOFF_GET,
                       CONTROLLER_INDEX, ""),
    "gen_ponoff_set": (defs.BTP_SERVICE_ID_MMDL,
                       defs.MMDL_GEN_PONOFF_SET,
                       CONTROLLER_INDEX),
    "gen_plvl_get": (defs.BTP_SERVICE_ID_MMDL,
                     defs.MMDL_GEN_PLVL_GET,
                     CONTROLLER_INDEX, ""),
    "gen_plvl_set": (defs.BTP_SERVICE_ID_MMDL,
                     defs.MMDL_GEN_PLVL_SET,
                     CONTROLLER_INDEX),
    "gen_plvl_last_get": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_GEN_PLVL_LAST_GET,
                          CONTROLLER_INDEX, ""),
    "gen_plvl_dflt_get": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_GEN_PLVL_DFLT_GET,
                          CONTROLLER_INDEX, ""),
    "gen_plvl_range_get": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_GEN_PLVL_RANGE_GET,
                           CONTROLLER_INDEX, ""),
    "gen_plvl_dflt_set": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_GEN_PLVL_DFLT_SET,
                          CONTROLLER_INDEX),
    "gen_plvl_range_set": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_GEN_PLVL_RANGE_SET,
                           CONTROLLER_INDEX),
    "gen_battery_get": (defs.BTP_SERVICE_ID_MMDL,
                        defs.MMDL_GEN_BATTERY_GET,
                        CONTROLLER_INDEX, ""),
    "gen_loc_global_get": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_GEN_LOC_GLOBAL_GET,
                           CONTROLLER_INDEX, ""),
    "gen_loc_local_get": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_GEN_LOC_LOCAL_GET,
                          CONTROLLER_INDEX, ""),
    "gen_loc_global_set": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_GEN_LOC_GLOBAL_SET,
                           CONTROLLER_INDEX),
    "gen_loc_local_set": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_GEN_LOC_LOCAL_SET,
                          CONTROLLER_INDEX),
    "gen_props_get": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_GEN_PROPS_GET,
                      CONTROLLER_INDEX),
    "gen_prop_get": (defs.BTP_SERVICE_ID_MMDL,
                     defs.MMDL_GEN_PROP_GET,
                     CONTROLLER_INDEX),
    "gen_prop_set": (defs.BTP_SERVICE_ID_MMDL,
                     defs.MMDL_GEN_PROP_SET,
                     CONTROLLER_INDEX),
    "sensor_desc_get": (defs.BTP_SERVICE_ID_MMDL,
                        defs.MMDL_SENSOR_DESC_GET,
                        CONTROLLER_INDEX),
    "sensor_get": (defs.BTP_SERVICE_ID_MMDL,
                   defs.MMDL_SENSOR_GET,
                   CONTROLLER_INDEX),
    "sensor_column_get": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_SENSOR_COLUMN_GET,
                          CONTROLLER_INDEX),
    "sensor_series_get": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_SENSOR_SERIES_GET,
                          CONTROLLER_INDEX),
    "sensor_cadence_get": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_SENSOR_CADENCE_GET,
                           CONTROLLER_INDEX),
    "sensor_cadence_set": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_SENSOR_CADENCE_SET,
                           CONTROLLER_INDEX),
    "sensor_settings_get": (defs.BTP_SERVICE_ID_MMDL,
                            defs.MMDL_SENSOR_SETTINGS_GET,
                            CONTROLLER_INDEX),
    "sensor_setting_get": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_SENSOR_SETTING_GET,
                           CONTROLLER_INDEX),
    "sensor_setting_set": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_SENSOR_SETTING_SET,
                           CONTROLLER_INDEX),
    "time_get": (defs.BTP_SERVICE_ID_MMDL,
                 defs.MMDL_TIME_GET,
                 CONTROLLER_INDEX, ""),
    "time_set": (defs.BTP_SERVICE_ID_MMDL,
                 defs.MMDL_TIME_SET,
                 CONTROLLER_INDEX),
    "time_role_get": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_TIME_ROLE_GET,
                      CONTROLLER_INDEX, ""),
    "time_role_set": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_TIME_ROLE_SET,
                      CONTROLLER_INDEX),
    "time_zone_get": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_TIME_ZONE_GET,
                      CONTROLLER_INDEX, ""),
    "time_zone_set": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_TIME_ZONE_SET,
                      CONTROLLER_INDEX),
    "time_tai_utc_delta_get": (defs.BTP_SERVICE_ID_MMDL,
                               defs.MMDL_TIME_TAI_UTC_DELTA_GET,
                               CONTROLLER_INDEX, ""),
    "time_tai_utc_delta_set": (defs.BTP_SERVICE_ID_MMDL,
                               defs.MMDL_TIME_TAI_UTC_DELTA_SET,
                               CONTROLLER_INDEX),
    "light_lightness_get": (defs.BTP_SERVICE_ID_MMDL,
                            defs.MMDL_LIGHT_LIGHTNESS_GET,
                            CONTROLLER_INDEX, ""),
    "light_lightness_set": (defs.BTP_SERVICE_ID_MMDL,
                            defs.MMDL_LIGHT_LIGHTNESS_SET,
                            CONTROLLER_INDEX),
    "light_lightness_linear_get": (defs.BTP_SERVICE_ID_MMDL,
                                   defs.MMDL_LIGHT_LIGHTNESS_LINEAR_GET,
                                   CONTROLLER_INDEX, ""),
    "light_lightness_linear_set": (defs.BTP_SERVICE_ID_MMDL,
                                   defs.MMDL_LIGHT_LIGHTNESS_LINEAR_SET,
                                   CONTROLLER_INDEX),
    "light_lightness_last_get": (defs.BTP_SERVICE_ID_MMDL,
                                 defs.MMDL_LIGHT_LIGHTNESS_LAST_GET,
                                 CONTROLLER_INDEX, ""),
    "light_lightness_default_get": (defs.BTP_SERVICE_ID_MMDL,
                                    defs.MMDL_LIGHT_LIGHTNESS_DEFAULT_GET,
                                    CONTROLLER_INDEX, ""),
    "light_lightness_default_set": (defs.BTP_SERVICE_ID_MMDL,
                                    defs.MMDL_LIGHT_LIGHTNESS_DEFAULT_SET,
                                    CONTROLLER_INDEX),
    "light_lightness_range_get": (defs.BTP_SERVICE_ID_MMDL,
                                  defs.MMDL_LIGHT_LIGHTNESS_RANGE_GET,
                                  CONTROLLER_INDEX, ""),
    "light_lightness_range_set": (defs.BTP_SERVICE_ID_MMDL,
                                  defs.MMDL_LIGHT_LIGHTNESS_RANGE_SET,
                                  CONTROLLER_INDEX),
    "light_lc_mode_get": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_LIGHT_LC_MODE_GET,
                          CONTROLLER_INDEX, ""),
    "light_lc_mode_set": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_LIGHT_LC_MODE_SET,
                          CONTROLLER_INDEX),
    "light_lc_occupancy_mode_get": (defs.BTP_SERVICE_ID_MMDL,
                                    defs.MMDL_LIGHT_LC_OCCUPANCY_MODE_GET,
                                    CONTROLLER_INDEX, ""),
    "light_lc_occupancy_mode_set": (defs.BTP_SERVICE_ID_MMDL,
                                    defs.MMDL_LIGHT_LC_OCCUPANCY_MODE_SET,
                                    CONTROLLER_INDEX),
    "light_lc_light_onoff_mode_get": (defs.BTP_SERVICE_ID_MMDL,
                                      defs.MMDL_LIGHT_LC_LIGHT_ONOFF_MODE_GET,
                                      CONTROLLER_INDEX, ""),
    "light_lc_light_onoff_mode_set": (defs.BTP_SERVICE_ID_MMDL,
                                      defs.MMDL_LIGHT_LC_LIGHT_ONOFF_MODE_SET,
                                      CONTROLLER_INDEX),
    "light_lc_property_get": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_LC_PROPERTY_GET,
                              CONTROLLER_INDEX),
    "light_lc_property_set": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_LC_PROPERTY_SET,
                              CONTROLLER_INDEX),
    "sensor_data_set": (defs.BTP_SERVICE_ID_MMDL,
                        defs.MMDL_SENSOR_DATA_SET,
                        CONTROLLER_INDEX),
    "light_ctl_states_get": (defs.BTP_SERVICE_ID_MMDL,
                             defs.MMDL_LIGHT_CTL_STATES_GET,
                             CONTROLLER_INDEX, ""),
    "light_ctl_states_set": (defs.BTP_SERVICE_ID_MMDL,
                             defs.MMDL_LIGHT_CTL_STATES_SET,
                             CONTROLLER_INDEX),
    "light_ctl_temperature_get": (defs.BTP_SERVICE_ID_MMDL,
                                  defs.MMDL_LIGHT_CTL_TEMPERATURE_GET,
                                  CONTROLLER_INDEX, ""),
    "light_ctl_temperature_set": (defs.BTP_SERVICE_ID_MMDL,
                                  defs.MMDL_LIGHT_CTL_TEMPERATURE_SET,
                                  CONTROLLER_INDEX),
    "light_ctl_default_get": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_CTL_DEFAULT_GET,
                              CONTROLLER_INDEX, ""),
    "light_ctl_default_set": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_CTL_DEFAULT_SET,
                              CONTROLLER_INDEX),
    "light_ctl_temp_range_get": (defs.BTP_SERVICE_ID_MMDL,
                                 defs.MMDL_LIGHT_CTL_TEMPERATURE_RANGE_GET,
                                 CONTROLLER_INDEX, ""),
    "light_ctl_temp_range_set": (defs.BTP_SERVICE_ID_MMDL,
                                 defs.MMDL_LIGHT_CTL_TEMPERATURE_RANGE_SET,
                                 CONTROLLER_INDEX),
    "scene_get": (defs.BTP_SERVICE_ID_MMDL,
                  defs.MMDL_SCENE_STATE_GET,
                  CONTROLLER_INDEX, ""),
    "scene_register_get": (defs.BTP_SERVICE_ID_MMDL,
                           defs.MMDL_SCENE_REGISTER_GET,
                           CONTROLLER_INDEX, ""),
    "scene_store_procedure": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_SCENE_STORE_PROCEDURE,
                              CONTROLLER_INDEX),
    "scene_recall": (defs.BTP_SERVICE_ID_MMDL,
                     defs.MMDL_SCENE_RECALL,
                     CONTROLLER_INDEX),
    "light_xyl_get": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_LIGHT_XYL_GET,
                      CONTROLLER_INDEX, ""),
    "light_xyl_set": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_LIGHT_XYL_SET,
                      CONTROLLER_INDEX),
    "light_xyl_target_get": (defs.BTP_SERVICE_ID_MMDL,
                             defs.MMDL_LIGHT_XYL_TARGET_GET,
                             CONTROLLER_INDEX, ""),
    "light_xyl_default_get": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_XYL_DEFAULT_GET,
                              CONTROLLER_INDEX, ""),
    "light_xyl_default_set": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_XYL_DEFAULT_SET,
                              CONTROLLER_INDEX),
    "light_xyl_range_get": (defs.BTP_SERVICE_ID_MMDL,
                            defs.MMDL_LIGHT_XYL_RANGE_GET,
                            CONTROLLER_INDEX, ""),
    "light_xyl_range_set": (defs.BTP_SERVICE_ID_MMDL,
                            defs.MMDL_LIGHT_XYL_RANGE_SET,
                            CONTROLLER_INDEX),
    "light_hsl_get": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_LIGHT_HSL_GET,
                      CONTROLLER_INDEX, ""),
    "light_hsl_set": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_LIGHT_HSL_SET,
                      CONTROLLER_INDEX),
    "light_hsl_target_get": (defs.BTP_SERVICE_ID_MMDL,
                             defs.MMDL_LIGHT_HSL_TARGET_GET,
                             CONTROLLER_INDEX, ""),
    "light_hsl_default_get": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_HSL_DEFAULT_GET,
                              CONTROLLER_INDEX, ""),
    "light_hsl_default_set": (defs.BTP_SERVICE_ID_MMDL,
                              defs.MMDL_LIGHT_HSL_DEFAULT_SET,
                              CONTROLLER_INDEX),
    "light_hsl_range_get": (defs.BTP_SERVICE_ID_MMDL,
                            defs.MMDL_LIGHT_HSL_RANGE_GET,
                            CONTROLLER_INDEX, ""),
    "light_hsl_range_set": (defs.BTP_SERVICE_ID_MMDL,
                            defs.MMDL_LIGHT_HSL_RANGE_SET,
                            CONTROLLER_INDEX),
    "light_hsl_hue_get": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_LIGHT_HSL_HUE_GET,
                          CONTROLLER_INDEX, ""),
    "light_hsl_hue_set": (defs.BTP_SERVICE_ID_MMDL,
                          defs.MMDL_LIGHT_HSL_HUE_SET,
                          CONTROLLER_INDEX),
    "light_hsl_saturation_get": (defs.BTP_SERVICE_ID_MMDL,
                                 defs.MMDL_LIGHT_HSL_SATURATION_GET,
                                 CONTROLLER_INDEX, ""),
    "light_hsl_saturation_set": (defs.BTP_SERVICE_ID_MMDL,
                                 defs.MMDL_LIGHT_HSL_SATURATION_SET,
                                 CONTROLLER_INDEX),
    "scheduler_get": (defs.BTP_SERVICE_ID_MMDL,
                      defs.MMDL_SCHEDULER_GET,
                      CONTROLLER_INDEX, ""),
    "scheduler_action_get": (defs.BTP_SERVICE_ID_MMDL,
                             defs.MMDL_SCHEDULER_ACTION_GET,
                             CONTROLLER_INDEX),
    "scheduler_action_set": (defs.BTP_SERVICE_ID_MMDL,
                             defs.MMDL_SCHEDULER_ACTION_SET,
                             CONTROLLER_INDEX),
}


def mmdl_gen_onoff_get():
    logging.debug("%s", mmdl_gen_onoff_get.__name__)

    iutctl = get_iut()

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_onoff_get'])

    hdr_fmt = '<BBi'
    onoff, onoff_target, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set("Status", [onoff])
    logging.debug("Status onoff = %r",
                  stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_onoff_set(onoff, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_gen_onoff_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BB", ack, onoff))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_onoff_set'], data=data)

    if ack:
        hdr_fmt = '<BBi'
        onoff_r, target_onoff, remaining_time = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target_onoff])
        else:
            stack.mesh.recv_status_data_set("Status", [onoff_r])
        logging.debug("Status onoff = %r",
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_gen_lvl_get():
    logging.debug("%s", mmdl_gen_lvl_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_lvl_get'])

    hdr_fmt = '<hhi'
    level, target_level, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set("Status", [level])
    logging.debug("Satatus level = %r",
                  stack.mesh.recv_status_data_get("Status"))


def mmdl_gen_lvl_set(lvl, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_gen_lvl_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<Bh", ack, lvl))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_lvl_set'], data=data)

    if ack:
        hdr_fmt = '<hhi'
        level, target_level, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target_level])
        else:
            stack.mesh.recv_status_data_set("Status", [level])
        logging.debug("Status level = %r",
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_gen_lvl_delta_set(delta, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_gen_lvl_delta_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<Bi", ack, delta))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['gen_lvl_delta_set'], data=data)

    if ack:
        hdr_fmt = '<hhi'
        delta, delta_target, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [delta_target])
        else:
            stack.mesh.recv_status_data_set("Status", [delta])
        logging.debug("Status delta = %r",
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_gen_lvl_move_set(move, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_gen_lvl_move_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<Bh", ack, move))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['gen_lvl_move_set'], data=data)

    if ack:
        hdr_fmt = '<hhi'
        level, target_level, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target_level])
        else:
            stack.mesh.recv_status_data_set("Status", [level])
        logging.debug("Status level = %r",
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_gen_dtt_get():
    logging.debug("%s", mmdl_gen_dtt_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_dtt_get'])

    hdr_fmt = '<i'
    tt, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [tt])
    logging.debug("Status tt = %r", stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_dtt_set(tt, ack=True):
    logging.debug("%s", mmdl_gen_dtt_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BB", ack, tt))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_dtt_set'], data=data)

    if ack:
        hdr_fmt = '<i'
        tt, = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set("Status", [tt])
        logging.debug("Status tt = %r",
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_gen_ponoff_get():
    logging.debug("%s", mmdl_gen_ponoff_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_ponoff_get'])

    hdr_fmt = '<b'
    on_power_up, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [on_power_up])
    logging.debug("Status on power up = %r",
                  stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_ponoff_set(on_power_up, ack=True):
    logging.debug("%s", mmdl_gen_ponoff_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BB", ack, on_power_up))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['gen_ponoff_set'], data=data)

    if ack:
        hdr_fmt = '<b'
        on_power_up, = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [on_power_up])
        logging.debug("Status on power up = %r",
                      stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_plvl_get():
    logging.debug("%s", mmdl_gen_plvl_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_plvl_get'])

    hdr_fmt = '<H'
    power_level, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [power_level])
    logging.debug("Status power level = %r",
                  stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_plvl_set(power_lvl, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_gen_plvl_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, power_lvl))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_plvl_set'], data=data)

    if ack:
        hdr_fmt = '<HHi'
        present_power, target_power, remaining_time = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target_power])
        else:
            stack.mesh.recv_status_data_set('Status', [present_power])
        logging.debug("Status power = %r",
                      stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_plvl_last_get():
    logging.debug("%s", mmdl_gen_plvl_last_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_plvl_last_get'])

    hdr_fmt = '<H'
    power_last, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [power_last])
    logging.debug("Status power last = %r",
                  stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_plvl_dflt_get():
    logging.debug("%s", mmdl_gen_plvl_dflt_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_plvl_dflt_get'])

    hdr_fmt = '<H'
    present_power, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [present_power])
    logging.debug("Status power = %r",
                  stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_plvl_dflt_set(dflt, ack=True):
    logging.debug("%s", mmdl_gen_plvl_dflt_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, dflt))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['gen_plvl_dflt_set'], data=data)

    if ack:
        hdr_fmt = '<H'
        power_default, = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set("Status", [power_default])
        logging.debug("Status power = %r",
                      stack.mesh.recv_status_data_get('Status'))


def mmdl_gen_plvl_range_get():
    logging.debug("%s", mmdl_gen_plvl_range_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_plvl_range_get'])

    hdr_fmt = '<HH'
    status, = struct.unpack_from('<B', rsp)
    range_min, range_max, = struct.unpack_from(hdr_fmt, rsp[2:])
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [status, range_min, range_max])
    logging.debug("Status: Range Min = %r Range Max = %r Status = %r",
                  range_min, range_max, status)


def mmdl_gen_plvl_range_set(range_min, range_max, ack=True):
    logging.debug("%s", mmdl_gen_plvl_range_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHH", ack, range_min, range_max))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['gen_plvl_range_set'], data=data)

    if ack:
        hdr_fmt = '<HH'
        status, = struct.unpack_from('<B', rsp)
        range_min, range_max, = struct.unpack_from(hdr_fmt, rsp[2:])
        stack = get_stack()
        stack.mesh.recv_status_data_set(
            'Status', [status, range_min, range_max])
        logging.debug("Status: Range Min = %r Range Max = %r Status = %r",
                      range_min, range_max, status)


def mmdl_gen_battery_get():
    logging.debug("%s", mmdl_gen_battery_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_battery_get'])

    hdr_fmt = '<B3s3sB'
    battery, discharge_min, charge_min, flags = struct.unpack_from(
        hdr_fmt, rsp)
    discharge_min = int(binascii.hexlify(discharge_min), 16)
    charge_min = int(binascii.hexlify(charge_min), 16)
    stack = get_stack()
    stack.mesh.recv_status_data_set(
        'Status', [battery, discharge_min, charge_min, flags])
    logging.debug("Status: Battery = %r , Discharge Min = 0x%x , Charge Min = 0x%x , Flags = %r",
                  battery, discharge_min, charge_min, flags)


def mmdl_gen_loc_global_get():
    logging.debug("%s", mmdl_gen_loc_global_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_loc_global_get'])

    hdr_fmt = '<IIH'
    lat, lon, alt = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lat, lon, alt])
    logging.debug('Status: Lat = 0x%x Lon = 0x%x Alt = 0x%x', lat, lon, alt)


def mmdl_gen_loc_local_get():
    logging.debug("%s", mmdl_gen_loc_local_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_loc_local_get'])

    hdr_fmt = '<HHHBH'
    north, east, alt, floor, location_uncert = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set(
        'Status', [north, east, alt, floor, location_uncert])
    logging.debug('Status: North = 0x%x East = 0x%x Alt = 0x%x Floor = 0x%x Location uncert = 0x%x',
                  north, east, alt, floor, location_uncert)


def mmdl_gen_loc_global_set(lat, lon, alt, ack=True):
    logging.debug("%s", mmdl_gen_loc_global_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BIIH", ack, lat, lon, alt))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['gen_loc_global_set'], data=data)

    if ack:
        hdr_fmt = '<IIH'
        lat, lon, alt = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [lat, lon, alt])
        logging.debug(
            'Status: Lat = 0x%x Lon = 0x%x Alt = 0x%x', lat, lon, alt)


def mmdl_gen_loc_local_set(north, east, alt, floor, location_uncert, ack=True):
    logging.debug("%s", mmdl_gen_loc_local_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHHBH", ack, north,
                                 east, alt, floor, location_uncert))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['gen_loc_local_set'], data=data)

    if ack:
        hdr_fmt = '<HHHBH'
        north, east, alt, floor, location_uncert = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set(
            'Status', [north, east, alt, floor, location_uncert])
        logging.debug('Status: North = 0x%x East = 0x%x Alt = 0x%x Floor = 0x%x Location uncert = 0x%x',
                      north, east, alt, floor, location_uncert)


def mmdl_gen_props_get(kind, prop_id=0):
    logging.debug("%s", mmdl_gen_props_get.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", kind, prop_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_props_get'], data=data)

    prop_id = int(binascii.hexlify(rsp), 16)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [prop_id])
    logging.debug('Status: Property IDs = %r)', prop_id)


def mmdl_gen_prop_get(kind, prop_id):
    logging.debug("%s", mmdl_gen_prop_get.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", kind, prop_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_prop_get'], data=data)

    hdr_fmt = '<HBB'
    (prop_id, access, size) = struct.unpack_from(hdr_fmt, rsp)
    val = int(binascii.hexlify(rsp[4:]), 16)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [prop_id, access, val])
    logging.debug('Status: Property ID = %r, Access = %r, Size = %r, Val = 0x%x',
                  prop_id, access, size, val)


def mmdl_gen_prop_set(kind, prop_id, access, value, ack=True):
    logging.debug("%s", mmdl_gen_prop_set.__name__)

    payload = binascii.unhexlify(value)
    payload_len = len(payload)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BBHBB", ack, kind,
                                 prop_id, access, payload_len))
    data.extend(payload)

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['gen_prop_set'], data=data)

    if ack:
        hdr_fmt = '<HBB'
        (prop_id_r, access_r, size_r) = struct.unpack_from(hdr_fmt, rsp)
        val = int(binascii.hexlify(rsp[4:]), 16)
        if value == '':
            val = value
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [prop_id, access, val])
        logging.debug('Status: Property ID = %r, Access = %r, Size = %r, Val = %r',
                      prop_id, access, size_r, val)


def mmdl_sensor_desc_get(sensor_id=None):
    logging.debug("%s", mmdl_sensor_desc_get.__name__)

    iutctl = get_iut()
    if sensor_id:
        data = bytearray(struct.pack("<H", sensor_id))
    else:
        data = ""

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['sensor_desc_get'], data=data)

    prop_id = int(binascii.hexlify(rsp), 16)

    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [prop_id])
    logging.debug('Status: PropertyId = 0x%x ', prop_id)


def mmdl_sensor_get(sensor_id):
    logging.debug("%s", mmdl_sensor_get.__name__)

    iutctl = get_iut()
    if sensor_id:
        data = bytearray(struct.pack("<H", sensor_id))
    else:
        data = ""

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['sensor_get'], data=data)

    if len(binascii.hexlify(rsp)) == 6:
        hdr_fmt = '<H1s'
        sensor_id, sensor_data = struct.unpack_from(hdr_fmt, rsp)
        sensor_data = int(binascii.hexlify(sensor_data))
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [sensor_id, sensor_data])
        logging.debug('Status: Sensor id = 0x%x, Sensor data = 0x%x',
                      sensor_id, sensor_data)

    else:
        hdr_fmt = '<H1sH3sH3s'
        sensor_id_0, sensor_data_0, sensor_id_1, sensor_data_1, sensor_id_2, sensor_data_2 = struct.unpack_from(
            hdr_fmt, rsp)
        sensor_data_0 = int(binascii.hexlify(sensor_data_0))
        sensor_data_1 = int(binascii.hexlify(sensor_data_1))
        sensor_data_2 = int(binascii.hexlify(sensor_data_2))
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [
            sensor_id_0, sensor_data_0, sensor_id_1, sensor_data_1, sensor_id_2, sensor_data_2])
        logging.debug(
            ("Status: Sensor id = 0x%x Sensor data = 0x%x \n Sensor id = 0x%x "
             "Sensor data = 0x%x \n Sensor id = 0x%x Sensor data = 0x%x"),
            sensor_id_0,
            sensor_data_0,
            sensor_id_1,
            sensor_data_1,
            sensor_id_2,
            sensor_data_2)


def mmdl_sensor_cadence_get(sensor_id):
    logging.debug("%s", mmdl_sensor_cadence_get.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<H", sensor_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['sensor_cadence_get'], data=data)
    hdr_fmt = '<H'
    data = int(binascii.hexlify(rsp[:6]), 16)
    (sensor_id,) = struct.unpack_from(hdr_fmt, rsp[6:])
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [sensor_id, data])
    logging.debug('Status: Sensor data = 0x%x Sensor id = 0x%x',
                  data, sensor_id)


def mmdl_sensor_cadence_set(sensor_id, payload, ack=True):
    logging.debug("%s", mmdl_sensor_cadence_set.__name__)

    payload = binascii.unhexlify(payload)
    payload_len = len(payload)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHH", ack, sensor_id, payload_len))
    data.extend(payload)

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['sensor_cadence_set'], data=data)
    if ack:
        data = binascii.hexlify(rsp).decode('UTF-8')
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [data])
        logging.debug('Satus: Cadence data = %r ', data)


def mmdl_sensor_settings_get(sensor_id):
    logging.debug("%s", mmdl_sensor_settings_get.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<H", sensor_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['sensor_settings_get'], data=data)
    hdr_fmt = '<HH'
    (sensor_id, prop_id) = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [sensor_id, prop_id])
    logging.debug(
        'Status: Sensor Id = 0x%x Setting prop Id = 0x%x', sensor_id, prop_id)


def mmdl_sensor_setting_get(sensor_id, setting_id):
    logging.debug("%s", mmdl_sensor_setting_get.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<HH", sensor_id, setting_id))

    iutctl.btp_socket.send_wait_rsp(*MMDL['sensor_setting_get'], data=data)


def mmdl_sensor_setting_set(sensor_id, setting_id, setting_raw, ack=True):
    logging.debug("%s", mmdl_sensor_setting_set.__name__)

    payload = binascii.unhexlify(setting_raw)
    payload_len = len(payload)

    iutctl = get_iut()
    data = bytearray(struct.pack(
        "<BHHB", ack, sensor_id, setting_id, payload_len))
    data.extend(payload)

    iutctl.btp_socket.send_wait_rsp(*MMDL['sensor_setting_set'], data=data)


def mmdl_sensor_column_get(sensor_id, raw_value):
    logging.debug("%s", mmdl_sensor_column_get.__name__)

    payload = binascii.unhexlify(raw_value)
    payload_len = len(payload)

    iutctl = get_iut()
    data = bytearray(struct.pack("<HB", sensor_id, payload_len))
    data.extend(payload)

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['sensor_column_get'], data=data)

    hdr_fmt = '<H%ds' % (len(rsp) - 2)
    (prop_id, column_data) = struct.unpack_from(hdr_fmt, rsp)
    column_data = binascii.hexlify(column_data).decode('UTF-8')
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [prop_id, column_data])
    logging.debug('Status: Property ID = 0x%x Column data = %r',
                  prop_id, column_data)


def mmdl_sensor_series_get(sensor_id, raw_values):
    logging.debug("%s", mmdl_sensor_series_get.__name__)

    payload = binascii.unhexlify(raw_values)
    payload_len = len(payload)

    iutctl = get_iut()
    data = bytearray(struct.pack("<HB", sensor_id, payload_len))
    data.extend(payload)

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['sensor_series_get'], data=data)
    hdr_fmt = '<9sH'
    (column_data, prop_id) = struct.unpack_from(hdr_fmt, rsp)
    column_data = int(binascii.hexlify(column_data), 16)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [prop_id, column_data])
    logging.debug('Status: Property ID = 0x%x Column data = 0x%x',
                  prop_id, column_data)


def mmdl_time_get():
    logging.debug("%s", mmdl_time_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['time_get'])

    hdr_fmt = '<5sBBHB'
    (tai, subsecond, uncertainty, tai_utc_delta,
     time_zone_offset) = struct.unpack_from(hdr_fmt, rsp)
    tai = int(binascii.hexlify(tai[::-1]), 16)
    stack = get_stack()
    stack.mesh.recv_status_data_set(
        'Status', [tai, subsecond, uncertainty, tai_utc_delta, time_zone_offset])
    logging.debug(
        'Status: TAI Seconds = %r , Subsecond = %r , Uncertainty = %r , TAI-UTC Delta = %r , Time Zone Offset = %r',
        tai,
        subsecond,
        uncertainty,
        tai_utc_delta,
        time_zone_offset)


def mmdl_time_set(tai, subsecond, uncertainty, tai_utc_delta, time_zone_offset):
    logging.debug("%s", mmdl_time_set.__name__)

    iutctl = get_iut()

    data = bytearray(struct.pack("<IBBBHB", tai & 0xffffffff, tai >>
                                 32, subsecond, uncertainty, tai_utc_delta, time_zone_offset))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['time_set'], data=data)

    hdr_fmt = '<5sBBHB'

    (tai, subsecond, uncertainty, tai_utc_delta,
     time_zone_offset) = struct.unpack_from(hdr_fmt, rsp)
    tai = int(binascii.hexlify(tai[::-1]).lower(), 16)
    stack = get_stack()
    stack.mesh.recv_status_data_set(
        'Status', [tai, subsecond, uncertainty, tai_utc_delta, time_zone_offset])
    logging.debug(
        'Status: TAI Seconds = %r , Subsecond = %r , Uncertainty = %r , TAI-UTC Delta = %r , Time Zone Offset = %r',
        tai,
        subsecond,
        uncertainty,
        tai_utc_delta,
        time_zone_offset)


def mmdl_time_role_get():
    logging.debug("%s", mmdl_time_role_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['time_role_get'])

    hdr_fmt = '<B'
    role, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [role])
    logging.debug('Status: Time role = %r', role)


def mmdl_time_role_set(role):
    logging.debug("%s", mmdl_time_role_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<B", role))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['time_role_set'], data=data)

    hdr_fmt = '<B'
    role, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [role])
    logging.debug('Status: Time role = %r', role)


def mmdl_time_zone_get():
    logging.debug("%s", mmdl_time_zone_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['time_zone_get'])

    hdr_fmt = '<hhQ'
    current_offset, new_offset, timestamp = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set(
        'Status', [current_offset, new_offset, timestamp])
    logging.debug('Status: Current offset = 0x%x , New offset = 0x%x Timestamp = 0x%x',
                  current_offset, new_offset, timestamp)


def mmdl_time_zone_set(new_offset, timestamp):
    logging.debug("%s", mmdl_time_zone_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<hQ", new_offset, timestamp))

    rsp, = iutctl.btp_socket.send_wait_rsp(*MMDL['time_zone_set'], data=data)

    hdr_fmt = '<hQ'
    new_offset, timestamp = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [new_offset, timestamp])
    logging.debug('Status: New offset = %r Timestamp = %r',
                  new_offset, timestamp)


def mmdl_time_tai_utc_delta_get():
    logging.debug("%s", mmdl_time_tai_utc_delta_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['time_tai_utc_delta_get'])

    hdr_fmt = '<hhQ'
    delta_current, delta_new, timestamp = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set(
        'Status', [delta_current, delta_new, timestamp])
    logging.debug('Status: Delta current = %r New delta = %r Timestamp = %r',
                  delta_current, delta_new, timestamp)


def mmdl_time_tai_utc_delta_set(delta_new, timestamp):
    logging.debug("%s", mmdl_time_tai_utc_delta_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<hQ", delta_new, timestamp))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['time_tai_utc_delta_set'], data=data)

    hdr_fmt = '<hQ'
    delta_new, timestamp = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [delta_new, timestamp])
    logging.debug('Status: New delta = %r Timestamp = %r',
                  delta_new, timestamp)


def mmdl_light_lightness_get():
    logging.debug("%s", mmdl_light_lightness_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_lightness_get'])

    hdr_fmt = '<HHi'
    lightness, tt, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness])
    logging.debug('Status: Lightness = %r', lightness)


def mmdl_light_lightness_set(lightness, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_light_lightness_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, lightness))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lightness_set'], data=data)

    if ack:
        hdr_fmt = '<HHi'
        lightness, target, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target])
        else:
            stack.mesh.recv_status_data_set('Status', [lightness])

        logging.debug('Status: Lightness = %r ',
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_light_lightness_linear_get():
    logging.debug("%s", mmdl_light_lightness_linear_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lightness_linear_get'])

    hdr_fmt = '<HH'
    lightness, lightness_target = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness])

    logging.debug('Status: Lightness linear = %r ',
                  stack.mesh.recv_status_data_get("Status"))


def mmdl_light_lightness_linear_set(lightness_linear, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_light_lightness_linear_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, lightness_linear))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lightness_linear_set'], data=data)

    if ack:
        hdr_fmt = '<HHi'
        lightness_linear, target, remaining_time = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target])
        else:
            stack.mesh.recv_status_data_set('Status', [lightness_linear])

        logging.debug('Status: Lightness linear = %r ',
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_light_lightness_last_get():
    logging.debug("%s", mmdl_light_lightness_last_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_lightness_last_get'])

    hdr_fmt = '<H'
    lightness, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness])

    logging.debug('Status: Lightness last = %r ',
                  stack.mesh.recv_status_data_get("Status"))


def mmdl_light_lightness_default_get():
    logging.debug("%s", mmdl_light_lightness_default_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lightness_default_get'])

    hdr_fmt = '<H'
    dflt, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [dflt])

    logging.debug('Status: Lightness default= %r ',
                  stack.mesh.recv_status_data_get("Status"))


def mmdl_light_lightness_default_set(dflt, ack=True):
    logging.debug("%s", mmdl_light_lightness_default_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, dflt))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lightness_default_set'], data=data)

    if ack:
        hdr_fmt = '<H'
        dflt, = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [dflt])

        logging.debug('Status: Lightness default = %r ',
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_light_lightness_range_get():
    logging.debug("%s", mmdl_light_lightness_range_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lightness_range_get'])

    hdr_fmt = '<HHH'
    status, min_val, max_val = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [status, min_val, max_val])
    logging.debug(
        'Status: Status Code = %r , Range min = %r Range max = %r', status, min_val, max_val)


def mmdl_light_lightness_range_set(min_val, max_val, ack=True):
    logging.debug("%s", mmdl_light_lightness_range_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHH", ack, min_val, max_val))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lightness_range_set'], data=data)

    if ack:
        hdr_fmt = '<HHH'
        status, min_val, max_val = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [status, min_val, max_val])
        logging.debug(
            'Status: Status code = %r, Range min = %r Range max = %r', status, min_val, max_val)


def mmdl_light_lc_mode_get():
    logging.debug("%s", mmdl_light_lc_mode_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_lc_mode_get'])

    hdr_fmt = '<B'
    mode, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [mode])
    logging.debug('Satus: Mode = %r', mode)


def mmdl_light_lc_mode_set(mode, ack=True):
    logging.debug("%s", mmdl_light_lc_mode_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BB", ack, mode))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lc_mode_set'], data=data)

    if ack:
        hdr_fmt = '<B'
        mode, = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [mode])
        logging.debug('Status: Mode = %r', mode)


def mmdl_light_lc_occupancy_mode_get():
    logging.debug("%s", mmdl_light_lc_occupancy_mode_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lc_occupancy_mode_get'])

    hdr_fmt = '<B'
    occupancy_mode, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [occupancy_mode])
    logging.debug('Status: Occupancy mode = %r', occupancy_mode)


def mmdl_light_lc_occupancy_mode_set(occupancy_mode, ack=True):
    logging.debug("%s", mmdl_light_lc_occupancy_mode_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BB", ack, occupancy_mode))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lc_occupancy_mode_set'], data=data)

    if ack:
        hdr_fmt = '<B'
        occupancy_mode, = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [occupancy_mode])
        logging.debug('Status: Occupancy mode = %r', occupancy_mode)


def mmdl_light_lc_light_onoff_mode_get():
    logging.debug("%s", mmdl_light_lc_light_onoff_mode_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lc_light_onoff_mode_get'])

    hdr_fmt = '<B'
    light_onoff_mode, = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [light_onoff_mode])
    logging.debug('Status: Light onoff mode = %r', light_onoff_mode)


def mmdl_light_lc_light_onoff_mode_set(light_onoff_mode, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_light_lc_light_onoff_mode_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BB", ack, light_onoff_mode))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lc_light_onoff_mode_set'], data=data)

    if ack:
        hdr_fmt = '<BBi'
        light_onoff_mode, target, remaining_time = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target])
        else:
            stack.mesh.recv_status_data_set('Status', [light_onoff_mode])

        logging.debug('Status: Lightness onoff mode= %r ',
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_light_lc_property_get(prop_id):
    logging.debug("%s", mmdl_light_lc_property_get.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<H", prop_id))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lc_property_get'], data=data)

    hdr_fmt = '<HH'
    prop_id, prop_val = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [prop_id, prop_val])
    logging.debug(
        'Status: Property value = %r , Property Id = %r ', prop_val, prop_id)


def mmdl_light_lc_property_set(prop_id, prop_val, ack=True):
    logging.debug("%s", mmdl_light_lc_property_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHH", ack, prop_id, prop_val))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_lc_property_set'], data=data)

    if ack:
        hdr_fmt = '<HH'
        prop_id, prop_val = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [prop_id, prop_val])
        logging.debug(
            'Status: Property value = %r , Property Id = %r ', prop_val, prop_id)


def mmdl_sensor_data_set(sensor_id, raw_values):
    logging.debug("%s", mmdl_sensor_data_set.__name__)

    payload_len = len(raw_values)

    iutctl = get_iut()
    data = bytearray(struct.pack("<HB", sensor_id, payload_len))
    data.extend(raw_values)

    iutctl.btp_socket.send_wait_rsp(*MMDL['sensor_data_set'], data=data)


def mmdl_light_ctl_states_get():
    logging.debug("%s", mmdl_light_ctl_states_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_ctl_states_get'])

    hdr_fmt = '<HHHHi'
    current_light, current_temp, target_light, target_temp, remaining_time = struct.unpack_from(
        hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [current_light, current_temp])
    logging.debug('Status: Light, Temp = %r',
                  stack.mesh.recv_status_data_get("Status"))


def mmdl_light_ctl_states_set(ctl_lightness, ctl_temperature, ctl_delta_uv, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_light_ctl_states_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHh", ack, ctl_lightness,
                                 ctl_temperature, ctl_delta_uv))

    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_ctl_states_set'], data=data)

    if ack:
        hdr_fmt = '<HHHHi'
        current_light, current_temp, target_light, target_temp, remaining_time = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set(
                "Status", [target_light, target_temp])
        else:
            stack.mesh.recv_status_data_set(
                'Status', [current_light, current_temp])

        logging.debug('Status: Light, Temp = %r',
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_light_ctl_temperature_get():
    logging.debug("%s", mmdl_light_ctl_temperature_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_ctl_temperature_get'])

    hdr_fmt = '<HhHhi'
    current_temp, current_delta, target_temp, target_delta, remaining_time = struct.unpack_from(
        hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [current_temp, current_delta])
    logging.debug('Status: Temp, Delta = %r',
                  stack.mesh.recv_status_data_get("Status"))


def mmdl_light_ctl_temperature_set(ctl_temperature, ctl_delta_uv, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_light_ctl_temperature_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHh", ack, ctl_temperature, ctl_delta_uv))

    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_ctl_temperature_set'], data=data)

    if ack:
        hdr_fmt = '<HHHHi'
        current_temp, current_delta, target_temp, target_delta, remaining_time = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set(
                "Status", [target_temp, target_delta])
        else:
            stack.mesh.recv_status_data_set(
                'Status', [current_temp, current_delta])

        logging.debug('Status: Temp, Delta = %r',
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_light_ctl_default_get():
    logging.debug("%s", mmdl_light_ctl_default_get.__name__)

    iutctl = get_iut()

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_ctl_default_get'])

    hdr_fmt = '<HHh'
    ctl_light, ctl_temp, ctl_delta = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [ctl_light, ctl_temp, ctl_delta])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_ctl_default_set(ctl_lightness, ctl_temperature, ctl_delta_uv, ack=True):
    logging.debug("%s", mmdl_light_ctl_default_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHh", ack, ctl_lightness,
                                 ctl_temperature, ctl_delta_uv))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_ctl_default_set'], data=data)

    if ack:
        hdr_fmt = '<HHh'
        ctl_light, ctl_temp, ctl_delta = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set(
            'Status', [ctl_light, ctl_temp, ctl_delta])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_ctl_temp_range_get():
    logging.debug("%s", mmdl_light_ctl_temp_range_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_ctl_temp_range_get'])

    hdr_fmt = '<BHH'
    status, range_min, range_max = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [status, range_min, range_max])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_ctl_temp_range_set(range_min, range_max, ack=True):
    logging.debug("%s", mmdl_light_ctl_temp_range_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHH", ack, range_min, range_max))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['light_ctl_temp_range_set'], data=data)

    if ack:
        hdr_fmt = '<BHH'
        status, range_min, range_max = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [range_min, range_max])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_scene_get():
    logging.debug("%s", mmdl_scene_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['scene_get'])

    hdr_fmt = '<BHH'
    status, scene, target = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [status, scene])
    logging.debug('Status: Status = %r , Scene = %r, Target = %r',
                  status, scene, target)


def mmdl_scene_register_get():
    logging.debug("%s", mmdl_scene_register_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['scene_register_get'])

    hdr_fmt = '<BH'
    status, scene = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [status, scene])
    logging.debug('Status: Status = %r , Scene = %r', status, scene)


def mmdl_scene_store_procedure(scene_num, ack=True):
    logging.debug("%s", mmdl_scene_store_procedure.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, scene_num))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(
        *MMDL['scene_store_procedure'], data=data)

    if ack:
        hdr_fmt = '<BH'
        status, scene = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [scene])
        logging.debug('Status: Status = %r , Scene = %r', status, scene)


def mmdl_scene_recall(scene_num, tt=None, delay=None, ack=True):
    logging.debug("%s", mmdl_scene_recall.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, scene_num))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['scene_recall'], data=data)

    if ack:
        hdr_fmt = '<BHHi'
        status, scene, target, remaining_time = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        if remaining_time:
            stack.mesh.recv_status_data_set("Status", [target])
        else:
            stack.mesh.recv_status_data_set('Status', [scene])

        logging.debug('Status: Scene = %r ',
                      stack.mesh.recv_status_data_get("Status"))


def mmdl_light_xyl_get():
    logging.debug("%s", mmdl_light_xyl_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_xyl_get'])

    hdr_fmt = '<HHHi'
    lightness, x_value, y_value, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness, x_value, y_value])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_xyl_set(lightness, x_value, y_value, tt, delay, ack=True):
    logging.debug("%s", mmdl_light_xyl_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHH", ack, lightness, x_value, y_value))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_xyl_set'], data=data)

    if ack:
        hdr_fmt = '<HHHI'
        lightness, x_value, y_value, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [lightness, x_value, y_value])
        stack.mesh.recv_status_data_set('Remaining Time', remaining_time)
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_xyl_target_get():
    logging.debug("%s", mmdl_light_xyl_target_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_xyl_target_get'])

    hdr_fmt = '<HHHi'
    lightness, x_value, y_value, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness, x_value, y_value])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_xyl_default_get():
    logging.debug("%s", mmdl_light_xyl_default_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_xyl_default_get'])

    hdr_fmt = '<HHH'
    lightness, x_value, y_value = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness, x_value, y_value])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_xyl_default_set(lightness, x_value, y_value, ack=True):
    logging.debug("%s", mmdl_light_xyl_default_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHH", ack, lightness, x_value, y_value))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_xyl_default_set'], data=data)

    if ack:
        hdr_fmt = '<HHH'
        lightness, x_value, y_value = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [lightness, x_value, y_value])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_xyl_range_get():
    logging.debug("%s", mmdl_light_xyl_range_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_xyl_range_get'])

    hdr_fmt = '<BHHHH'
    status, min_x, min_y, max_x, max_y = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [status, min_x, min_y, max_x, max_y])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_xyl_range_set(lmin_x, min_y, max_x, max_y, ack=True):
    logging.debug("%s", mmdl_light_xyl_range_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHHH", ack, lmin_x, min_y, max_x, max_y))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_xyl_range_set'], data=data)

    if ack:
        hdr_fmt = '<BHHHH'
        status, min_x, min_y, max_x, max_y = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [min_x, min_y, max_x, max_y])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_get():
    logging.debug("%s", mmdl_light_hsl_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_get'])

    hdr_fmt = '<HHHi'
    lightness, hue, saturation, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness, hue, saturation])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_set(lightness, hue, saturation, tt, delay, ack=True):
    logging.debug("%s", mmdl_light_hsl_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHH", ack, lightness, hue, saturation))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_set'], data=data)

    if ack:
        hdr_fmt = '<HHHi'
        lightness, hue, saturation, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [lightness, hue, saturation])
        stack.mesh.recv_status_data_set('Remaining Time', remaining_time)
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_target_get():
    logging.debug("%s", mmdl_light_hsl_target_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_target_get'])

    hdr_fmt = '<HHHi'
    lightness, hue, saturation, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness, hue, saturation])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_default_get():
    logging.debug("%s", mmdl_light_hsl_default_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_default_get'])

    hdr_fmt = '<HHH'
    lightness, hue, saturation = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [lightness, hue, saturation])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_default_set(lightness, hue, saturation, ack=True):
    logging.debug("%s", mmdl_light_hsl_default_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHH", ack, lightness, hue, saturation))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_default_set'], data=data)

    if ack:
        hdr_fmt = '<HHH'
        lightness, hue, saturation = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [lightness, hue, saturation])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_range_get():
    logging.debug("%s", mmdl_light_hsl_range_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_range_get'])

    hdr_fmt = '<BHHHH'
    status_code, hue_min, saturation_min, hue_max, saturation_max = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [status_code, hue_min, saturation_min, hue_max, saturation_max])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_range_set(hue_min, saturation_min, hue_max, saturation_max, ack=True):
    logging.debug("%s", mmdl_light_hsl_range_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BHHHH", ack, hue_min, saturation_min, hue_max, saturation_max))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_range_set'], data=data)

    if ack:
        hdr_fmt = '<BHHHH'
        status_code, hue_min, saturation_min, hue_max, saturation_max = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status', [hue_min, saturation_min, hue_max, saturation_max])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_hue_get():
    logging.debug("%s", mmdl_light_hsl_hue_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_hue_get'])

    hdr_fmt = '<HHi'
    hue_current, hue_target, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [hue_current])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_hue_set(hue, tt, delay, ack=True):
    logging.debug("%s", mmdl_light_hsl_hue_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, hue))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_hue_set'], data=data)

    if ack:
        hdr_fmt = '<HHi'
        hue_current, hue_target, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        if delay:
            stack.mesh.recv_status_data_set('Status', [hue_target])
        else:
            stack.mesh.recv_status_data_set('Status', [hue_current])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_saturation_get():
    logging.debug("%s", mmdl_light_hsl_saturation_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_saturation_get'])

    hdr_fmt = '<HHi'
    saturation_current, saturation_target, remaining_time = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [saturation_current])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_light_hsl_saturation_set(hue, tt, delay, ack=True):
    logging.debug("%s", mmdl_light_hsl_saturation_set.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<BH", ack, hue))
    if tt is not None:
        data.extend(struct.pack("<B", tt))
    if delay is not None:
        data.extend(struct.pack("<B", delay))

    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['light_hsl_saturation_set'], data=data)

    if ack:
        hdr_fmt = '<HHi'
        saturation_current, saturation_target, remaining_time = struct.unpack_from(hdr_fmt, rsp)
        stack = get_stack()
        if delay:
            stack.mesh.recv_status_data_set('Status', [saturation_target])
        else:
            stack.mesh.recv_status_data_set('Status', [saturation_current])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_scheduler_get():
    logging.debug("%s", mmdl_scheduler_get.__name__)

    iutctl = get_iut()
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['scheduler_get'])

    hdr_fmt = '<H'
    (schedules,) = struct.unpack_from(hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status', [schedules])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_scheduler_action_get(index):
    logging.debug("%s", mmdl_scheduler_action_get.__name__)

    iutctl = get_iut()
    data = bytearray(struct.pack("<B", index))
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['scheduler_action_get'], data)

    hdr_fmt = '<BBBBBBBBBH'
    year, month, day, hour, minute, second, day_of_week, action, transition_time, scene_num = struct.unpack_from(
        hdr_fmt, rsp)
    stack = get_stack()
    stack.mesh.recv_status_data_set('Status',
                                    [year, month, day, hour, minute, second, day_of_week, action, transition_time,
                                     scene_num])
    logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))


def mmdl_scheduler_action_set(index, year, month, day, hour, minute, second, day_of_week, action, transition_time,
                              scene_num, ack=True):
    logging.debug("%s", mmdl_scheduler_action_set.__name__)

    iutctl = get_iut()
    data = bytearray(
        struct.pack("<BBBHBBBBBBBH", ack, index, year, month, day, hour, minute, second, day_of_week, action,
                    transition_time, scene_num))
    (rsp,) = iutctl.btp_socket.send_wait_rsp(*MMDL['scheduler_action_set'], data)
    if ack:
        hdr_fmt = '<BBBHBBBBBH'
        year, month, day, hour, minute, second, day_of_week, action, transition_time, scene_num = struct.unpack_from(
            hdr_fmt, rsp)
        stack = get_stack()
        stack.mesh.recv_status_data_set('Status',
                                        [index, year, month, day, hour, minute, second, day_of_week, action,
                                         transition_time, scene_num])
        logging.debug('Status: %r', stack.mesh.recv_status_data_get("Status"))
