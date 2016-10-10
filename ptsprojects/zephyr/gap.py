"""GAP test cases"""

try:
    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.ztestcase import ZTestCase

except ImportError:  # running this module as script
    import sys
    sys.path.append("../..")  # to be able to locate the following imports

    from ptsprojects.testcase import TestCase, TestCmd, TestFunc, \
        TestFuncCleanUp
    from ptsprojects.zephyr.ztestcase import ZTestCase

from ptsprojects.zephyr.iutctl import get_zephyr
from time import sleep
import btp
import binascii
import gatt


class Addr:
    le_public = 0
    le_random = 1

class IOCap:
    display_only = 0
    display_yesno = 1
    keyboard_only = 2
    no_input_output = 3


class UUID:
    gap_svc = '1800'
    device_name = '2a00'

class SVC:
    gap = (None, None, UUID.gap_svc)


class CHAR:
    name = (None, None, None, UUID.device_name)


class Prop:
    """Properties of characteresic

    Specified in BTP spec:

    Possible values for the Properties parameter are a bit-wise of the
    following bits:

    0       Broadcast
    1       Read
    2       Write Without Response
    3       Write
    4       Notify
    5       Indicate
    6       Authenticated Signed Writes
    7       Extended Properties

    """
    broadcast     = 2 ** 0
    read          = 2 ** 1
    write_wo_resp = 2 ** 2
    write         = 2 ** 3
    nofity        = 2 ** 4
    indicate      = 2 ** 5
    auth_swrite   = 2 ** 6
    ext_prop      = 2 ** 7

    names = {
        broadcast     : "Broadcast",
        read          : "Read",
        write_wo_resp : "Write Without Response",
        write         : "Write",
        nofity        : "Notify",
        indicate      : "Indicate",
        auth_swrite   : "Authenticated Signed Writes",
        ext_prop      : "Extended Properties",
    }

    @staticmethod
    def decode(prop):
        return decode_flag_name(prop, Prop.names)


class Perm:
    """Permission of characteresic or descriptor

    Specified in BTP spec:

    Possible values for the Permissions parameter are a bit-wise of the
    following bits:

    0       Read
    1       Write
    2       Read with Encryption
    3       Write with Encryption
    4       Read with Authentication
    5       Write with Authentication
    6       Authorization

    """
    read        = 2 ** 0
    write       = 2 ** 1
    read_enc    = 2 ** 2
    write_enc   = 2 ** 3
    read_authn  = 2 ** 4
    write_authn = 2 ** 5
    authz       = 2 ** 6

    names = {
        read        : "Read",
        write       : "Write",
        read_enc    : "Read with Encryption",
        write_enc   : "Write with Encryption",
        read_authn  : "Read with Authentication",
        write_authn : "Write with Authentication",
        authz       : "Authorization"
    }

    @staticmethod
    def decode(perm):
        return decode_flag_name(perm, Perm.names)


init_gatt_db=[TestFunc(btp.core_reg_svc_gatts),
              TestFunc(btp.gatts_add_svc, 0, gatt.UUID.gap_svc),
              TestFunc(btp.gatts_add_char, 0, gatt.Prop.read | gatt.Prop.write,
                       gatt.Perm.read | gatt.Perm.write, gatt.UUID.device_name),
              TestFunc(btp.gatts_set_val, 0, binascii.hexlify('Test GAP')),
              TestFunc(btp.gatts_add_char, 0, gatt.Prop.read | gatt.Prop.write,
                       gatt.Perm.read | gatt.Perm.write, gatt.UUID.appearance),
              TestFunc(btp.gatts_set_val, 0, '1234'),

              TestFunc(btp.gatts_add_svc, 0, gatt.UUID.VND16_1),
              TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                       gatt.Perm.read | gatt.Perm.read_authn,
                       gatt.UUID.VND16_2),
              TestFunc(btp.gatts_set_val, 0, '01'),
              TestFunc(btp.gatts_add_char, 0, gatt.Prop.read,
                       gatt.Perm.read | gatt.Perm.read_enc, gatt.UUID.VND16_3),
              TestFunc(btp.gatts_set_val, 0, '02'),
              TestFunc(btp.gatts_add_char, 0,
                       gatt.Prop.read | gatt.Prop.auth_swrite,
                       gatt.Perm.read | gatt.Perm.write,
                       gatt.UUID.VND16_3),
              TestFunc(btp.gatts_set_val, 0, '03'),
              TestFunc(btp.gatts_start_server)]


