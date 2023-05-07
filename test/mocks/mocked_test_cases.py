# Randomly selected group of test cases
mock_workspace_test_cases = {
    'GAP': [
        'GAP/BROB/BCST/BV-01-C',
        'GAP/BROB/BCST/BV-02-C',
        'GAP/BROB/BCST/BV-03-C',
        'GAP/BROB/BCST/BV-04-C',
        'GAP/SEC/CSIGN/BI-02-C',
        'GAP/SEC/CSIGN/BI-03-C',
        'GAP/SEC/CSIGN/BI-04-C',
        'GAP/PRIV/CONN/BV-10-C',
        'GAP/PRIV/CONN/BV-11-C',
        'GAP/PRIV/CONN/BV-12-C',
        'GAP/ADV/BV-01-C',
        'GAP/ADV/BV-02-C',
        'GAP/ADV/BV-03-C',
    ],
    'GATT': [
        'GATT/CL/GAC/BV-01-C',
        'GATT/CL/GAD/BV-01-C',
        'GATT/CL/GAD/BV-02-C',
        'GATT/CL/GAD/BV-03-C',
        'GATT/CL/GAD/BV-04-C',
        'GATT/SR/GAS/BV-07-C',
        'GATT/SR/GAS/BV-08-C',
        'GATT/SR/GAT/BV-01-C',
        'GATT/SR/UNS/BI-01-C',
        'GATT/SR/UNS/BI-02-C',
        'GATT/SR/GPM/BV-05-C',
    ],
    'L2CAP': [
        'L2CAP/COS/CFC/BV-01-C',
        'L2CAP/COS/CFC/BV-02-C',
        'L2CAP/COS/CFC/BV-03-C',
        'L2CAP/COS/ECFC/BV-01-C',
        'L2CAP/COS/ECFC/BV-02-C',
        'L2CAP/COS/ECFC/BV-03-C',
        'L2CAP/LE/CPU/BV-01-C',
        'L2CAP/LE/CPU/BV-02-C',
        'L2CAP/LE/CPU/BI-01-C',
        'L2CAP/LE/CPU/BI-02-C',
        'L2CAP/LE/REJ/BI-01-C',
        'L2CAP/LE/REJ/BI-02-C',
        'L2CAP/LE/CFC/BV-01-C',
        'L2CAP/LE/CFC/BV-02-C',
        'L2CAP/LE/CFC/BV-03-C',
        'L2CAP/LE/CID/BI-01-C',
        'L2CAP/ECFC/BV-01-C',
        'L2CAP/ECFC/BV-02-C',
        'L2CAP/ECFC/BV-03-C',
        'L2CAP/TIM/BV-03-C',
    ],
}

mock_workspace_test_cases_sum = sum(mock_workspace_test_cases.values(), [])

mock_iut_config_1 = {}
mock_iut_config_1_result = {}

mock_iut_config_2 = {
    'prj.conf': {}
}
mock_iut_config_2_result = {
    'prj.conf': mock_workspace_test_cases_sum
}

mock_iut_config_3 = {
    'prj.conf': {'test_cases': []}
}
mock_iut_config_3_result = {
    'prj.conf': mock_workspace_test_cases_sum
}

mock_iut_config_4 = {
    'prj.conf': {'test_cases': ['GAP', 'GATT']}
}
mock_iut_config_4_result = {
    'prj.conf': mock_workspace_test_cases['GAP'] + mock_workspace_test_cases['GATT']
}

mock_iut_config_5 = {
    'prj.conf': {},
    'overlay1.conf': {}
}
mock_iut_config_5_result = {
    'prj.conf': mock_workspace_test_cases_sum,
    'overlay1.conf': []
}

mock_iut_config_6 = {
    'prj.conf': {},
    'overlay1.conf': {'test_cases': []}
}
mock_iut_config_6_result = {
    'prj.conf': mock_workspace_test_cases_sum,
    'overlay1.conf': []
}

mock_iut_config_7 = {
    'prj.conf': {},
    'overlay1.conf': {'test_cases': ['GATT', 'L2CAP']}
}
mock_iut_config_7_result = {
    'prj.conf': mock_workspace_test_cases['GAP'],
    'overlay1.conf': mock_workspace_test_cases['GATT'] + mock_workspace_test_cases['L2CAP']
}

mock_iut_config_8 = {
    'prj.conf': {'test_cases': []},
    'overlay1.conf': {}
}
mock_iut_config_8_result = {
    'prj.conf': mock_workspace_test_cases_sum,
    'overlay1.conf': []
}

mock_iut_config_9 = {
    'prj.conf': {'test_cases': []},
    'overlay1.conf': {'test_cases': []}
}
mock_iut_config_9_result = {
    'prj.conf': mock_workspace_test_cases_sum,
    'overlay1.conf': []
}

