#
# auto-pts - The Bluetooth PTS Automation Framework
#
# Copyright (c) 2026, NXP.
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
import os

from autopts.ptsprojects.stack.common import wait_for_event
from autopts.pybtp import types


class PBAPFolderStructure:
    """PBAP virtual folder structure definition"""

    ROOT = "."

    INTERNAL_TELECOM = "telecom"

    SIM1_TELECOM = "SIM1/telecom"

    PHONEBOOK_TYPES = {
        'pb': {'object': 'pb.vcf', 'folder': 'pb', 'description': '主电话簿'},
        'ich': {'object': 'ich.vcf', 'folder': 'ich', 'description': '来电历史'},
        'och': {'object': 'och.vcf', 'folder': 'och', 'description': '去电历史'},
        'mch': {'object': 'mch.vcf', 'folder': 'mch', 'description': '未接来电'},
        'cch': {'object': 'cch.vcf', 'folder': 'cch', 'description': '组合通话历史'},
        'spd': {'object': 'spd.vcf', 'folder': 'spd', 'description': '快速拨号'},
        'fav': {'object': 'fav.vcf', 'folder': 'fav', 'description': '收藏夹'}
    }

    VALID_FOLDERS = {
        'telecom',
        'SIM1',
        'pb', 'ich', 'och', 'mch', 'cch', 'spd', 'fav'
    }

    VALID_PATH_PATTERNS = [
        'telecom',
        'telecom/pb', 'telecom/ich', 'telecom/och', 'telecom/mch',
        'telecom/cch', 'telecom/spd', 'telecom/fav',
        'SIM1',
        'SIM1/telecom',
        'SIM1/telecom/pb', 'SIM1/telecom/ich', 'SIM1/telecom/och',
        'SIM1/telecom/mch', 'SIM1/telecom/cch', 'SIM1/telecom/spd', 'SIM1/telecom/fav'
    ]

    VALID_TELECOM_PATH_PATTERNS = [
        'telecom/pb', 'telecom/ich', 'telecom/och', 'telecom/mch',
        'telecom/cch', 'telecom/spd', 'telecom/fav',
        'SIM1/telecom/pb', 'SIM1/telecom/ich', 'SIM1/telecom/och',
        'SIM1/telecom/mch', 'SIM1/telecom/cch', 'SIM1/telecom/spd', 'SIM1/telecom/fav',
        'pb', 'ich', 'och', 'mch', 'cch', 'spd', 'fav'
    ]

    PROPERTY_SELECTOR_MAP = {
        'VERSION': types.PBAPPropertySelector.VERSION,
        'FN': types.PBAPPropertySelector.FN,
        'N': types.PBAPPropertySelector.N,
        'PHOTO': types.PBAPPropertySelector.PHOTO,
        'BDAY': types.PBAPPropertySelector.BDAY,
        'ADR': types.PBAPPropertySelector.ADR,
        'LABEL': types.PBAPPropertySelector.LABEL,
        'TEL': types.PBAPPropertySelector.TEL,
        'EMAIL': types.PBAPPropertySelector.EMAIL,
        'MAILER': types.PBAPPropertySelector.MAILER,
        'TZ': types.PBAPPropertySelector.TZ,
        'GEO': types.PBAPPropertySelector.GEO,
        'TITLE': types.PBAPPropertySelector.TITLE,
        'ROLE': types.PBAPPropertySelector.ROLE,
        'LOGO': types.PBAPPropertySelector.LOGO,
        'AGENT': types.PBAPPropertySelector.AGENT,
        'ORG': types.PBAPPropertySelector.ORG,
        'NOTE': types.PBAPPropertySelector.NOTE,
        'REV': types.PBAPPropertySelector.REV,
        'SOUND': types.PBAPPropertySelector.SOUND,
        'URL': types.PBAPPropertySelector.URL,
        'UID': types.PBAPPropertySelector.UID,
        'KEY': types.PBAPPropertySelector.KEY,
        'NICKNAME': types.PBAPPropertySelector.NICKNAME,
        'CATEGORIES': types.PBAPPropertySelector.CATEGORIES,
        'PRODID': types.PBAPPropertySelector.PRODID,
        'CLASS': types.PBAPPropertySelector.CLASS,
        'SORT_STRING': types.PBAPPropertySelector.SORT_STRING,
        'SORT-STRING': types.PBAPPropertySelector.SORT_STRING,
        'X-IRMC-CALL-DATETIME': types.PBAPPropertySelector.X_IRMC_CALL_DATETIME,
        'X-BT-SPEEDDIALKEY': types.PBAPPropertySelector.X_BT_SPEEDDIALKEY,
        'X-BT-UCI': types.PBAPPropertySelector.X_BT_UCI,
        'X-BT-UID': types.PBAPPropertySelector.X_BT_UID,
    }

    SFV_TRACKED_PROPERTIES = {
        'N',
        'FN',
        'TEL',
        'EMAIL',
        'MAILER',
        'ADR',
        'X-BT-UCI',
    }

    MOCK_PHONEBOOK_DATA = """BEGIN:VCARD
VERSION:3.0
N:PTS.;;
FN:PTS
TEL;TYPE=CELL:+1234567890
TEL;TYPE=HOME:+0987654321
EMAIL;TYPE=INTERNET:PTS@example.com
ADR;TYPE=HOME:;;123 Main St;City;State;12345;Country
ORG:Tech Corp
TITLE:Software Engineer
BDAY:1985-06-15
NOTE:Important client contact
X-BT-SPEEDDIALKEY:231232131
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Doe;Jane;Ms.;;
FN:Jane Doe
TEL;TYPE=WORK:+1122334455
TEL;TYPE=CELL:+1122334456
EMAIL;TYPE=INTERNET:jane.doe@example.com
EMAIL;TYPE=WORK:jane.doe@company.com
ADR;TYPE=WORK:;;456 Business Ave;Metropolis;State;54321;Country
ORG:Business Solutions Inc
TITLE:Project Manager
BDAY:1990-03-22
URL:https://www.janedoe.com
NOTE:Team lead for project Alpha
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Johnson;Michael;Dr.;;Jr.
FN:Dr. Michael Johnson Jr.
TEL;TYPE=CELL:+2223334444
TEL;TYPE=FAX:+2223334445
EMAIL;TYPE=INTERNET:m.johnson@hospital.com
ADR;TYPE=WORK:;;789 Medical Center;Healthcare City;State;67890;Country
ORG:City Hospital
TITLE:Chief Surgeon
BDAY:1978-11-30
NOTE:Emergency contact
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Williams;Sarah;;;
FN:Sarah Williams
TEL;TYPE=CELL:+3334445555
TEL;TYPE=HOME:+3334445556
EMAIL;TYPE=INTERNET:sarah.w@email.com
ADR;TYPE=HOME:;;321 Oak Street;Hometown;State;11111;Country
ORG:Freelance Designer
TITLE:Graphic Designer
BDAY:1992-08-10
URL:https://sarahdesigns.com
NOTE:Portfolio available online
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Brown;Robert;Mr.;;
FN:Robert Brown
TEL;TYPE=WORK:+4445556666
TEL;TYPE=CELL:+4445556667
TEL;TYPE=HOME:+4445556668
EMAIL;TYPE=INTERNET:robert.brown@finance.com
EMAIL;TYPE=WORK:r.brown@investment.com
ADR;TYPE=WORK:;;555 Wall Street;Financial District;NY;10005;USA
ORG:Investment Bank Corp
TITLE:Financial Advisor
BDAY:1980-01-25
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Zhang;Wei;;;
FN:Wei Zhang
TEL;TYPE=CELL:+8613800138000
TEL;TYPE=WORK:+861012345678
EMAIL;TYPE=INTERNET:wei.zhang@example.cn
ADR;TYPE=WORK:;;88 Changan Ave;Beijing;;100000;China
ORG:Beijing Tech Co
TITLE:Senior Developer
BDAY:1987-09-15
NOTE:Speaks English and Chinese
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Li;Ming;;;
FN:Ming Li
TEL;TYPE=CELL:+8613900139000
TEL;TYPE=HOME:+862112345678
EMAIL;TYPE=INTERNET:ming.li@example.cn
ADR;TYPE=HOME:;;99 Nanjing Rd;Shanghai;;200000;China
ORG:China Mobile
TITLE:Network Engineer
BDAY:1985-12-05
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Wang;Fang;;;
FN:PTS_PH
TEL;TYPE=CELL:+8613700137000
TEL;TYPE=WORK:+862087654321
EMAIL;TYPE=INTERNET:fang.wang@example.cn
EMAIL;TYPE=WORK:f.wang@bank.cn
ADR;TYPE=WORK:;;66 Finance St;Guangzhou;;510000;China
ORG:Shanghai Bank
TITLE:Branch Manager
BDAY:1988-05-20
NOTE:VIP customer service
PHOTO:jhdksahjkjhrfiuashdkjsahdaksjd
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Garcia;Maria;;;
FN:PTS_8
TEL;TYPE=CELL:+5551234567
TEL;TYPE=HOME:+5559876543
EMAIL;TYPE=INTERNET:maria.garcia@example.es
ADR;TYPE=HOME:;;77 Plaza Mayor;Madrid;;28001;Spain
ORG:Marketing Solutions
TITLE:Marketing Director
BDAY:1991-07-18
URL:https://mariagarcia.es
X-BT-UCI:12312412431231241243
END:VCARD
BEGIN:VCARD
VERSION:3.0
N:Mueller;Hans;;;
FN:PTS_9
TEL;TYPE=CELL:+491234567890
TEL;TYPE=WORK:+4989123456
EMAIL;TYPE=INTERNET:hans.mueller@example.de
ADR;TYPE=WORK:;;88 Hauptstrasse;Munich;;80331;Germany
ORG:Auto Engineering GmbH
TITLE:Mechanical Engineer
BDAY:1983-03-12
NOTE:Automotive specialist
X-BT-UID:F1984D696B612048C3A46B6B696E6560
END:VCARD"""

    def __init__(self):
        """Initialize with current path set to root directory"""
        self.current_path = self.ROOT
        self.primary_folder_version = bytearray(os.urandom(16).hex(), 'utf-8')
        self.secondary_folder_version = bytearray(os.urandom(16).hex(), 'utf-8')
        self.database_identifier = bytearray(os.urandom(16).hex(), 'utf-8')

    def reset_dbi(self):
        """Reset database identifier to a new random value"""
        self.database_identifier = bytearray(os.urandom(16).hex(), 'utf-8')

    def reset_pfv(self):
        self.primary_folder_version = bytearray(os.urandom(16).hex(), 'utf-8')

    def reset_sfv(self):
        self.secondary_folder_version = bytearray(os.urandom(16).hex(), 'utf-8')

    def _update_folder_versions(self, modified_properties=None, is_entry_change=False):
        """
        Update folder version counters based on the type of change
        According to PBAP spec:
        - PFV increments on ANY property change, insertion, or removal
        - SFV increments ONLY on changes to N, FN, TEL, EMAIL, MAILER, ADR, X-BT-UCI
          or on insertion/removal of entries
        :param modified_properties: Set of property names that were modified (uppercase)
        :param is_entry_change: True if this is an entry insertion or removal
        """
        if is_entry_change:
            # Entry insertion or removal: update both PFV and SFV
            self.reset_pfv()
            self.reset_sfv()
            logging.debug("Folder versions updated: entry insertion/removal")
            return

        if modified_properties is None:
            modified_properties = set()

        # Always update PFV for any property change
        if modified_properties:
            self.reset_pfv()

            # Check if any modified property is tracked by SFV
            sfv_properties_modified = modified_properties & self.SFV_TRACKED_PROPERTIES
            if sfv_properties_modified:
                self.reset_sfv()
                logging.debug(f"Folder versions updated: PFV and SFV (properties: {sfv_properties_modified})")
            else:
                logging.debug(f"Folder versions updated: PFV only (properties: {modified_properties})")

    def _extract_property_name(self, property_name):
        """
        Extract base property name from property string
        
        :param property_name: Property name (may include parameters)
        :return: Base property name in uppercase
        """
        if isinstance(property_name, str):
            # Handle cases like "TEL;TYPE=CELL" -> "TEL"
            if ';' in property_name:
                return property_name.split(';')[0].upper()
            return property_name.upper()
        return str(property_name).upper()

    def _add_root_prefix(self, path):
        """
        Add root directory prefix to path
        :param path: Input path
        :return: Path with root directory prefix
        """
        if not path or path == ".":
            return self.ROOT

        path = path.lstrip('.').lstrip('/')

        if not path:
            return self.ROOT

        return f"./{path}"

    def _validate_folder_name(self, folder_name):
        """
        Validate if folder name is valid
        :param folder_name: Folder name
        :return: True if valid, otherwise False
        """
        if not folder_name:
            return False

        if '/' in folder_name or '\\' in folder_name:
            return False

        if not folder_name.strip():
            return False

        if folder_name not in self.VALID_FOLDERS:
            return False

        return True

    def validate_path(self, path):
        """
        Validate if path is valid
        :param path: Path string
        :return: True if valid, otherwise False
        """
        if not path:
            return False

        clean_path = path.lstrip('.').lstrip('/')

        if not clean_path:
            return False

        if clean_path not in self.VALID_PATH_PATTERNS:
            return False

        return True

    def _is_valid_navigation(self, current_path, folder_name):
        """
        Validate if navigation from current path to specified folder is valid
        :param current_path: Current path
        :param folder_name: Folder name to navigate to
        :return: True if valid, otherwise False
        """
        if current_path == self.ROOT or current_path == ".":
            target_path = folder_name
        else:
            clean_current = current_path.lstrip('.').lstrip('/')
            target_path = f"{clean_current}/{folder_name}" if clean_current else folder_name

        return target_path in self.VALID_PATH_PATTERNS

    def _get_available_subfolders(self, current_path):
        """
        Get available subfolders under current path
        :param current_path: Current path
        :return: Set of available subfolders
        """
        available = set()

        if current_path == self.ROOT or current_path == ".":
            current_clean = ""
        else:
            current_clean = current_path.lstrip('.').lstrip('/')

        for valid_path in self.VALID_PATH_PATTERNS:
            if current_clean:
                if valid_path.startswith(current_clean + '/'):
                    remaining = valid_path[len(current_clean) + 1:]
                    next_folder = remaining.split('/')[0]
                    available.add(next_folder)
            else:
                next_folder = valid_path.split('/')[0]
                available.add(next_folder)

        return available

    def set_path_to_root(self):
        """Set path to root directory"""
        self.current_path = self.ROOT
        return self.current_path

    def set_path(self, path):
        """
        Set path to specified directory
        :param path: Target path, such as "telecom/pb" or "./telecom/pb" or "."
        :return: Path with root directory prefix, such as "./telecom/pb", returns None if path is invalid
        """
        if path is None:
            return None

        if not isinstance(path, str):
            return None

        if path == "." or path == "./":
            self.current_path = self.ROOT
            return self.current_path

        clean_path = path.lstrip('.').lstrip('/')

        if not clean_path:
            self.current_path = self.ROOT
            return self.current_path

        if not self.validate_path(path):
            return None

        self.current_path = clean_path
        return self._add_root_prefix(self.current_path)

    def navigate_up(self):
        """Navigate up one level"""
        if self.current_path == self.ROOT or self.current_path == ".":
            return self.current_path

        path = self.current_path.lstrip('.').lstrip('/')
        parts = path.split('/')

        if len(parts) > 1:
            self.current_path = '/'.join(parts[:-1])
        else:
            self.current_path = self.ROOT

        return self._add_root_prefix(self.current_path)

    def navigate_down(self, folder_name):
        """
        Navigate down to subdirectory
        :param folder_name: Subdirectory name
        :return: Path with root directory prefix, returns None if folder name is invalid
        """
        if folder_name is None:
            return None

        if not isinstance(folder_name, str):
            return None

        if not self._validate_folder_name(folder_name):
            return None

        if not self._is_valid_navigation(self.current_path, folder_name):
            return None

        if self.current_path == self.ROOT or self.current_path == ".":
            self.current_path = folder_name
        else:
            path = self.current_path.lstrip('.').lstrip('/')
            self.current_path = f"{path}/{folder_name}" if path else folder_name

        return self._add_root_prefix(self.current_path)

    def get_current_path(self):
        """Get current path (with root directory prefix)"""
        return self._add_root_prefix(self.current_path)

    def is_valid_combined_path(self, path):
        """
        Check if the current path combined with the specified path is valid
        :param path: Path to add (can be a single folder name or complete path)
        :return: True if valid, otherwise False

        Example:
            # Assume current path is "telecom"
            folder.current_path = "telecom"
            folder.is_valid_combined_path("pb")  # True, result is "telecom/pb"
            folder.is_valid_combined_path("invalid")  # False

            # Assume current path is "."
            folder.current_path = "."
            folder.is_valid_combined_path("telecom")  # True
            folder.is_valid_combined_path("SIM1")  # True
        """
        if not path:
            return False

        # If path is absolute (contains /), validate directly
        if '/' in path:
            # Clean the path
            clean_path = path.lstrip('.').lstrip('/')
            if not clean_path:
                return True  # Root directory is valid

            # Directly validate if the complete path is valid
            return clean_path in self.VALID_PATH_PATTERNS

        # For single folder name, use existing _is_valid_navigation function
        return self._is_valid_navigation(self.current_path, path)

    def _parse_vcard_list(self, vcard_text):
        """
        Parse vCard list, return list of individual vCards
        :param vcard_text: Text containing multiple vCards
        :return: List of vCard strings
        """
        vcards = []
        current_vcard = []
        in_vcard = False

        for line in vcard_text.split('\n'):
            line = line.strip()
            if line == 'BEGIN:VCARD':
                in_vcard = True
                current_vcard = [line]
            elif line == 'END:VCARD':
                current_vcard.append(line)
                vcards.append('\n'.join(current_vcard))
                current_vcard = []
                in_vcard = False
            elif in_vcard:
                current_vcard.append(line)

        return vcards

    def is_in_telecom_path(self):
        """
        Check if current path is under 'telecom/...' or 'SIM1/telecom/...'
        :return: bool - True if in telecom path, False otherwise
        """
        clean_path = self.current_path.lstrip('.').lstrip('/')

        if not clean_path or clean_path == ".":
            return False

        is_internal = clean_path == 'telecom' or clean_path.startswith('telecom/')

        is_sim1 = clean_path == 'SIM1/telecom' or clean_path.startswith('SIM1/telecom/')

        return is_internal or is_sim1

    def _parse_vcard_to_dict(self, vcard_text):
        """
        Parse single vCard text to dictionary
        :param vcard_text: Single vCard text
        :return: vCard property dictionary
        """
        vcard_dict = {}

        for line in vcard_text.split('\n'):
            line = line.strip()
            if line and ':' in line and line not in ['BEGIN:VCARD', 'END:VCARD']:
                if ';' in line.split(':', 1)[0]:
                    key_part, value = line.split(':', 1)
                    key = key_part.split(';')[0]
                else:
                    key, value = line.split(':', 1)

                if key in vcard_dict:
                    if isinstance(vcard_dict[key], list):
                        vcard_dict[key].append(value)
                    else:
                        vcard_dict[key] = [vcard_dict[key], value]
                else:
                    vcard_dict[key] = value

        return vcard_dict

    def _has_selected_properties(self, vcard_dict, vcard_selector, vcard_selector_operator):
        """
        Check if vCard matches the vCardSelector criteria based on the operator
        :param vcard_dict: vCard property dictionary
        :param vcard_selector: 64-bit unsigned integer bitmask
        :param vcard_selector_operator: 0 = OR (any property), 1 = AND (all properties)
        :return: True if vCard matches the selector criteria
        """
        if vcard_selector is None or vcard_selector == 0:
            # No selector specified, include all vCards
            return True

        # Build list of selected properties (bits that are set in vcard_selector)
        selected_properties = []
        for prop_name, prop_bit in self.PROPERTY_SELECTOR_MAP.items():
            if (vcard_selector & prop_bit) != 0:
                selected_properties.append(prop_name)
        logging.info(f'selected_properties = {selected_properties}')
        if not selected_properties:
            # No properties selected, include all vCards
            return True

        # Check which selected properties exist in this vCard
        matches = []
        for prop_name in selected_properties:
            # Check if this property exists in the vCard
            has_property = prop_name in vcard_dict
            matches.append(has_property)

        # Apply operator logic
        if vcard_selector_operator == 0:  # OR logic
            # vCard must have at least ONE of the selected properties
            return any(matches)
        else:  # AND logic (vcard_selector_operator == 1)
            # vCard must have ALL of the selected properties
            return all(matches)

    def _is_property_selected(self, property_name, vcard_selector):
        """
        Check if a vCard property is selected in the vCardSelector bitmask
        :param property_name: vCard property name (e.g., 'FN', 'TEL', 'EMAIL')
        :param vcard_selector: 64-bit unsigned integer bitmask
        :return: True if property is selected, False otherwise
        """
        if vcard_selector is None or vcard_selector == 0:
            # If no selector specified, include all properties
            return True

        property_bit = self.PROPERTY_SELECTOR_MAP.get(property_name)
        if property_bit is None:
            # Unknown property, include it by default
            return True

        # Check if the bit is set
        return (vcard_selector & property_bit) != 0

    def _filter_vcard_by_selector(self, vcard_text, vcard_selector):
        """
        Filter vCard properties based on vCardSelector bitmask
        :param vcard_text: Complete vCard text
        :param vcard_selector: 64-bit unsigned integer bitmask (0 means return all)
        :return: Filtered vCard text with only selected properties
        """
        if vcard_selector is None or vcard_selector == 0:
            # No filtering, return complete vCard
            return vcard_text

        filtered_lines = []

        for line in vcard_text.split('\n'):
            line_stripped = line.strip()

            # Always include BEGIN and END
            if line_stripped in ['BEGIN:VCARD', 'END:VCARD']:
                filtered_lines.append(line_stripped)
                continue

            # Parse property name
            if ':' in line_stripped:
                if ';' in line_stripped.split(':', 1)[0]:
                    property_name = line_stripped.split(';')[0]
                else:
                    property_name = line_stripped.split(':')[0]

                # Check if this property is selected
                if self._is_property_selected(property_name, vcard_selector):
                    filtered_lines.append(line_stripped)

        return '\n'.join(filtered_lines)

    def pull_phonebook(self, max_list_count=65535, list_start_offset=0,
                      property_selector=None, vcard_selector=None,
                      vcard_selector_operator=0, format_type=0x01):
        """
        PullPhoneBook - Get phonebook content (collection of multiple complete vCards)
        Each vCard entry includes BEGIN:VCARD, all properties, and END:VCARD

        :param max_list_count: Maximum number of entries to return (default 65535)
        :param list_start_offset: Start offset (default 0)
        :param property_selector: 64-bit unsigned integer bitmask for property filtering (0 or None = all properties)
                                 Controls which properties are included in returned vCards
                                 Mandatory properties (VERSION, N, FN, TEL for vCard 3.0) are always returned
                                 Use types.PBAPPropertySelector constants
                                 Example: types.PBAPPropertySelector.FN | types.PBAPPropertySelector.TEL
        :param vcard_selector: 64-bit unsigned integer bitmask for vCard filtering (0 or None = all vCards)
                              Controls which vCards are returned based on property existence
                              Use types.PBAPPropertySelector constants
                              Example: types.PBAPPropertySelector.EMAIL (only return vCards with email)
        :param vcard_selector_operator: Determines logic when multiple bits are set in vCardSelector
                                        0 = OR logic (default) - vCard must have at least ONE selected property with value
                                        1 = AND logic - vCard must have ALL selected properties with values
        :param format_type: vCard format version
                           0x00 = vCard 2.1
                           0x01 = vCard 3.0 (default)
        :return: Dictionary containing phonebook metadata and complete vCard entries

        Example:
            # Get all vCards, but only return FN and TEL properties
            result = pull_phonebook(property_selector=types.PBAPPropertySelector.FN | types.PBAPPropertySelector.TEL)

            # Get only vCards that have EMAIL, return all properties
            result = pull_phonebook(vcard_selector=types.PBAPPropertySelector.EMAIL)

            # Get vCards with EMAIL, return only FN, TEL, EMAIL properties
            result = pull_phonebook(
                property_selector=(
                    types.PBAPPropertySelector.FN |
                    types.PBAPPropertySelector.TEL |
                    types.PBAPPropertySelector.EMAIL
                ),
                vcard_selector=types.PBAPPropertySelector.EMAIL
            )

            # Get vCards that have both EMAIL AND PHOTO, return all properties
            result = pull_phonebook(
                vcard_selector=types.PBAPPropertySelector.EMAIL | types.PBAPPropertySelector.PHOTO,
                vcard_selector_operator=1  # AND logic
            )

            # Get vCards in vCard 2.1 format
            result = pull_phonebook(format_type=0x00)
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        # Step 1: Filter vCards based on vCardSelector and vCardSelectorOperator
        # This determines WHICH vCards to return based on property existence
        filtered_vcards = []
        for vcard_text in all_vcards:
            vcard_dict = self._parse_vcard_to_dict(vcard_text)

            # Check if this vCard matches the selector criteria
            if self._has_selected_properties(vcard_dict, vcard_selector, vcard_selector_operator):
                filtered_vcards.append(vcard_text)

        all_vcards = filtered_vcards
        total_count = len(all_vcards)

        if max_list_count == 0:
            return {
                'phonebook_size': total_count,
                'returned_count': 0,
                'content': ''
            }

        # Step 2: Apply offset and count limits
        end_offset = min(list_start_offset + max_list_count, total_count)
        selected_vcards = all_vcards[list_start_offset:end_offset]

        # Step 3: Filter properties in each vCard based on PropertySelector
        # This determines WHICH properties to include in each returned vCard
        result_vcards = []
        for vcard_text in selected_vcards:
            # Apply property filtering if specified
            if property_selector is not None and property_selector != 0:
                filtered_vcard = self._filter_vcard_by_property_selector(
                    vcard_text, property_selector, format_type
                )
            else:
                filtered_vcard = vcard_text

            # Apply format conversion if needed
            if format_type == 0x00:
                # Convert to vCard 2.1
                filtered_vcard = self._convert_vcard_to_21(filtered_vcard)

            result_vcards.append(filtered_vcard)

        result_content = '\n'.join(result_vcards)

        return {
            'phonebook_size': total_count,
            'returned_count': len(result_vcards),
            'content': result_content
        }

    def _filter_vcard_by_property_selector(self, vcard_text, property_selector, format_type=0x01):
        """
        Filter vCard properties based on PropertySelector bitmask
        Follows PBAP specification rules:
        - Mandatory properties for vCard 3.0: VERSION, N, FN, TEL (always returned)
        - Mandatory properties for vCard 2.1: VERSION, N, TEL (always returned)
        - If TEL has no value, an empty TEL property is included
        - Only requested properties (that are supported) are returned
        - All instances of multi-value properties are returned

        :param vcard_text: Complete vCard text
        :param property_selector: 64-bit unsigned integer bitmask (0 means return all)
        :param format_type: vCard format version (0x00 = vCard 2.1, 0x01 = vCard 3.0)
        :return: Filtered vCard text with mandatory and selected properties
        """
        if property_selector is None or property_selector == 0:
            # No filtering, return complete vCard
            return vcard_text

        # Define mandatory properties based on format
        if format_type == 0x00:
            # vCard 2.1: VERSION, N, TEL
            mandatory_properties = ['VERSION', 'N', 'TEL']
        else:
            # vCard 3.0: VERSION, N, FN, TEL
            mandatory_properties = ['VERSION', 'N', 'FN', 'TEL']

        filtered_lines = []
        has_tel = False  # Track if we found any TEL property

        for line in vcard_text.split('\n'):
            line_stripped = line.strip()

            # Always include BEGIN and END
            if line_stripped in ['BEGIN:VCARD', 'END:VCARD']:
                filtered_lines.append(line_stripped)
                continue

            # Parse property name
            if ':' in line_stripped:
                if ';' in line_stripped.split(':', 1)[0]:
                    property_name = line_stripped.split(';')[0]
                else:
                    property_name = line_stripped.split(':')[0]

                # Check if this is a mandatory property
                is_mandatory = property_name in mandatory_properties

                # Check if this property is selected
                is_selected = self._is_property_selected(property_name, property_selector)

                # Include if mandatory OR selected
                if is_mandatory or is_selected:
                    filtered_lines.append(line_stripped)
                    if property_name == 'TEL':
                        has_tel = True

        # PBAP requirement: If TEL property has no value, include empty TEL
        # Insert empty TEL before END:VCARD if no TEL was found
        if not has_tel:
            # Find END:VCARD and insert empty TEL before it
            end_index = -1
            for i, line in enumerate(filtered_lines):
                if line == 'END:VCARD':
                    end_index = i
                    break

            if end_index != -1:
                filtered_lines.insert(end_index, 'TEL:')

        return '\n'.join(filtered_lines)

    def pull_vcard_listing(self, max_list_count=65535, list_start_offset=0,
                          search_value=None, search_attribute=None, order=None,
                          vcard_selector=None, vcard_selector_operator=0):
        """
        PullvCardListing - Get vCard list (XML format)

        :param max_list_count: Maximum number of entries to return
        :param list_start_offset: Start offset
        :param search_value: Search value
        :param search_attribute: Search attribute (such as 'name', 'number', 'sound')
        :param order: Sort order ('indexed', 'alphanumeric', 'phonetic')
        :param vcard_selector: 64-bit unsigned integer bitmask for property selection (0 or None = all properties)
                               Use types.PBAPPropertySelector constants
        :param vcard_selector_operator: Determines logic when multiple bits are set in vCardSelector
                                        0 = OR logic (default) - vCard must have at least ONE selected property
                                        1 = AND logic - vCard must have ALL selected properties
        :return: vCard list in XML format

        Note: vCardSelector filters which vCards appear in the listing based on their properties.
              The actual property filtering is applied when retrieving individual vCards via PullvCardEntry.
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        listing_items = []
        for index, vcard_text in enumerate(all_vcards):
            vcard_dict = self._parse_vcard_to_dict(vcard_text)

            # Filter vCards based on vCardSelector and vCardSelectorOperator
            if not self._has_selected_properties(vcard_dict, vcard_selector, vcard_selector_operator):
                continue

            name = vcard_dict.get('FN', '')
            if not name and 'N' in vcard_dict:
                n_parts = vcard_dict['N'].split(';')
                if len(n_parts) >= 2:
                    name = f"{n_parts[1]} {n_parts[0]}".strip()
                else:
                    name = vcard_dict['N']

            # Apply search filtering
            if search_value and search_attribute:
                if search_attribute.lower() == 'name':
                    if search_value.lower() not in name.lower():
                        continue
                elif search_attribute.lower() == 'number':
                    tel = vcard_dict.get('TEL', '')
                    if isinstance(tel, list):
                        tel = ' '.join(tel)
                    if search_value not in tel:
                        continue

            listing_items.append({
                'handle': f"{index}.vcf",
                'name': name
            })

        if order == 'alphanumeric':
            listing_items.sort(key=lambda x: x['name'].lower())
        elif order == 'indexed':
            pass

        total_count = len(listing_items)
        end_offset = min(list_start_offset + max_list_count, total_count)
        selected_items = listing_items[list_start_offset:end_offset]

        xml_lines = [
            '<?xml version="1.0"?>',
            '<!DOCTYPE vcard-listing SYSTEM "vcard-listing.dtd">',
            '<vCard-listing version="1.0">'
        ]

        for item in selected_items:
            name_escaped = item['name'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            xml_lines.append(f'  <card handle="{item["handle"]}" name="{name_escaped}"/>')

        xml_lines.append('</vCard-listing>')

        xml_content = '\n'.join(xml_lines)

        return {
            'phonebook_size': total_count,
            'returned_count': len(selected_items),
            'content': xml_content
        }

    def pull_vcard_entry(self, handle, propertyselector=None, format_type=0x01):
        """
        PullvCardEntry - Get single vCard entry with property filtering and format selection
        Returns a complete vCard including BEGIN:VCARD, all properties, and END:VCARD

        :param handle: vCard handle, can be:
                       - Index format: "0.vcf", "5.vcf", or just "0", "5"
                       - X-BT-UID format: "X-BT-UID:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" (32 hex chars)
        :param propertyselector: 64-bit unsigned integer bitmask for property selection (0 or None = all properties)
                               Use types.PBAPPropertySelector constants
                               Example: types.PBAPPropertySelector.FN | types.PBAPPropertySelector.TEL
        :param format_type: vCard format version
                           0x00 = vCard 2.1
                           0x01 = vCard 3.0 (default)
        :return: Dictionary with success status and complete vCard data

        Example:
            # Get vCard by index with property filtering
            selector = types.PBAPPropertySelector.FN | types.PBAPPropertySelector.TEL
            result = pull_vcard_entry("0.vcf", propertyselector=selector, format_type=0x01)

            # Get vCard by X-BT-UID
            result = pull_vcard_entry("X-BT-UID:F1984D696B612048C3A46B6B696E656E", format_type=0x00)
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        vcard_text = None
        index = -1

        # Check if handle is X-BT-UID format
        if isinstance(handle, str) and handle.upper().startswith('X-BT-UID:'):
            uid = handle[9:].strip()  # Remove "X-BT-UID:" prefix

            # Validate UID format (should be 32 hex characters)
            if len(uid) != 32 or not all(c in '0123456789ABCDEFabcdef' for c in uid):
                return {
                    'success': False,
                    'error': f'Invalid X-BT-UID format: {handle} (expected 32 hex characters)',
                    'content': None
                }

            # Search for vCard with matching X-BT-UID
            for idx, vcard in enumerate(all_vcards):
                vcard_dict = self._parse_vcard_to_dict(vcard)
                vcard_uid = vcard_dict.get('X-BT-UID', '').strip()

                if vcard_uid.upper() == uid.upper():
                    vcard_text = vcard
                    index = idx
                    break

            if vcard_text is None:
                return {
                    'success': False,
                    'error': f'X-BT-UID not found: {uid}',
                    'content': None
                }
        else:
            # Handle index format (e.g., "0.vcf" or "5")
            try:
                if isinstance(handle, str) and handle.endswith('.vcf'):
                    index = int(handle.replace('.vcf', ''))
                else:
                    index = int(handle)
            except ValueError:
                return {
                    'success': False,
                    'error': f'Invalid handle format: {handle}',
                    'content': None
                }

            if index < 0 or index >= len(all_vcards):
                return {
                    'success': False,
                    'error': f'Handle {handle} not found (valid range: 0-{len(all_vcards) - 1})',
                    'content': None
                }

            vcard_text = all_vcards[index]

        # Apply property selector filtering
        if propertyselector is not None and propertyselector != 0:
            vcard_text = self._filter_vcard_by_selector(vcard_text, propertyselector)

        # Apply format conversion if needed
        if format_type == 0x00:
            # Convert to vCard 2.1 format
            vcard_text = self._convert_vcard_to_21(vcard_text)
        # else: format_type == 0x01 or default, keep vCard 3.0 format

        return {
            'success': True,
            'error': None,
            'content': vcard_text
        }

    def _convert_vcard_to_21(self, vcard_text):
        """
        Convert vCard 3.0 format to vCard 2.1 format
        :param vcard_text: vCard 3.0 text
        :return: vCard 2.1 text

        Main differences between vCard 2.1 and 3.0:
        - VERSION: 3.0 -> 2.1
        - Encoding: vCard 2.1 uses ENCODING=QUOTED-PRINTABLE or BASE64
        - Charset: vCard 2.1 may need CHARSET parameter
        - Type parameters: TYPE=CELL -> CELL (without TYPE=)
        """
        lines = []

        for line in vcard_text.split('\n'):
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # Convert VERSION
            if line_stripped == 'VERSION:3.0':
                lines.append('VERSION:2.1')
                continue

            # Convert TYPE parameters (e.g., TEL;TYPE=CELL -> TEL;CELL)
            if ';TYPE=' in line_stripped:
                # Handle multiple TYPE parameters
                parts = line_stripped.split(':')
                if len(parts) >= 2:
                    property_part = parts[0]
                    value_part = ':'.join(parts[1:])

                    # Replace TYPE=XXX with XXX
                    property_part = property_part.replace(';TYPE=', ';')

                    line_stripped = f"{property_part}:{value_part}"

            lines.append(line_stripped)

        return '\n'.join(lines)

    def remove_vcard_property(self, name, property_name):
        """
        Remove a specific property from a vCard entry by name

        :param name: Full name (FN field) of the vCard
        :param property_name: Property name to remove (e.g., 'TEL', 'EMAIL', 'PHOTO', 'X-BT-UID')
                             Can be a single property or a list of properties
        :return: Dictionary with success status and result message

        Example:
            # Remove TEL property from vCard
            result = remove_vcard_property("John Smith", "TEL")

            # Remove multiple properties
            result = remove_vcard_property("Jane Doe", ["EMAIL", "PHOTO"])
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        vcard_index = -1

        # Search for vCard with matching name
        for idx, vcard in enumerate(all_vcards):
            vcard_dict = self._parse_vcard_to_dict(vcard)
            vcard_name = vcard_dict.get('FN', '').strip()

            if vcard_name == name:
                vcard_index = idx
                break

        if vcard_index == -1:
            return {
                'success': False,
                'error': f'vCard with name "{name}" not found'
            }

        # Get the vCard text
        vcard_text = all_vcards[vcard_index]

        # Convert property_name to list if it's a string
        if isinstance(property_name, str):
            properties_to_remove = [property_name.upper()]
        else:
            properties_to_remove = [prop.upper() for prop in property_name]

        # Remove the specified properties
        modified_vcard = self._remove_properties_from_vcard(vcard_text, properties_to_remove)

        # Update the vCard in MOCK_PHONEBOOK_DATA
        all_vcards[vcard_index] = modified_vcard
        self.MOCK_PHONEBOOK_DATA = '\n'.join(all_vcards)

        # Auto-update folder versions based on removed properties
        self._update_folder_versions(modified_properties=set(properties_to_remove))

        return {
            'success': True,
            'message': f'Successfully removed properties {properties_to_remove} from vCard: {name}',
            'modified_vcard': modified_vcard
        }

    def _remove_properties_from_vcard(self, vcard_text, properties_to_remove):
        """
        Remove specified properties from a vCard text

        :param vcard_text: Complete vCard text
        :param properties_to_remove: List of property names to remove (uppercase)
        :return: Modified vCard text with properties removed
        """
        lines = []
        skip_line = False

        for line in vcard_text.split('\n'):
            line_stripped = line.strip()

            # Always keep BEGIN and END
            if line_stripped in ['BEGIN:VCARD', 'END:VCARD']:
                lines.append(line_stripped)
                continue

            # Skip empty lines
            if not line_stripped:
                continue

            # Parse property name
            if ':' in line_stripped:
                if ';' in line_stripped.split(':', 1)[0]:
                    property_name = line_stripped.split(';')[0].upper()
                else:
                    property_name = line_stripped.split(':')[0].upper()

                # Check if this property should be removed
                if property_name in properties_to_remove:
                    logging.debug(f"Removing property: {line_stripped}")
                    continue

            lines.append(line_stripped)

        return '\n'.join(lines)

    def add_vcard_property(self, name, property_name, property_value):
        """
        Add or update a property in a vCard entry by name

        :param name: Full name (FN field) of the vCard
        :param property_name: Property name to add (e.g., 'TEL', 'EMAIL', 'NOTE')
        :param property_value: Property value (can include parameters, e.g., 'TYPE=CELL:+1234567890')
        :return: Dictionary with success status and result message

        Example:
            # Add a phone number
            result = add_vcard_property("John Smith", "TEL", "TYPE=CELL:+9876543210")

            # Add an email
            result = add_vcard_property("Jane Doe", "EMAIL", "TYPE=WORK:new.email@example.com")

            # Add a note
            result = add_vcard_property("John Smith", "NOTE", "This is a new note")
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        vcard_index = -1

        # Search for vCard with matching name
        for idx, vcard in enumerate(all_vcards):
            vcard_dict = self._parse_vcard_to_dict(vcard)
            vcard_name = vcard_dict.get('FN', '').strip()

            if vcard_name == name:
                vcard_index = idx
                break

        if vcard_index == -1:
            return {
                'success': False,
                'error': f'vCard with name "{name}" not found'
            }

        # Get the vCard text
        vcard_text = all_vcards[vcard_index]

        # Add the property
        modified_vcard = self._add_property_to_vcard(vcard_text, property_name, property_value)

        # Update the vCard in MOCK_PHONEBOOK_DATA
        all_vcards[vcard_index] = modified_vcard
        self.MOCK_PHONEBOOK_DATA = '\n'.join(all_vcards)

        # Auto-update folder versions based on added property
        added_property = self._extract_property_name(property_name)
        self._update_folder_versions(modified_properties={added_property})

        return {
            'success': True,
            'message': f'Successfully added property {property_name} to vCard: {name}',
            'modified_vcard': modified_vcard
        }

    def _add_property_to_vcard(self, vcard_text, property_name, property_value):
        """
        Add a property to a vCard text (before END:VCARD)

        :param vcard_text: Complete vCard text
        :param property_name: Property name to add
        :param property_value: Property value (may include parameters)
        :return: Modified vCard text with property added
        """
        lines = []

        for line in vcard_text.split('\n'):
            line_stripped = line.strip()

            # Insert new property before END:VCARD
            if line_stripped == 'END:VCARD':
                # Format the new property line
                if ':' in property_value:
                    # Value already includes parameters (e.g., "TYPE=CELL:+123456")
                    new_line = f"{property_name.upper()};{property_value}"
                else:
                    # Simple value without parameters
                    new_line = f"{property_name.upper()}:{property_value}"

                lines.append(new_line)
                logging.debug(f"Adding property: {new_line}")

            if line_stripped:
                lines.append(line_stripped)

        return '\n'.join(lines)

    def modify_vcard_property(self, name, property_name, new_value):
        """
        Modify a specific property value in a vCard entry by name

        :param name: Full name (FN field) of the vCard
        :param property_name: Property name to modify (e.g., 'TEL', 'EMAIL', 'NOTE', 'FN')
        :param new_value: New property value (can include parameters, e.g., 'TYPE=CELL:+9999999999')
        :return: Dictionary with success status and result message

        Example:
            # Modify phone number
            result = modify_vcard_property("John Smith", "TEL", "TYPE=CELL:+9999999999")

            # Modify email
            result = modify_vcard_property("Jane Doe", "EMAIL", "TYPE=WORK:newemail@example.com")

            # Modify name
            result = modify_vcard_property("John Smith", "FN", "John A. Smith")

            # Modify note
            result = modify_vcard_property("Jane Doe", "NOTE", "Updated note")
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        vcard_index = -1

        # Search for vCard with matching name
        for idx, vcard in enumerate(all_vcards):
            vcard_dict = self._parse_vcard_to_dict(vcard)
            vcard_name = vcard_dict.get('FN', '').strip()

            if vcard_name == name:
                vcard_index = idx
                break

        if vcard_index == -1:
            return {
                'success': False,
                'error': f'vCard with name "{name}" not found'
            }

        # Get the vCard text
        vcard_text = all_vcards[vcard_index]

        # Modify the property
        modified_vcard = self._modify_property_in_vcard(vcard_text, property_name, new_value)

        # Update the vCard in MOCK_PHONEBOOK_DATA
        all_vcards[vcard_index] = modified_vcard
        self.MOCK_PHONEBOOK_DATA = '\n'.join(all_vcards)

        # Auto-update folder versions based on modified property
        modified_property = self._extract_property_name(property_name)
        self._update_folder_versions(modified_properties={modified_property})

        return {
            'success': True,
            'message': f'Successfully modified property {property_name} in vCard: {name}',
            'modified_vcard': modified_vcard
        }

    def _modify_property_in_vcard(self, vcard_text, property_name, new_value):
        """
        Modify a property in a vCard text

        :param vcard_text: Complete vCard text
        :param property_name: Property name to modify (uppercase will be applied)
        :param new_value: New property value (may include parameters)
        :return: Modified vCard text with property updated
        """
        lines = []
        property_found = False
        property_name_upper = property_name.upper()

        for line in vcard_text.split('\n'):
            line_stripped = line.strip()

            # Always keep BEGIN and END
            if line_stripped in ['BEGIN:VCARD', 'END:VCARD']:
                lines.append(line_stripped)
                continue

            # Skip empty lines
            if not line_stripped:
                continue

            # Parse property name
            if ':' in line_stripped:
                if ';' in line_stripped.split(':', 1)[0]:
                    current_property = line_stripped.split(';')[0].upper()
                else:
                    current_property = line_stripped.split(':')[0].upper()

                # Check if this is the property to modify
                if current_property == property_name_upper and not property_found:
                    # Format the new property line
                    if ':' in new_value:
                        # Value already includes parameters (e.g., "TYPE=CELL:+123456")
                        new_line = f"{property_name_upper};{new_value}"
                    else:
                        # Simple value without parameters
                        new_line = f"{property_name_upper}:{new_value}"

                    lines.append(new_line)
                    property_found = True
                    logging.debug(f"Modified property: {line_stripped} -> {new_line}")
                    continue

            lines.append(line_stripped)

        # If property was not found, log a warning
        if not property_found:
            logging.warning(f"Property {property_name_upper} not found in vCard, no modification made")

        return '\n'.join(lines)

    def add_vcard_entry(self, name, tel=None, email=None):
        """
        Add a new vCard entry to the phonebook

        :param name: Full name for the vCard (required)
        :param tel: Phone number (optional, can be a string or list of strings)
        :param email: Email address (optional, can be a string or list of strings)
        :return: Dictionary with success status, new vCard handle, and the created vCard

        Example:
            # Add vCard with only name
            result = add_vcard_entry("John Doe")

            # Add vCard with name and phone
            result = add_vcard_entry("Jane Smith", tel="+1234567890")

            # Add vCard with multiple phones and emails
            result = add_vcard_entry("Bob Johnson",
                                    tel=["+1111111111", "+2222222222"],
                                    email=["bob@example.com", "bob.j@work.com"])
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        # Generate new vCard handle (index)
        new_index = len(all_vcards)
        new_handle = f"{new_index}.vcf"

        # Build new vCard
        vcard_lines = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{name}"
        ]

        # Add N (structured name) - use FN as fallback
        name_parts = name.split()
        if len(name_parts) >= 2:
            # Assume "FirstName LastName" format
            vcard_lines.append(f"N:{name_parts[-1]};{' '.join(name_parts[:-1])};;;")
        else:
            vcard_lines.append(f"N:{name};;;;")

        # Add phone number(s)
        if tel:
            if isinstance(tel, str):
                vcard_lines.append(f"TEL;TYPE=CELL:{tel}")
            elif isinstance(tel, list):
                vcard_lines.extend(f"TEL;TYPE=CELL:{phone}" for phone in tel)

        # Add email(s)
        if email:
            if isinstance(email, str):
                vcard_lines.append(f"EMAIL;TYPE=INTERNET:{email}")
            elif isinstance(email, list):
                vcard_lines.extend(f"EMAIL;TYPE=INTERNET:{mail}" for mail in email)

        vcard_lines.append("END:VCARD")

        new_vcard = '\n'.join(vcard_lines)

        # Add to phonebook
        all_vcards.append(new_vcard)
        self.MOCK_PHONEBOOK_DATA = '\n'.join(all_vcards)

        # Auto-update folder versions for entry insertion
        self._update_folder_versions(is_entry_change=True)
        logging.info(f"Added new vCard entry: {new_handle} - {name}")

        return {
            'success': True,
            'handle': new_handle,
            'index': new_index,
            'message': f'Successfully added vCard entry: {name}',
            'vcard': new_vcard
        }

    def delete_vcard_entry(self, name):
        """
        Delete a complete vCard entry from the phonebook by name

        :param name: Full name (FN field) of the vCard to delete
        :return: Dictionary with success status and result message

        Example:
            # Delete vCard by name
            result = delete_vcard_entry("John Smith")
            result = delete_vcard_entry("Jane Doe")
        """
        all_vcards = self._parse_vcard_list(self.MOCK_PHONEBOOK_DATA)

        vcard_index = -1
        deleted_vcard = None

        # Search for vCard with matching name
        for idx, vcard in enumerate(all_vcards):
            vcard_dict = self._parse_vcard_to_dict(vcard)
            vcard_name = vcard_dict.get('FN', '').strip()

            if vcard_name == name:
                vcard_index = idx
                deleted_vcard = vcard
                break

        if vcard_index == -1:
            return {
                'success': False,
                'error': f'vCard with name "{name}" not found'
            }

        # Delete the vCard
        all_vcards.pop(vcard_index)
        self.MOCK_PHONEBOOK_DATA = '\n'.join(all_vcards)

        # Auto-update folder versions for entry removal
        self._update_folder_versions(is_entry_change=True)

        logging.info(f"Deleted vCard entry at index {vcard_index}: {name}")

        return {
            'success': True,
            'message': f'Successfully deleted vCard entry: {name}',
            'deleted_index': vcard_index,
            'deleted_vcard': deleted_vcard
        }


class PBAPSrmState:
    SRM_DISABLED = 0
    SRM_ENABLED_BUT_WAITING = 1
    SRM_ENABLED = 2


class PBAPInfo:
    CONN_ID = "conn_id"
    LOCAL_MOPL = "local_mopl"
    REMOTE_MOPL = "remote_mopl"
    LOCAL_SRM = "local_srm"
    LOCAL_SRMP = "local_srmp"
    SRM_STATE = "srm_state"
    LOCAL_SUPPORT_FEATURE = "local_support_feature"
    REMOTE_SUPPORT_FEATURE = 'remote_support_feature'
    RX_DATA = "rx_data"
    TX_DATA = "tx_data"
    TX_CNT = "tx_cnt"


# class TransportType:
#     RFCOMM_CONN = 0
#     L2CAP_CONN = 1


# class ObexRole:
#     PCE = 0  # Phone Book Client Equipment
#     PSE = 1  # Phone Book Server Equipment


class PBAPConnection:
    def __init__(self, address):
        self.address = address
        self.transport_type = None  # RFCOMM or L2CAP connection type
        self.role = None       # PCE or PSE
        self.conn_info = {}
        self.data_rx = {}  # {ev: [data_list]}
        self.data_tx = {}
        # Initialize connection info
        self.conn_info[PBAPInfo.CONN_ID] = 0
        self.conn_info[PBAPInfo.LOCAL_MOPL] = 255
        self.conn_info[PBAPInfo.REMOTE_MOPL] = 255
        self.conn_info[PBAPInfo.RX_DATA] = {}
        self.conn_info[PBAPInfo.TX_DATA] = {}
        self.conn_info[PBAPInfo.TX_CNT] = 0
        self.conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_DISABLED
        self.conn_info[PBAPInfo.LOCAL_SRM] = False
        self.conn_info[PBAPInfo.LOCAL_SRMP] = 0
        self.conn_info[PBAPInfo.LOCAL_SUPPORT_FEATURE] = 0x3ff
        self.conn_info[PBAPInfo.REMOTE_SUPPORT_FEATURE] = 0

    def get_transport_type(self):
        """Get the current transport layer connection type (RFCOMM or L2CAP)"""
        return self.transport_type

    def set_transport_type(self, transport_type):
        """Set transport layer connection type"""
        self.transport_type = transport_type

    def clear_transport_type(self):
        """Clear transport layer connection"""
        self.transport_type = None

    def set_obex(self, conn_type):
        """Set OBEX layer connection type"""
        self.role = conn_type

    def clear_obex(self):
        """Clear OBEX layer connection"""
        self.role = None

    def is_transport_connected(self):
        """Check if transport layer is connected"""
        return self.transport_type is not None

    def is_obex_connected(self):
        """Check if OBEX layer is connected"""
        return self.role is not None

    def set_info(self, key, value):
        self.conn_info[key] = value

    def get_info(self, key=None):
        if key is None:
            return self.conn_info
        return self.conn_info.get(key)

    def clear_tx_state(self):
        self.conn_info[PBAPInfo.TX_DATA] = {}
        self.conn_info[PBAPInfo.TX_CNT] = 0
        self.conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_DISABLED
        self.conn_info[PBAPInfo.LOCAL_SRM] = False
        self.conn_info[PBAPInfo.LOCAL_SRMP] = 0
        # self.conn_info[PBAPInfo.LOCAL_AUTH_CHALLENGE_REQ] = {}

    def clear_rx_state(self):
        self.conn_info[PBAPInfo.RX_DATA] = {}
        self.conn_info[PBAPInfo.SRM_STATE] = PBAPSrmState.SRM_DISABLED
        self.conn_info[PBAPInfo.LOCAL_SRM] = False
        self.conn_info[PBAPInfo.LOCAL_SRMP] = 0
        # self.conn_info[PBAPInfo.LOCAL_AUTH_CHALLENGE_REQ] = {}

    def rx(self, ev, data):
        self.data_rx.setdefault(ev, []).append(data)

    def rx_data_get(self, ev, timeout, clear):
        if ev in self.data_rx and len(self.data_rx[ev]) != 0:
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        if wait_for_event(timeout, lambda: ev in self.data_rx and len(self.data_rx[ev]) != 0):
            if clear:
                return self.data_rx[ev].pop(0)
            else:
                return self.data_rx[ev][0]

        return None

    def rx_data_clear(self, ev, data):
        if ev in self.data_rx:
            if data in self.data_rx[ev]:
                self.data_rx[ev].remove(data)

    def tx(self, ev, data):
        self.data_tx.setdefault(ev, []).append(data)
        logging.info(f"tx = {self.data_tx}")

    def tx_data_get(self, ev, timeout, clear):
        logging.info(f"tx_data_get = {self.data_tx}")
        if ev in self.data_tx and len(self.data_tx[ev]) != 0:
            if clear:
                return self.data_tx[ev].pop(0)
            else:
                return self.data_tx[ev][0]

        if wait_for_event(timeout, lambda: ev in self.data_tx and len(self.data_tx[ev]) != 0):
            if clear:
                return self.data_tx[ev].pop(0)
            else:
                return self.data_tx[ev][0]

        return None

    def tx_data_clear(self, ev):
        if ev in self.data_tx:
            del self.data_tx[ev]


class SdpConnection:
    def __init__(self, address, rfcomm_channel, l2cap_psm, supported_features, supported_repositories):
        self.address = address
        self.rfcomm_channel = rfcomm_channel
        self.l2cap_psm = l2cap_psm
        self.supported_features = supported_features
        self.supported_repositories = supported_repositories


class PBAP:
    def __init__(self):
        """
        Initialize PBAP (Phone Book Access Profile) instance

        Creates SDP and PBAP connection dictionaries, phonebook structure,
        and starts the event handler for PBAP events
        """
        self.sdp_connections = {}  # {address : conn}
        self.pbap_connections = {}  # {address : conn}
        self.auto_send = True
        self.phonebook = PBAPFolderStructure()
        from autopts.pybtp.btp import PBAPEventHandler
        self.event_handler = PBAPEventHandler(self)
        self.event_handler.start()

    def disable_auto_send(self):
        """Disable automatic sending of responses to PBAP requests"""
        self.auto_send = False

    def add_sdp_connection(self, address, rfcomm_channel, l2cap_psm, supported_features, supported_repositories):
        """
        Add or update an SDP (Service Discovery Protocol) connection for a given address

        :param address: Bluetooth device address
        :param rfcomm_channel: RFCOMM channel number for PBAP service
        :param l2cap_psm: L2CAP PSM (Protocol Service Multiplexer) value
        :param supported_features: Bitmask of supported PBAP features
        :param supported_repositories: Bitmask of supported phonebook repositories
        """
        self.sdp_connections[address] = SdpConnection(
            address,
            rfcomm_channel,
            l2cap_psm,
            supported_features,
            supported_repositories
        )

    def get_sdp_connection(self, address):
        """
        Retrieve an SDP connection by address

        :param address: Bluetooth device address
        :return: SdpConnection object or None if not found
        """
        return self.sdp_connections.get(address)

    def remove_sdp_connection(self, address):
        """
        Remove an SDP connection by address

        :param address: Bluetooth device address
        """
        if address in self.sdp_connections:
            del self.sdp_connections[address]

    def wait_for_sdp_finished(self, address, timeout=5):
        """
        Wait for SDP (Service Discovery Protocol) discovery to complete for a given address

        :param address: Bluetooth device address
        :param timeout: Maximum time to wait in seconds (default: 5)
        :return: True if SDP connection exists, False otherwise
        """
        wait_for_event(timeout, lambda: self.get_sdp_connection(address) is not None)

        return self.get_sdp_connection(address) is not None

    def add_pbap_connection(self, address, transport_type: types.PBAPTransportType):
        """
        Add or update a PBAP connection for a given address

        :param address: Bluetooth device address
        :param transport_type: Transport type (RFCOMM or L2CAP) from types.PBAPTransportType
        """
        conn = PBAPConnection(address)
        conn.set_transport_type(transport_type)
        self.pbap_connections[address] = conn

    def get_pbap_connection(self, address):
        """
        Retrieve a PBAP connection by address

        :param address: Bluetooth device address
        :return: PBAPConnection object or None if not found
        """
        return self.pbap_connections.get(address)

    def remove_pbap_connection(self, address, transport_type: types.PBAPTransportType):
        """
        Remove a PBAP connection by address and transport type

        :param address: Bluetooth device address
        :param transport_type: Transport type to match (RFCOMM or L2CAP)
        """
        if address in self.pbap_connections:
            conn = self.get_pbap_connection(address)
            if conn and conn.get_transport_type() == transport_type:
                del self.pbap_connections[address]

    def wait_for_pbap_connection(self, address, timeout=5):
        """
        Wait for a PBAP connection to be established

        :param address: Bluetooth device address
        :param timeout: Maximum time to wait in seconds (default: 5)
        :return: True if connection is established, False otherwise
        """
        wait_for_event(timeout, lambda: self.get_pbap_connection(address) is not None)

        return self.get_pbap_connection(address) is not None

    def wait_for_pbap_disconnection(self, address, timeout=5):
        """
        Wait for a PBAP connection to be disconnected

        :param address: Bluetooth device address
        :param timeout: Maximum time to wait in seconds (default: 5)
        :return: True if connection is disconnected, False otherwise
        """
        wait_for_event(timeout, lambda: self.get_pbap_connection(address) is None)

        return self.get_pbap_connection(address) is None

    def add_pbap_obex_connection(self, address, role: types.PBAPRole):
        """
        Add OBEX (Object Exchange) connection layer to an existing PBAP connection

        :param address: Bluetooth device address
        :param role: OBEX role (PCE or PSE)
        """
        conn = self.get_pbap_connection(address)
        if conn:
            conn.set_obex(role)

    def is_pbap_obex_connected(self, address, timeout=0):
        """
        Check if OBEX connection layer is established for a PBAP connection

        :param address: Bluetooth device address
        :param timeout: Maximum time to wait for OBEX connection (in seconds), 0 means no wait
        :return: True if OBEX connection is established, False otherwise
        """
        if self.get_pbap_connection(address) is None:
            return False
        conn = self.get_pbap_connection(address)
        wait_for_event(timeout, lambda: conn.is_obex_connected())
        return conn.is_obex_connected()

    def remote_pbap_obex_connection(self, address):
        """
        Remove OBEX connection layer from a PBAP connection

        :param address: Bluetooth device address
        """
        conn = self.get_pbap_connection(address)
        if conn:
            conn.clear_obex()

    def set_info(self, address, key, value):
        """
        Set connection information for a PBAP connection

        :param address: Bluetooth device address
        :param key: Information key (e.g., CONN_ID, LOCAL_MOPL, etc.)
        :param value: Information value to set
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return

        conn.set_info(key, value)

    def get_info(self, address, key):
        """
        Get connection information from a PBAP connection

        :param address: Bluetooth device address
        :param key: Information key to retrieve
        :return: Information value or None if connection doesn't exist
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return None

        return conn.get_info(key)

    def clear_tx_state(self, address):
        """
        Clear transmission state for a PBAP connection

        Resets TX data, TX count, SRM state, and SRM parameters

        :param address: Bluetooth device address
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return

        conn.clear_tx_state()

    def clear_rx_state(self, address):
        """
        Clear reception state for a PBAP connection

        Resets RX data, SRM state, and SRM parameters

        :param address: Bluetooth device address
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return

        conn.clear_rx_state()

    def rx(self, address, ev, data):
        """
        Store received data for a specific event on a PBAP connection

        :param address: Bluetooth device address
        :param ev: Event identifier
        :param data: Received data to store
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return

        conn.rx(ev, data)

    def rx_data_get(self, address, ev, timeout=10, clear=True):
        """
        Get received data for a specific event on a PBAP connection

        :param address: Bluetooth device address
        :param ev: Event identifier
        :param timeout: Maximum time to wait for data in seconds (default: 10)
        :param clear: Whether to remove data after retrieval (default: True)
        :return: Received data or None if not available
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return None

        return conn.rx_data_get(ev, timeout, clear)

    def rx_data_clear(self, address, ev, data):
        """
        Clear specific received data for an event on a PBAP connection

        :param address: Bluetooth device address
        :param ev: Event identifier
        :param data: Specific data to remove
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return

        conn.rx_data_clear(ev, data)

    def tx(self, address, ev, data):
        """
        Store transmission data for a specific event on a PBAP connection

        :param address: Bluetooth device address
        :param ev: Event identifier
        :param data: Data to transmit
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return

        conn.tx(ev, data)

    def tx_data_get(self, address, ev, timeout=10, clear=True):
        """
        Get transmission data for a specific event on a PBAP connection

        :param address: Bluetooth device address
        :param ev: Event identifier
        :param timeout: Maximum time to wait for data in seconds (default: 10)
        :param clear: Whether to remove data after retrieval (default: True)
        :return: Transmission data or None if not available
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return None

        return conn.tx_data_get(ev, timeout, clear)

    def tx_data_clear(self, address, ev):
        """
        Clear all transmission data for a specific event on a PBAP connection

        :param address: Bluetooth device address
        :param ev: Event identifier
        """
        conn = self.get_pbap_connection(address)
        if conn is None:
            return

        conn.tx_data_clear(ev)

    def set_path(self, flag, path):
        """
        Set the current path in the PBAP phonebook folder structure

        :param flag: Operation flag (2=set path, 3=navigate up)
        :param path: Target path or folder name (can be bytes or string)
        :return: Current path after operation with root prefix, or None if invalid
        """
        result_path = None
        if isinstance(path, bytes):
            path = path.decode('utf-16-be').rstrip('\x00')
        logging.info(f"flags = {flag}, path = {path}")
        if flag == 2:
            if path is None or len(path) == 0:
                result_path = self.phonebook.set_path_to_root()
            else:
                if path.endswith('.vcf'):
                    path_without_vcf = path.rsplit('.vcf', 1)[0]
                    if '/' in path_without_vcf:
                        result_path = self.phonebook.set_path(path_without_vcf)
                    else:
                        result_path = self.phonebook.navigate_down(path_without_vcf)
                else:
                    if '/' in path:
                        result_path = self.phonebook.set_path(path)
                    else:
                        result_path = self.phonebook.navigate_down(path)

        elif flag == 3:
            result_path = self.phonebook.navigate_up()

        return result_path

    def pull_vcard_listing(self, max_list_count=65535,
                           list_start_offset=0, search_value=None,
                           search_attribute=None, order=None,
                          vcard_selector=None, vcard_selector_operator=0):
        """
        Retrieve vCard listing from phonebook in XML format

        :param max_list_count: Maximum number of entries to return (default: 65535)
        :param list_start_offset: Start offset for pagination (default: 0)
        :param search_value: Search value to filter results
        :param search_attribute: Attribute to search (e.g., 'name', 'number')
        :param order: Sort order ('indexed', 'alphanumeric', 'phonetic')
        :param vcard_selector: Property bitmask for filtering vCards
        :param vcard_selector_operator: Logic operator (0=OR, 1=AND)
        :return: Dictionary with phonebook size, returned count, and XML content
        """
        return self.phonebook.pull_vcard_listing(
            max_list_count, list_start_offset, search_value, search_attribute,
            order, vcard_selector, vcard_selector_operator
        )

    def pull_phonebook(self, max_list_count=65535, list_start_offset=0, property_selector=None,
                          vcard_selector=None, vcard_selector_operator=0, format_type=0x01):
        """
        Retrieve complete phonebook with vCard entries

        :param max_list_count: Maximum number of entries to return (default: 65535)
        :param list_start_offset: Start offset for pagination (default: 0)
        :param property_selector: Property bitmask for filtering properties in vCards
        :param vcard_selector: vCard bitmask for filtering which vCards to return
        :param vcard_selector_operator: Logic operator (0=OR, 1=AND)
        :param format_type: vCard format (0x00=vCard 2.1, 0x01=vCard 3.0)
        :return: Dictionary with phonebook size, returned count, and vCard content
        """
        return self.phonebook.pull_phonebook(
            max_list_count, list_start_offset, property_selector,
            vcard_selector, vcard_selector_operator, format_type
        )

    def pull_vcard_entry(self, handle, propertyselector=None, format_type=0x01):
        """
        Retrieve a single vCard entry by handle

        :param handle: vCard handle (e.g., "0.vcf" or "X-BT-UID:...")
        :param propertyselector: Property bitmask for filtering properties
        :param format_type: vCard format (0x00=vCard 2.1, 0x01=vCard 3.0)
        :return: Dictionary with success status and vCard content
        """
        return self.phonebook.pull_vcard_entry(handle=handle, propertyselector=propertyselector, format_type=format_type)

    def remove_vcard_property(self, name, property_name):
        """
        Remove a property from a vCard entry

        :param name: Full name (FN field) of the vCard
        :param property_name: Property name to remove (e.g., 'TEL', 'EMAIL')
        :return: Dictionary with success status and result message
        """
        return self.phonebook.remove_vcard_property(name, property_name)

    def add_vcard_property(self, name, property_name, property_value):
        """
        Add a property to a vCard entry

        :param name: Full name (FN field) of the vCard
        :param property_name: Property name to add (e.g., 'TEL', 'EMAIL')
        :param property_value: Property value to add
        :return: Dictionary with success status and result message
        """
        return self.phonebook.add_vcard_property(name, property_name, property_value)

    def modify_vcard_property(self, name, property_name, new_value):
        """
        Modify a property value in a vCard entry

        :param name: Full name (FN field) of the vCard
        :param property_name: Property name to modify (e.g., 'TEL', 'EMAIL')
        :param new_value: New property value
        :return: Dictionary with success status and result message
        """
        return self.phonebook.modify_vcard_property(name, property_name, new_value)

    def delete_vcard_entry(self, name):
        """
        Delete a complete vCard entry from the phonebook

        :param name: Full name (FN field) of the vCard to delete
        :return: Dictionary with success status and result message
        """
        return self.phonebook.delete_vcard_entry(name)

    def add_vcard_entry(self, name):
        """
        Add a new vCard entry to the phonebook

        :param name: Full name for the new vCard entry
        :return: Dictionary with success status, handle, and vCard content
        """
        return self.phonebook.add_vcard_entry(name)

    def is_valid_combined_path(self, name):
        """
        Check if a path is valid in the phonebook folder structure

        :param name: Path to validate
        :return: True if path is valid, False otherwise
        """
        return name in self.phonebook.VALID_TELECOM_PATH_PATTERNS

    def reset_dbi(self):
        """Reset the phonebook database instance"""
        self.phonebook.reset_dbi()
