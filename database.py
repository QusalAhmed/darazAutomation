import psycopg2


class Connection:
    def __init__(self):
        self.conn = psycopg2.connect(database='choate', user='postgres', password='qusal',
                                     host='localhost', port=5432)
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
