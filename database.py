import json
import sqlite3
import pandas as pd

con = sqlite3.connect('database.db')
cursor = con.cursor()


def start_command(user_id):
    if not (user_id,) in cursor.execute('SELECT user_id FROM user_info').fetchall():
        cursor.execute(f"INSERT INTO 'user_info'(user_id) VALUES('{user_id}')")
        con.commit()


def new_broadcast():
    last = cursor.execute(f'SELECT id FROM broadcast').fetchall()[-1][0] + 1
    cursor.execute(f"INSERT INTO 'broadcast'(id) VALUES({last})")
    cursor.execute(f"CREATE TABLE '{last}'(user_id INT)")
    con.commit()

    return last


def export_sheet():
    df = pd.read_sql_query("SELECT * FROM user_info", sqlite3.connect('database.db'))
    df.to_excel('Пользователи.xlsx')


def all_users():
    return [i[0] for i in cursor.execute(f'SELECT user_id FROM user_info').fetchall()]


def set_username(user_id, username):
    cursor.execute(f'UPDATE user_info SET username = "{username}" WHERE user_id = {user_id}')
    con.commit()


def ban(user_id):
    username = cursor.execute(f'SELECT username FROM user_info WHERE user_id = "{user_id}"').fetchall()[0][0]

    cursor.execute(f'INSERT INTO ban("id", "username") VALUES({user_id}, "{username}")')
    con.commit()


def check_ban(user_id):
    a = cursor.execute(f'SELECT id FROM ban WHERE id = {user_id}').fetchall()
    return bool(a)


def unban(user_id):
    cursor.execute(f'DELETE FROM ban WHERE id = {user_id}')
    con.commit()


if __name__ == '__main__':
    pass
    # print(send_custom(1132908805))
