# -*- coding: utf-8 -*-

import MySQLdb
from MySQLdb import Error

from warnings import filterwarnings
filterwarnings("ignore")


class MysqlManager(object):
    def __init__(self, db_info):
        self.db_info = db_info
        self.db_connection = None
        self._connect_to_mysql()

    def _connect_to_mysql(self):
        if self.db_connection:
            self.db_connection.close()
            del self.db_connection

        try:
            self.db_connection = MySQLdb.connect(**self.db_info)
        except Exception as e:
            raise e

    def _get_cursor(self):
        try:
            self.db_connection.ping(True)
        except Error as e:
            self._connect_to_mysql()
        finally:
            return self.db_connection.cursor()

    def query(self, sql):
        cursor = self._get_cursor()
        try:
            cursor.execute(sql, None)
            self.db_connection.commit()
            result = cursor.fetchall()
        except Error as e:
            cursor.close()
            return False, str(e)
        cursor.close()
        return True, result

    def query_one(self, sql):
        cursor = self._get_cursor()
        try:
            cursor.execute(sql, None)
            self.db_connection.commit()
            result = cursor.fetchone()
        except Error as e:
            cursor.close()
            return False, str(e)
        cursor.close()
        return True, result

    def execute(self, sql, param=None):
        cursor = self._get_cursor()
        try:
            cursor.execute(sql, param)
            self.db_connection.commit()
            affected_rows = cursor.rowcount
        except Error as e:
            cursor.close()
            self.db_connection.rollback()
            return False, str(e)
        cursor.close()
        return True, affected_rows

    def executemany(self, sql, param=None):
        cursor = self._get_cursor()
        try:
            cursor.executemany(sql, param)
            self.db_connection.commit()
            affected_rows = cursor.rowcount
        except Error as e:
            cursor.close()
            self.db_connection.rollback()
            return False, str(e)
        cursor.close()
        return True, affected_rows

    def close(self):
        try:
            self.db_connection.close()
        except:
            pass

if __name__ == '__main__':
    pass