class AdType:
    flags = 1
    uuid16_some = 2
    name_short = 8
    uuid16_svc_data = 22
    gap_appearance = 25
    manufacturer_data = 255

iut_device_name = 'Tester'


class AdData:
    ad_manuf = (AdType.manufacturer_data, 'ABCD')
    ad_name_sh = (AdType.name_short, binascii.hexlify(iut_device_name))

# Advertising data
ad = [(AdType.uuid16_some, '1111'),
      (AdType.gap_appearance, '1111'),
      (AdType.name_short, binascii.hexlify('Tester')),
      (AdType.manufacturer_data, '11111111'),
      (AdType.uuid16_svc_data, '111111')]


def test_cases(pts):
    """Returns a list of GAP test cases
    pts -- Instance of PyPTS"""

    pts_bd_addr = pts.q_bd_addr

    pre_conditions=[TestFunc(btp.core_reg_svc_gap),
                    TestFunc(btp.gap_read_ctrl_info),
                    TestFunc(btp.wrap, pts.update_pixit_param,
                             "GAP", "TSPX_bd_addr_iut",
                             btp.get_stored_bd_addr)]

    test_cases = [
        ZTestCase("GAP", "TC_BROB_BCST_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn, start_wid=47),
                   TestFunc(btp.gap_set_nondiscov, start_wid=47),
                   TestFunc(btp.gap_adv_ind_on, start_wid=47)]),
        ZTestCase("GAP", "TC_BROB_BCST_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_set_nondiscov),
                   TestFunc(btp.gap_adv_ind_on, sd=[AdData.ad_manuf, AdData.ad_name_sh])]),
        ZTestCase("GAP", "TC_BROB_BCST_BV_03_C",
                  edit1_wids={1002: (btp.var_store_get_passkey, pts_bd_addr,
                                     Addr.le_public)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.display_only),

                        # Enter general discoverable mode and send connectable
                        # event so that PTS could connect and get IRK
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_set_gendiscov),
                        TestFunc(btp.gap_adv_ind_on,
                                 sd=[AdData.ad_manuf, AdData.ad_name_sh]),
                        TestFunc(pts.update_pixit_param, "GAP",
                                 "TSPX_iut_device_name_in_adv_packet_for_random_address",
                                 iut_device_name),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, post_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, post_wid=77),
                        TestFunc(btp.gap_adv_off, post_wid=77),

                        # Enter broadcast mode
                        TestFunc(btp.gap_set_nonconn, start_wid=80),
                        TestFunc(btp.gap_set_nondiscov, start_wid=80),
                        TestFunc(btp.gap_adv_ind_on,
                                 sd=[AdData.ad_manuf, AdData.ad_name_sh],
                                 start_wid=80),
                        TestFuncCleanUp(btp.gap_adv_off)]),
        ZTestCase("GAP", "TC_BROB_OBSV_BV_01_C",
                  ok_cancel_wids={4: (btp.gap_device_found_ev, Addr.le_public,
                                      pts_bd_addr)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, type='passive',
                                 mode='observe', start_wid=12),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_BROB_OBSV_BV_02_C",
                  ok_cancel_wids={4: (btp.gap_device_found_ev, Addr.le_public,
                                      pts_bd_addr)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, type='active',
                                 mode='observe', start_wid=160),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_NONM_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn, start_wid=5),
                   TestFunc(btp.gap_set_nondiscov, start_wid=5),
                   TestFunc(btp.gap_adv_ind_on, start_wid=5)]),
        ZTestCase("GAP", "TC_DISC_NONM_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nondiscov, start_wid=72),
                   TestFunc(btp.gap_adv_ind_on, start_wid=72)]),
        ZTestCase("GAP", "TC_DISC_LIMM_BV_03_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_set_limdiscov),
                   TestFunc(btp.gap_adv_ind_on, start_wid=59)]),
        ZTestCase("GAP", "TC_DISC_LIMM_BV_04_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_set_limdiscov),
                   TestFunc(btp.gap_adv_ind_on, start_wid=50)]),
        ZTestCase("GAP", "TC_DISC_GENM_BV_03_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_set_gendiscov),
                   TestFunc(btp.gap_adv_ind_on, start_wid=51)]),
        ZTestCase("GAP", "TC_DISC_GENM_BV_04_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_conn),
                   TestFunc(btp.gap_set_gendiscov),
                   TestFunc(btp.gap_adv_ind_on, start_wid=52)]),
        ZTestCase("GAP", "TC_DISC_LIMP_BV_01_C",
                  ok_cancel_wids={10: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, mode='limited',
                                 start_wid=13),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_LIMP_BV_02_C",
                  ok_cancel_wids={11: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr, None, None, None, 15, False)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, mode='limited',
                                 start_wid=13),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_LIMP_BV_03_C",
                  ok_cancel_wids={11: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr, None, None, None, 15, False)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, mode='limited',
                                 start_wid=13),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_LIMP_BV_04_C",
                  ok_cancel_wids={11: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr, None, None, None, 15, False)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, mode='limited',
                                 start_wid=13),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_LIMP_BV_05_C",
                  ok_cancel_wids={11: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr, None, None, None, 15, False)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, mode='limited',
                                 start_wid=13),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        # TODO: fails cause of ZEP-380
        ZTestCase("GAP", "TC_DISC_GENP_BV_01_C",
                  ok_cancel_wids={14: (btp.gap_device_found_ev, Addr.le_public,
                                      pts_bd_addr)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, start_wid=23),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_GENP_BV_02_C",
                  ok_cancel_wids={14: (btp.gap_device_found_ev, Addr.le_public,
                                      pts_bd_addr)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, start_wid=23),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_GENP_BV_03_C",
                  ok_cancel_wids={11: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr, None, None, None, 15, False)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, start_wid=23),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_GENP_BV_04_C",
                  ok_cancel_wids={11: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr, None, None, None, 15, False)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, start_wid=23),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_DISC_GENP_BV_05_C",
                  ok_cancel_wids={11: (btp.gap_device_found_ev, Addr.le_public,
                                       pts_bd_addr, None, None, None, 15, False)},
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_start_discov, start_wid=23),
                        TestFuncCleanUp(btp.gap_stop_discov)]),
        ZTestCase("GAP", "TC_IDLE_NAMP_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gattc_disc_prim_uuid, Addr.le_public,
                            pts_bd_addr, UUID.gap_svc, start_wid=73),
                   TestFunc(btp.gattc_disc_prim_uuid_find_attrs_rsp,
                            (SVC.gap,), store_attrs=True, start_wid=73),
                   TestFunc(btp.gattc_disc_all_chrc, Addr.le_public,
                            pts_bd_addr, None, None, (SVC.gap, 1),
                            start_wid=73),
                   TestFunc(btp.gattc_disc_all_chrc_find_attrs_rsp,
                            (CHAR.name,), store_attrs=True, start_wid=73),
                   TestFunc(btp.gattc_read_char_val, Addr.le_public,
                            pts_bd_addr, (CHAR.name, 1), start_wid=73),
                   TestFunc(btp.gattc_read_rsp, start_wid=73),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_IDLE_NAMP_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.core_reg_svc_gatts),
                   TestFunc(btp.gatts_add_svc, 0, UUID.gap_svc),
                   TestFunc(btp.gatts_add_char, 0, Prop.read,
                            Perm.read | Perm.write, UUID.device_name),
                   TestFunc(btp.gatts_set_val, 0, '1234'),
                   TestFunc(btp.gatts_start_server),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=78)]),
        # PTS issue #14873
        ZTestCase("GAP", "TC_CONN_NCON_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn),
                   TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_CONN_NCON_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn, start_wid=122),
                   TestFunc(btp.gap_set_gendiscov, start_wid=122),
                   TestFunc(btp.gap_adv_ind_on, start_wid=54)]),
        ZTestCase("GAP", "TC_CONN_NCON_BV_03_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nonconn, start_wid=121),
                   TestFunc(btp.gap_set_limdiscov, start_wid=121),
                   TestFunc(btp.gap_adv_ind_on, start_wid=55)]),
        ZTestCase("GAP", "TC_CONN_UCON_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_nondiscov, start_wid=74),
                   TestFunc(btp.gap_adv_ind_on, start_wid=74)]),
        ZTestCase("GAP", "TC_CONN_UCON_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_gendiscov, start_wid=75),
                   TestFunc(btp.gap_adv_ind_on, start_wid=75)]),
        ZTestCase("GAP", "TC_CONN_UCON_BV_03_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_limdiscov, start_wid=76),
                   TestFunc(btp.gap_adv_ind_on, start_wid=76)]),
        ZTestCase("GAP", "TC_CONN_ACEP_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_CONN_GCEP_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_CONN_GCEP_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_CONN_DCEP_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on, start_wid=21)]),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_03_C",
                  pre_conditions +
                  [TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_04_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=40),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=40),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_CONN_CPUP_BV_05_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=40),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=40),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        # TODO: fails cause of ZEP-381
        # ZTestCase("GAP", "TC_CONN_CPUP_BV_06_C",
        #           [TestFunc(btp.core_reg_svc_gap),
        #            TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
        #                     start_wid=40),
        #            TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
        #                     start_wid=40),
        #            TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
        #                     start_wid=77),
        #            TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
        #                     Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_CONN_TERM_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                            start_wid=77),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_BOND_NBON_BV_01_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, post_wid=118)]),
        ZTestCase("GAP", "TC_BOND_NBON_BV_02_C",
                  pre_conditions +
                  [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                   TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_connected_ev, pts_bd_addr, Addr.le_public,
                            start_wid=78),
                   TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                            start_wid=100),
                   TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                            Addr.le_public, post_wid=118)]),
         ZTestCase("GAP", "TC_BOND_NBON_BV_03_C",
                   pre_conditions +
                   [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                    TestFunc(btp.gap_set_conn, start_wid=91),
                    TestFunc(btp.gap_adv_ind_on, start_wid=91),]),
         ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=108),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108)]),
         # PTS issue #14444
         # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=108),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108)]),
         # wid: 118
         # style: MMI_Style_Ok_Cancel1 0x11041
         # description: Please press ok to disconnect the link.
         #
         # We should click ok, and then wait for gap_disconnected_ev
         # (sth like a PostFunc)
         # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=118)]),
         # PTS issue #14444
         # ZTestCase("GAP", "TC_BOND_BON_BV_01_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, 4),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=108),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108)]),
         # PTS issue #14445
         # ZTestCase("GAP", "TC_BOND_BON_BV_02_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.display_only),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=78),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=78),
         #                 TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
         #                          start_wid=108),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=108)]),
         # PTS issue #14449
         ZTestCase("GAP", "TC_BOND_BON_BV_02_C",
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                  start_wid=78),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=78),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108),
                         TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                  Addr.le_public, post_wid=118)]),
         ZTestCase("GAP", "TC_BOND_BON_BV_03_C",
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on)]),
         # Missing functionality - We respond "None" instead of the passkey
         # ZTestCase("GAP", "TC_BOND_BON_BV_03_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.display_only),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=1002)]),
         # wid: 1001
         # style: MMI_Style_Ok 0x11040
         # description: The Secure ID is 398563. Press OK to continue.
         # ZTestCase("GAP", "TC_BOND_BON_BV_03_C",
         #           cmds=[TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.keyboard_only),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=150)]),
         ZTestCase("GAP", "TC_BOND_BON_BV_04_C",
                   cmds=pre_conditions +
                        [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                  start_wid=78),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=78),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108),
                         TestFunc(btp.gap_disconn, pts_bd_addr,
                                  Addr.le_public, start_wid=77),
                         TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=77)]),
         ZTestCase("GAP", "TC_SEC_AUT_BV_11_C",
                   edit1_wids={139: "0008",
                               1002: (btp.var_store_get_passkey, pts_bd_addr,
                                      Addr.le_public)},
                   cmds=pre_conditions + init_gatt_db +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_set_conn, start_wid=91),
                         TestFunc(btp.gap_adv_ind_on, start_wid=91),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, post_wid=91)]),
         # PTS issue #14452
         # ZTestCase("GAP", "TC_SEC_AUT_BV_12_C",
         #           edit1_wids={139: "0008"},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.display_only),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=40),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=40),
         #                 TestFunc(btp.gattc_exchange_mtu, Addr.le_public,
         #                          pts_bd_addr, start_wid=40)]),
         # PTS issue #14454
         ZTestCase("GAP", "TC_SEC_AUT_BV_13_C",
                   edit1_wids={139: "0008",
                               1002: (btp.var_store_get_passkey, pts_bd_addr,
                                      Addr.le_public)},
                   cmds=pre_conditions + init_gatt_db +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                  start_wid=40),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, start_wid=40),
                         TestFunc(btp.gattc_exchange_mtu, Addr.le_public,
                                  pts_bd_addr, start_wid=40)]),
         ZTestCase("GAP", "TC_SEC_AUT_BV_14_C",
                   edit1_wids={139: "0008",
                               1002: (btp.var_store_get_passkey, pts_bd_addr,
                                      Addr.le_public)},
                   cmds=pre_conditions + init_gatt_db +
                        [TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_set_conn, start_wid=91),
                         TestFunc(btp.gap_adv_ind_on, start_wid=91),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, post_wid=91)]),
         # PTS issue #14474
         # ZTestCase("GAP", "TC_SEC_AUT_BV_16_C",
         #           edit1_wids={140: "000a"},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
         #                 TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
         #                          start_wid=78),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=78),
         #                 TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
         #                          start_wid=44),
         #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=44)]),
         ZTestCase("GAP", "TC_SEC_AUT_BV_18_C",
                   cmds=pre_conditions +
                        [TestFunc(btp.core_reg_svc_gatts),
                         TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, post_wid=91),
                         TestFunc(btp.gattc_read, Addr.le_public,
                                  pts_bd_addr, "0001", start_wid=112),
                         TestFunc(btp.gattc_read_rsp, store_val=False,
                                  start_wid=112),
                         TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                  start_wid=108)]),
         ZTestCase("GAP", "TC_SEC_AUT_BV_20_C",
                   edit1_wids={1002: (btp.var_store_get_passkey, pts_bd_addr,
                                      Addr.le_public)},
                   cmds=pre_conditions +
                        [TestFunc(btp.core_reg_svc_gatts),
                         TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                         TestFunc(btp.gap_set_conn),
                         TestFunc(btp.gap_adv_ind_on),
                         TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                  Addr.le_public, post_wid=91),
                         TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                  Addr.le_public, post_wid=118),
                         # This sleep is workaround, because apparently PTS is
                         # asking for service request before it receives
                         # HCI encryption change event.
                         TestFunc(sleep, 2, start_wid=112),
                         TestFunc(btp.gattc_read, Addr.le_public,
                                  pts_bd_addr, "0001", start_wid=112),
                         TestFunc(btp.gattc_read_rsp, store_val=False,
                                  start_wid=112)]),
        # TODO: Inform about lost bond
        ZTestCase("GAP", "TC_SEC_AUT_BV_22_C",
                  edit1_wids={1002: (btp.var_store_get_passkey, pts_bd_addr,
                                     Addr.le_public)},
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_gatts),
                        TestFunc(btp.gap_set_io_cap, IOCap.display_only),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, post_wid=91),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, post_wid=118),
                        TestFunc(btp.gattc_read, Addr.le_public,
                                 pts_bd_addr, "0001", start_wid=112),
                        TestFunc(btp.gattc_read_rsp, store_val=False,
                                 start_wid=112),
                        TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                                 start_wid=108)]),
         ZTestCase("GAP", "TC_SEC_CSIGN_BV_01_C",
                   pre_conditions +
                   [TestFunc(btp.core_reg_svc_gatts),
                    TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                    TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                             start_wid=78),
                    TestFunc(btp.gap_connected_ev, pts_bd_addr,
                             Addr.le_public, start_wid=78),
                    TestFunc(btp.gap_pair, pts_bd_addr, Addr.le_public,
                             start_wid=108),
                    TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                             Addr.le_public, post_wid=118),
                    TestFunc(btp.gattc_signed_write, Addr.le_public,
                             pts_bd_addr, "0001", "01", start_wid=125),
                    TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                             start_wid=77),
                    TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                             Addr.le_public, start_wid=77)]),
         # Missing functionality - We respond "None" instead of the passkey
         # ZTestCase("GAP", "TC_SEC_CSIGN_BV_02_C",
         #           edit1_wids={1002: btp.var_get_passkey},
         #           cmds=init_gatt_db + \
         #                [TestFunc(btp.core_reg_svc_gap),
         #                 TestFunc(btp.gap_set_io_cap, IOCap.display_only),
         #                 TestFunc(btp.gap_set_conn),
         #                 TestFunc(btp.gap_adv_ind_on),
         #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
         #                          Addr.le_public, start_wid=91),
         #                 TestFunc(btp.gap_passkey_disp_ev, pts_bd_addr,
         #                          Addr.le_public, True, start_wid=1002)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BV_02_C",
                  cmds=init_gatt_db + pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BI_01_C",
                  cmds=init_gatt_db + pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BI_02_C",
                  cmds=init_gatt_db + pre_conditions +
                       [TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        # By now, we cannot remove bonding 
        # wid: 135
        # description: Please have Upper Tester remove the bonding information
        #              of the PTS. Press OK to continue
        # ZTestCase("GAP", "TC_SEC_CSIGN_BI_03_C",
        #           cmds=init_gatt_db + \
        #                [TestFunc(btp.core_reg_svc_gap),
        #                 TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
        #                 TestFunc(btp.gap_set_conn),
        #                 TestFunc(btp.gap_adv_ind_on),
        #                 TestFunc(btp.gap_connected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=91),
        #                 TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
        #                          start_wid=77),
        #                 TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
        #                          Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_SEC_CSIGN_BI_04_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.core_reg_svc_gatts),
                        TestFunc(btp.gatts_add_svc, 0, gatt.UUID.VND16_1),
                        TestFunc(btp.gatts_add_char, 0,
                                 gatt.Prop.read | gatt.Prop.auth_swrite,
                                 gatt.Perm.read | gatt.Perm.write_authn,
                                 gatt.UUID.VND16_3),
                        TestFunc(btp.gatts_set_val, 0, '01'),
                        TestFunc(btp.gatts_start_server),
                        TestFunc(btp.gap_set_io_cap, IOCap.no_input_output),
                        TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=91),
                        TestFunc(btp.gap_disconn, pts_bd_addr, Addr.le_public,
                                 start_wid=77),
                        TestFunc(btp.gap_disconnected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=77)]),
        ZTestCase("GAP", "TC_ADV_BV_01_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_02_C",
                  cmds=init_gatt_db + pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_03_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_set_gendiscov),
                        TestFunc(btp.gap_adv_ind_on)]),
        ZTestCase("GAP", "TC_ADV_BV_04_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_10_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_ADV_BV_11_C",
                  cmds=pre_conditions +
                       [TestFunc(btp.gap_set_conn),
                        TestFunc(btp.gap_adv_ind_on, ad)]),
        ZTestCase("GAP", "TC_GAT_BV_01_C",
                  cmds=init_gatt_db + pre_conditions +
                       [TestFunc(btp.gap_conn, pts_bd_addr, Addr.le_public,
                                 start_wid=78),
                        TestFunc(btp.gap_connected_ev, pts_bd_addr,
                                 Addr.le_public, start_wid=78)]),
        ZTestCase("GAP", "TC_GAT_BV_01_C",
                  no_wid=158,
                  cmds=init_gatt_db + pre_conditions +
                       [TestFunc(btp.gap_set_conn, start_wid=9),
                        TestFunc(btp.gap_adv_ind_on, start_wid=9)]),
        ZTestCase("GAP", "TC_GAT_BV_05_C",
                  cmds=init_gatt_db + pre_conditions +
                      [TestFunc(btp.gap_set_conn, start_wid=91),
                       TestFunc(btp.gap_adv_ind_on, start_wid=91)]),
        ZTestCase("GAP", "TC_GAT_BV_06_C",
                  cmds=init_gatt_db + pre_conditions +
                      [TestFunc(btp.gap_set_conn, start_wid=91),
                       TestFunc(btp.gap_adv_ind_on, start_wid=91)]),
    ]

    return test_cases


def main():
    """Main."""
    import sys
    import ptsprojects.zephyr.iutctl as iutctl

    iutctl.init_stub()

    test_cases_ = test_cases("AB:CD:EF:12:34:56")

    for test_case in test_cases_:
        print
        print test_case

        if test_case.edit1_wids:
            print "edit1_wids: %r" % test_case.edit1_wids

        if test_case.verify_wids:
            print "verify_wids: %r" % test_case.verify_wids

        for index, cmd in enumerate(test_case.cmds):
            print "%d) %s" % (index, cmd)

if __name__ == "__main__":
    main()