mock_iut_config_10 = {
    'prj.conf': {'test_cases': []},
    'overlay1.conf': {'test_cases': ['GATT', 'L2CAP']}
}
mock_iut_config_10_result = {
    'prj.conf': mock_workspace_test_cases['GAP'],
    'overlay1.conf': mock_workspace_test_cases['GATT'] + mock_workspace_test_cases['L2CAP']
}

mock_iut_config_11 = {
    'prj.conf': {'test_cases': ['GATT']},
    'overlay1.conf': {}
}
mock_iut_config_11_result = {
    'prj.conf': mock_workspace_test_cases['GATT'],
    'overlay1.conf': []
}

mock_iut_config_12 = {
    'prj.conf': {'test_cases': ['GATT']},
    'overlay1.conf': {'test_cases': []}
}
mock_iut_config_12_result = {
    'prj.conf': mock_workspace_test_cases['GATT'],
    'overlay1.conf': []
}

mock_iut_config_13 = {
    'prj.conf': {'test_cases': ['GATT']},
    'overlay1.conf': {'test_cases': ['GAP', 'L2CAP']}
}
mock_iut_config_13_result = {
    'prj.conf': mock_workspace_test_cases['GATT'],
    'overlay1.conf': mock_workspace_test_cases['GAP'] + mock_workspace_test_cases['L2CAP']
}

mock_iut_config_14 = {
    'prj.conf': {'test_cases': ['GATT']},
    'overlay1.conf': {'test_cases': ['GAP']},
    'overlay2.conf': {'test_cases': ['L2CAP']}
}
mock_iut_config_14_result = {
    'prj.conf': mock_workspace_test_cases['GATT'],
    'overlay1.conf': mock_workspace_test_cases['GAP'],
    'overlay2.conf': mock_workspace_test_cases['L2CAP']
}

mock_iut_config_15 = {
    'prj.conf': {'test_cases': ['GAP']},
    'overlay1.conf': {'test_cases': ['GAP']},
    'overlay2.conf': {'test_cases': ['L2CAP']}
}
mock_iut_config_15_result = {
    'prj.conf': [],
    'overlay1.conf': mock_workspace_test_cases['GAP'],
    'overlay2.conf': mock_workspace_test_cases['L2CAP']
}

mock_iut_config_16 = {
    'prj.conf': {'test_cases': ['GATT']},
    'overlay1.conf': {'test_cases': ['GAP']},
    'overlay2.conf': {'test_cases': ['GAP']}
}
mock_iut_config_16_result = {
    'prj.conf': mock_workspace_test_cases['GATT'],
    'overlay1.conf': mock_workspace_test_cases['GAP'],
    'overlay2.conf': []
}

mock_iut_config_17 = {
    'prj.conf': {},
    'overlay1.conf': {'test_cases': ['GATT']},
    'overlay2.conf': {'test_cases': ['GATT', 'L2CAP']}
}
mock_iut_config_17_result = {
    'prj.conf': mock_workspace_test_cases['GAP'],
    'overlay1.conf': mock_workspace_test_cases['GATT'],
    'overlay2.conf': mock_workspace_test_cases['L2CAP'],
}

mock_iut_config_18 = {
    'prj.conf': {
        'test_cases': [
            'GAP/BROB/BCST/BV-01-C',
            'GAP/BROB/BCST/BV-02-C',
            'GAP/BROB/BCST/BV-03-C',
            'GAP/BROB/BCST/BV-04-C',
            'L2CAP/COS/CFC/BV-01-C',
            'L2CAP/COS/CFC/BV-02-C',
            'L2CAP/COS/CFC/BV-03-C',
            'L2CAP/COS/ECFC/BV-01-C',
            'L2CAP/COS/ECFC/BV-02-C',
            'L2CAP/COS/ECFC/BV-03-C',
            'GATT/CL/GAC/BV-01-C',
            'GATT/CL/GAD/BV-01-C',
            'GATT/CL/GAD/BV-02-C',
            'GATT/CL/GAD/BV-03-C',
            'GATT/CL/GAD/BV-04-C',
            'GATT/SR/GAS/BV-07-C',
            'GATT/SR/GAS/BV-08-C',
            'GATT/SR/GAT/BV-01-C',
            'GATT/SR/UNS/BI-01-C',
            'GATT/SR/UNS/BI-02-C',
            'GATT/SR/GPM/BV-05-C',
        ]
    },
    'overlay1.conf': {
        'test_cases': [
            'L2CAP/LE/CPU/BV-01-C',
            'L2CAP/LE/CPU/BV-02-C',
            'L2CAP/LE/CPU/BI-01-C',
            'L2CAP/LE/CPU/BI-02-C',
            'L2CAP/LE/REJ/BI-01-C',
            'L2CAP/LE/REJ/BI-02-C',
            'L2CAP/LE/CFC/BV-01-C',
            'L2CAP/LE/CFC/BV-02-C',
            'L2CAP/LE/CFC/BV-03-C',
            'L2CAP/LE/CID/BI-01-C',
        ]
    },
    'overlay2.conf': {
        'test_cases': [
            'L2CAP/ECFC/BV-01-C',
            'L2CAP/ECFC/BV-02-C',
            'L2CAP/ECFC/BV-03-C',
            'L2CAP/TIM/BV-03-C',
            'GAP/SEC/CSIGN/BI-02-C',
            'GAP/SEC/CSIGN/BI-03-C',
            'GAP/SEC/CSIGN/BI-04-C',
            'GAP/PRIV/CONN/BV-10-C',
            'GAP/PRIV/CONN/BV-11-C',
            'GAP/PRIV/CONN/BV-12-C',
            'GAP/ADV/BV-01-C',
            'GAP/ADV/BV-02-C',
            'GAP/ADV/BV-03-C',
            'GAP/SEC/CSIGN/BI-02-C',
            'GAP/SEC/CSIGN/BI-03-C',
            'GAP/SEC/CSIGN/BI-04-C',
            'GAP/PRIV/CONN/BV-10-C',
            'GAP/PRIV/CONN/BV-11-C',
            'GAP/PRIV/CONN/BV-12-C',
            'GAP/ADV/BV-01-C',
            'GAP/ADV/BV-02-C',
            'GAP/ADV/BV-03-C',
        ]
    }
}
mock_iut_config_18_result = {
    'prj.conf': mock_iut_config_18['prj.conf']['test_cases'],
    'overlay1.conf': mock_iut_config_18['overlay1.conf']['test_cases'],
    'overlay2.conf': mock_iut_config_18['overlay2.conf']['test_cases'],
}

