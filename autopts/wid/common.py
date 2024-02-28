import threading

get_iut = None


def verify_att_error(description):
    logging.debug("description=%r", description)

    description_values = []

    for err_code, err_string in att_rsp_str.items():
        if err_string and err_string in description:
            description_values.append(err_string)

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    logging.debug("Description values: %r", description_values)

    for value in description_values:
        logging.debug("Verifying: %r", value)

        try:
            if value not in verify_values:
                logging.debug("Verification failed, value not in verify values")
                return False
        except TypeError:
            logging.debug("Value under verification is not string")

    logging.debug("All verifications passed")

    clear_verify_values()

    return True


def verify_description(description):
    """A function to verify that values are in PTS MMI description

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    description_values = re.findall(r"(?:'|=\s+)([0-9-xA-Fa-f]{2,})", description)
    logging.debug("Description values: %r", description_values)

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"

    converted_verify = []

    # convert small values to int to simplify verification.
    # Some values are displayed with leading zeros
    for verify in verify_values:
        verify = verify.upper()
        if len(verify) < 8:
            converted_verify.append(int(verify, 16))
        else:
            converted_verify.append(verify)

    for value in description_values:
        logging.debug("Verifying: %r", value)

        value = value.upper()

        if len(value) < 8:
            value = int(value, 16)

        try:
            if value not in converted_verify:
                logging.debug("Verification failed, value not in verify values")
                return False
        except TypeError:
            logging.debug("Value under verification is not string")

    logging.debug("All verifications passed")

    clear_verify_values()

    return True


def verify_description_truncated(description):
    """A function to verify that truncated values are in PTS MMI description.

    Verification is successful if the PTS MMI description contains a value
    starting with the value under verification.

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    description_values = re.findall(r"(?:'|=\s+)([0-9-xA-Fa-f]{2,})", description)
    logging.debug("Description values: %r", description_values)

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"

    verify_values = list(map(str.upper, verify_values))
    description_values = list(map(str.upper, description_values))

    unverified_desc = [x for x in description_values if x not in verify_values]
    if unverified_desc:
        logging.debug("Verifying for partial matches: %r", unverified_desc)

        for desc_value in unverified_desc:
            matches = [x for x in verify_values if desc_value.startswith(x) and len(x) > 8]
            if not matches:
                logging.debug("Verification failed, %r not in verify values", desc_value)
                return False

    logging.debug("All verifications passed")

    clear_verify_values()

    return True


def verify_multiple_read_description(description):
    """A function to verify that merged multiple read att values are in

    PTS MMI description.

    Returns True if verification is successful, False if not.

    description -- MMI description

    """
    logging.debug("description=%r", description)

    MMI.reset()
    MMI.parse_description(description)
    description_values = MMI.args
    logging.debug("Description values: %r", description_values)

    got_mtp_read = [''.join(description_values)]

    verify_values = get_verify_values()
    logging.debug("Verifying values: %r", verify_values)

    # verify_values shall not be a string: all its characters will be verified
    assert isinstance(verify_values, list), "verify_values should be a list!"

    exp_mtp_read = ""
    for value in verify_values:
        try:
            exp_mtp_read = exp_mtp_read.join(value)
        except TypeError:
            value = value.decode("utf-8")
            exp_mtp_read = exp_mtp_read.join(value)

    if exp_mtp_read not in got_mtp_read:
        logging.debug("Verification failed, value not in description")
        return False

    logging.debug("Multiple read verifications passed")

    clear_verify_values()

    return True


def parse_passkey_description(description):
    """A function to parse passkey from description

    PTS MMI description.

    Returns passkey if successful, None if not.

    description -- MMI description
    """
    logging.debug("description=%r", description)

    match = re.search(r"\b[0-9]+\b", description)
    if match:
        pk = match.group(0)
        logging.debug("passkey=%r", pk)
        return int(pk)

    return None


def parse_handle_description(description):
    """A function to parse handle from description

    PTS MMI description.

    Returns passkey if successful, None if not.

    description -- MMI description
    """
    logging.debug("description=%r", description)

    match = re.search(r"\bhandle (?:0x)?([0-9A-Fa-f]+)\b", description)
    if match:
        handle = match.group(1)
        logging.debug("handle=%r", handle)
        return int(handle)

    return None
