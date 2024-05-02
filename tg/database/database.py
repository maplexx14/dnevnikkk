import psycopg2
def ensure_connections(func):
    """ Декоратор для подключения к СУБД: открывает соединение,
            выполняет переданную функцию и закрывает за собой соединение.
            Потокобезопасно!
        """

    def inner(*args, **kwargs):
        with psycopg2.connect(dbname='schoolbot', user='postgres', password='123', host='localhost', port='5432') as conn:
            res = func(*args, conn=conn, **kwargs)
        return res

    return inner


@ensure_connections
def init_db(conn, force: bool = False):
    """ Проверить существование таблицы а иначе пересоздать её
           :param conn: подключение к СУБД
           :param force: явно пересоздать все таблицы
       """
    c = conn.cursor()
    if force:
        c.execute('DROP TABLE IF EXISTS users')
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER,
            nickname        VARCHAR(50),
            name            VARCHAR(20),
            surname         VARCHAR(20),
            class           VARCHAR(20),
            rating          FLOAT
        )
    ''')
    # Сохранить изменения
    conn.commit()


@ensure_connections
def reg_db(conn, user_id: int, nickname: str,name: str, surname: str, clas: str,
           rating: float):  # Добавление пользователя в таблицу users
    c = conn.cursor()
    c.execute(f"INSERT INTO users (id, nickname, name, surname, class, rating) VALUES ({user_id},'{nickname}', '{name}', '{surname}', '{clas}', {rating})")
    conn.commit()
@ensure_connections
def add_rating(conn, user_id: int, rating: float):  # Добавление рейтинга пользователя
    c = conn.cursor()
    c.execute(f"UPDATE users SET rating = {rating} WHERE id = {user_id}")
    conn.commit()

@ensure_connections
def edit_db(conn, user_id: int, name: str, old: int, gender: str,
            change: str):  # Пересоздание пользователя по user_id в таблицу users
    c = conn.cursor()
    c.execute('UPDATE users SET name=?,old=?,gender=?,change=? WHERE user_id = ?', (name, old, gender, change, user_id))
    conn.commit()

@ensure_connections
def get_rating(conn):  # Получение рейтинга пользователя
    c = conn.cursor()
    c.execute('SELECT * FROM users ORDER BY rating DESC')
    return c.fetchall()
@ensure_connections
def check_user(conn, user_id: int):  # Проверка существования пользователя с данным user_id
    c = conn.cursor()
    c.execute(f'SELECT EXISTS(SELECT * FROM users WHERE id = {user_id})')
    return c.fetchone()


@ensure_connections  # Удаление пользователя из таблицы users
def delete_user(conn, user_id: int):
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE user_id=?', (user_id,))
    conn.commit()


@ensure_connections
def get_info(conn, user_id: int):  # Получение всей информации о пользователе из таблицы users
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
    return c.fetchone()


if __name__ == '__main__':
    init_db()