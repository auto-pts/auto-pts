#
# auto-pts - The Bluetooth PTS Automation Framework
#
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

"""Script merge multiple TestCase.db files"

Usage:
$ python ./merge_db.py path/to/input1.db path/to/input2.db ... -o path/to/output.db
"""
import argparse
import os
import sqlite3
import sys

DATABASE_FILE = 'Merge_database.db'


class TestCaseTable:
    def __init__(self, db_files, merged_db):
        self.database_files = db_files
        self.merged_database_file = merged_db

    def _open(self):
        self.conn_merge = sqlite3.connect(self.merged_database_file)
        self.cursor_merge = self.conn_merge.cursor()

    def _close(self):
        self.cursor_merge.close()
        self.conn_merge.close()

    def merge_databases(self):
        self._open()

        for database_file in self.database_files:
            source_conn = sqlite3.connect(database_file)
            source_cursor = source_conn.cursor()
            source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = source_cursor.fetchall()
            print(tables)

            for table in tables:
                self.cursor_merge.execute(
                    f"CREATE TABLE IF NOT EXISTS {table[0]} (name TEXT, duration REAL, "
                    "count INTEGER, result TEXT);")

                source_cursor.execute(f"SELECT DISTINCT name FROM {table[0]};")
                source_test_cases = [row[0] for row in source_cursor.fetchall()]

                for test_case_name in source_test_cases:
                    source_cursor.execute(
                        f"SELECT duration, count, result FROM {table[0]} WHERE name=:name;",
                        {"name": test_case_name}
                    )
                    source_data = source_cursor.fetchall()

                    if source_data:
                        max_count = max(row[1] for row in source_data)

                        self.cursor_merge.execute(
                            f"SELECT count FROM {table[0]} WHERE name=:name;",
                            {"name": test_case_name}
                        )
                        current_count = self.cursor_merge.fetchone()

                        if current_count is not None and current_count[0] >= max_count:
                            continue

                        self.cursor_merge.execute(
                            f"DELETE FROM {table[0]} WHERE name=:name;",
                            {"name": test_case_name}
                        )
                        self.cursor_merge.executemany(
                            f"INSERT INTO {table[0]} (name, duration, count, result) VALUES (?, ?, ?, ?);",
                            [(test_case_name, row[0], row[1], row[2]) for row in source_data]
                        )
                        self.conn_merge.commit()

        source_cursor.close()
        source_conn.close()
        self._close()


class MergeParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(description='Script to merge test results data base files', add_help=True)

        self.add_argument("-o", "--output", type=str, help="Path to output .db file.")
        self.add_argument("paths", nargs='+', default=None,
                          help="Paths to .db files.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(
            f'Usage:\n$ python3 {sys.argv[0]} path/to/input1.db path/to/input2.db ... -o path/to/output.db')

    parser = MergeParser()
    arg = parser.parse_args()

    if arg.output:
        merged_db_file = arg.output
    else:
        merged_db_file = DATABASE_FILE

    database_files = arg.paths

    TEST_CASE_DB = TestCaseTable(database_files, merged_db_file)

    if os.path.exists(TEST_CASE_DB.merged_database_file):
        os.remove(merged_db_file)

    TEST_CASE_DB.merge_databases()
