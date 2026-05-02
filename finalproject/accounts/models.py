from django.db import models, connection


class AccountManager(models.Manager["Account"]):

    def create_user_with_raw_sql(self, name, email, password, role):
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO users (name, email, password, role)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, [name, email, password, role])

    def login_with_raw_sql(self, email, password):
        with connection.cursor() as cursor:
            sql = """
                SELECT user_id, name, email, role
                FROM users
                WHERE email = %s AND password = %s
            """
            cursor.execute(sql, [email, password])
            row = cursor.fetchone()

            if not row:
                return None

            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))


class Account(models.Model):
    class Meta:
        db_table = 'users'
        managed = False

    objects: AccountManager = AccountManager()