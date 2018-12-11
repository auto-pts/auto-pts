import sqlite3

DATABASE_FILE = 'TestCase.db'


class TestCaseTable(object):
    def __init__(self, name):
        self._open()
        self.name = name

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS {} (name TEXT, duration REAL, "
            "count INTEGER, result TEXT);".format(self.name))
        self.conn.commit()

        self._close()

    def _open(self):
        self.conn = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.conn.cursor()

    def _close(self):
        self.cursor.close()
        self.conn.close()

    def update_statistics(self, test_case_name, duration, result):
        self._open()

        self.cursor.execute(
            "SELECT duration, count FROM {} "
            "WHERE name=:name;".format(self.name), {"name": test_case_name})
        row = self.cursor.fetchall()
        if len(row) == 0:
            self.cursor.execute(
                "INSERT INTO {} VALUES(?, ?, ?, ?);".format(self.name),
                (test_case_name, duration, 1, result))
            self.conn.commit()
            return

        (mean, count) = row[0]
        if not count:
            count = 0
            mean = 0

        count += 1
        mean += (duration - mean) / count

        self.cursor.execute(
            "UPDATE {} SET duration=:duration, count=:count, result=:result "
            "WHERE name=:name".format(self.name), {"duration": mean,
                                                   "count": count,
                                                   "name": test_case_name,
                                                   "result": result})
        self.conn.commit()
        self._close()

    def get_mean_duration(self, test_case_name):
        self._open()

        self.cursor.execute(
            "SELECT duration FROM {} "
            "WHERE name=:name;".format(self.name), {"name": test_case_name})
        row = self.cursor.fetchone()
        if row is not None:
            return row[0]

        self._close()

    def get_result(self, test_case_name):
        self._open()

        self.cursor.execute(
            "SELECT result FROM {} "
            "WHERE name=:name".format(self.name), {"name": test_case_name})
        row = self.cursor.fetchone()
        if row is not None:
            return row[0]

        self._close()

    def estimate_session_duration(self, test_cases_names, run_count_max):
        duration = 0
        count_unknown = 0
        num_test_cases = len(test_cases_names)

        for test_case_name in test_cases_names:
            expected_run_count = 1

            # Assume worst case scenario
            last_result = self.get_result(test_case_name)
            if last_result and last_result != 'PASS':
                expected_run_count = run_count_max

            mean_time = self.get_mean_duration(test_case_name)
            if mean_time is None:
                count_unknown += 1
            else:
                duration += mean_time * expected_run_count

        if (num_test_cases - count_unknown) != 0:
            duration += count_unknown * duration / (num_test_cases - count_unknown)

        return duration

