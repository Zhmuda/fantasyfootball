import psycopg2
from contextlib import contextmanager

class DBManager:
    def __init__(self, dbname, user, password):
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password)
        self.cur = self.conn.cursor()

    def execute_query(self, query, params=None):
        """ Выполняет запрос и возвращает результат (если есть). """
        self.cur.execute(query, params)
        if self.cur.description:  # Если есть результаты (например, SELECT)
            return self.cur.fetchall()
        return None

    def execute_non_query(self, query, params=None):
        """ Выполняет запрос без возвращения результата (например, INSERT, UPDATE). """
        self.cur.execute(query, params)
        self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()