mock_iut_config_19 = {
    'overlay1.conf': {'test_cases': ['GATT']},
    'overlay2.conf': {'test_cases': ['L2CAP']}
}
mock_iut_config_19_result = {
    'prj.conf': [],
    'overlay1.conf': mock_workspace_test_cases['GATT'],
    'overlay2.conf': mock_workspace_test_cases['L2CAP'],
}

# Rules:
# - The prj.conf is a default config, takes from the test case pool always
#   as the last, all remaining or remaining and matching 'test_cases' prefixes.
# - Except for the default config, the other .conf files select the tests
#   in the order of their order of appearance in the iut_config dictionary.

# Test some basic known use cases:
# 1. Empty iut_config
# 2. Only prj.conf, without 'test_cases' (takes the remaining test cases)
# 3. Only prj.conf, with empty 'test_cases' (takes the remaining test cases)
# 4. Only prj.conf, with filled 'test_cases' (takes the specified test cases)
# 5. prj.conf without 'test_cases', overlay1.conf without 'test_cases'
# 6. prj.conf without 'test_cases', overlay1.conf with empty 'test_cases'
# 7. prj.conf without 'test_cases', overlay1.conf with filled 'test_cases'
# 8. prj.conf with empty 'test_cases', overlay1.conf without 'test_cases'
# 9. prj.conf with empty 'test_cases', overlay1.conf with empty 'test_cases'
# 10. prj.conf with empty 'test_cases', overlay1.conf with filled 'test_cases'
# 11. prj.conf with filled 'test_cases', overlay1.conf without 'test_cases'
# 12. prj.conf with filled 'test_cases', overlay1.conf with empty 'test_cases'
# 13. prj.conf with filled 'test_cases', overlay1.conf with filled 'test_cases', no
# 14. prj.conf with filled 'test_cases', overlay1.conf and overlay2.conf with filled 'test_cases'
# 15. prj.conf overlap with overlay1.conf; overlay2.conf
# 16. prj.conf takes the remaining test cases; overlay1.conf overlap with overlay2.conf
# 17. prj.conf takes the remaining test cases; overlay1.conf overlap with overlay2.conf
# 18. Explicit test case names
# 19. The default config not used in the iut_config (hence should not be run)

test_case_list_generation_samples = [
    (mock_iut_config_1, mock_iut_config_1_result),
    (mock_iut_config_2, mock_iut_config_2_result),
    (mock_iut_config_3, mock_iut_config_3_result),
    (mock_iut_config_4, mock_iut_config_4_result),
    (mock_iut_config_5, mock_iut_config_5_result),
    (mock_iut_config_6, mock_iut_config_6_result),
    (mock_iut_config_7, mock_iut_config_7_result),
    (mock_iut_config_8, mock_iut_config_8_result),
    (mock_iut_config_9, mock_iut_config_9_result),
    (mock_iut_config_10, mock_iut_config_10_result),
    (mock_iut_config_11, mock_iut_config_11_result),
    (mock_iut_config_12, mock_iut_config_12_result),
    (mock_iut_config_13, mock_iut_config_13_result),
    (mock_iut_config_14, mock_iut_config_14_result),
    (mock_iut_config_15, mock_iut_config_15_result),
    (mock_iut_config_16, mock_iut_config_16_result),
    (mock_iut_config_17, mock_iut_config_17_result),
    (mock_iut_config_18, mock_iut_config_18_result),
    (mock_iut_config_19, mock_iut_config_19_result),
]
