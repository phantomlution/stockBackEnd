import pymysql.cursors

host = 'localhost'
user = 'root'
password = 'root'
db = 'stock'

class MySQL(object):
    def __init__(self):
        self.connection = pymysql.connect(host=host,
                             user=user,
                             password=password,
                             db=db,
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    def execute(self, sql, params):
        with self.connection.cursor() as cursor:
            affected_row = cursor.execute(sql, params)
        self.connection.commit()
        return affected_row

    def find(self, sql, params):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchone()
        return result

    def findAll(self, sql, params):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
        return result

    def close(self):
        self.connection.close()