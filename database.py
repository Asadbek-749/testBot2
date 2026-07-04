import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import config
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.is_postgres = bool(config.DATABASE_URL)
        if self.is_postgres:
            self.conn = psycopg2.connect(config.DATABASE_URL)
        else:
            self.conn = sqlite3.connect(config.SQLITE_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        
        self.create_tables()

    def get_cursor(self):
        if self.is_postgres:
            return self.conn.cursor(cursor_factory=RealDictCursor)
        return self.conn.cursor()

    @contextmanager
    def transaction(self):
        cursor = self.get_cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cursor.close()

    def create_tables(self):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS questions (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        opt1 TEXT NOT NULL,
                        opt2 TEXT NOT NULL,
                        opt3 TEXT NOT NULL,
                        correct_id INTEGER NOT NULL,
                        topic TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS results (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        name TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS active_polls (
                        poll_id TEXT PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        correct_option_id INTEGER NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS poll_answers (
                        id SERIAL PRIMARY KEY,
                        poll_id TEXT NOT NULL,
                        user_id BIGINT NOT NULL,
                        user_name TEXT NOT NULL,
                        is_correct BOOLEAN NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS certificates (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        name TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        text TEXT NOT NULL,
                        opt1 TEXT NOT NULL,
                        opt2 TEXT NOT NULL,
                        opt3 TEXT NOT NULL,
                        correct_id INTEGER NOT NULL,
                        topic TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS active_polls (
                        poll_id TEXT PRIMARY KEY,
                        chat_id INTEGER NOT NULL,
                        correct_option_id INTEGER NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS poll_answers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        poll_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT NOT NULL,
                        is_correct BOOLEAN NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS certificates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        topic TEXT NOT NULL,
                        date DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

    def add_question(self, text, opt1, opt2, opt3, correct_id, topic):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute(
                    "INSERT INTO questions (text, opt1, opt2, opt3, correct_id, topic) VALUES (%s, %s, %s, %s, %s, %s)",
                    (text, opt1, opt2, opt3, correct_id, topic)
                )
            else:
                cur.execute(
                    "INSERT INTO questions (text, opt1, opt2, opt3, correct_id, topic) VALUES (?, ?, ?, ?, ?, ?)",
                    (text, opt1, opt2, opt3, correct_id, topic)
                )

    def get_topics(self):
        with self.transaction() as cur:
            cur.execute("SELECT DISTINCT topic FROM questions")
            rows = cur.fetchall()
            return [row['topic'] if self.is_postgres else row[0] for row in rows]

    def get_questions_by_topic(self, topic):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute("SELECT * FROM questions WHERE topic = %s", (topic,))
            else:
                cur.execute("SELECT * FROM questions WHERE topic = ?", (topic,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
            
    def get_all_questions(self):
        with self.transaction() as cur:
            cur.execute("SELECT * FROM questions")
            rows = cur.fetchall()
            return [dict(row) for row in rows]
            
    def delete_question(self, q_id):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute("DELETE FROM questions WHERE id = %s", (q_id,))
            else:
                cur.execute("DELETE FROM questions WHERE id = ?", (q_id,))

    def delete_all_questions(self):
        with self.transaction() as cur:
            cur.execute("DELETE FROM questions")

    def delete_topic(self, topic):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute("DELETE FROM questions WHERE topic = %s", (topic,))
            else:
                cur.execute("DELETE FROM questions WHERE topic = ?", (topic,))

    def get_stats(self):
        with self.transaction() as cur:
            cur.execute("SELECT COUNT(*) FROM questions")
            q_count = cur.fetchone()['count' if self.is_postgres else 0] if self.is_postgres else cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(DISTINCT user_id) FROM results")
            u_count = cur.fetchone()['count' if self.is_postgres else 0] if self.is_postgres else cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM results")
            r_count = cur.fetchone()['count' if self.is_postgres else 0] if self.is_postgres else cur.fetchone()[0]
            
            return q_count, u_count, r_count

    def add_active_poll(self, poll_id, chat_id, correct_option_id):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute(
                    "INSERT INTO active_polls (poll_id, chat_id, correct_option_id) VALUES (%s, %s, %s)",
                    (poll_id, chat_id, correct_option_id)
                )
            else:
                cur.execute(
                    "INSERT INTO active_polls (poll_id, chat_id, correct_option_id) VALUES (?, ?, ?)",
                    (poll_id, chat_id, correct_option_id)
                )

    def get_active_poll(self, poll_id):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute("SELECT * FROM active_polls WHERE poll_id = %s", (poll_id,))
            else:
                cur.execute("SELECT * FROM active_polls WHERE poll_id = ?", (poll_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def add_poll_answer(self, poll_id, user_id, user_name, is_correct):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute(
                    "INSERT INTO poll_answers (poll_id, user_id, user_name, is_correct) VALUES (%s, %s, %s, %s)",
                    (poll_id, user_id, user_name, is_correct)
                )
            else:
                cur.execute(
                    "INSERT INTO poll_answers (poll_id, user_id, user_name, is_correct) VALUES (?, ?, ?, ?)",
                    (poll_id, user_id, user_name, is_correct)
                )

    def get_test_results(self, poll_ids):
        if not poll_ids:
            return []
        
        with self.transaction() as cur:
            placeholders = ','.join(['%s' if self.is_postgres else '?'] * len(poll_ids))
            query = f"""
                SELECT user_id, MAX(user_name) as name, SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as score
                FROM poll_answers
                WHERE poll_id IN ({placeholders})
                GROUP BY user_id
                ORDER BY score DESC
            """
            cur.execute(query, tuple(poll_ids))
            rows = cur.fetchall()
            return [dict(row) for row in rows]
            
    def save_final_results(self, results_data, topic):
        with self.transaction() as cur:
            for res in results_data:
                if res['score'] > 0:
                    if self.is_postgres:
                        cur.execute(
                            "INSERT INTO results (user_id, name, topic, score) VALUES (%s, %s, %s, %s)",
                            (res['user_id'], res['name'], topic, res['score'])
                        )
                    else:
                        cur.execute(
                            "INSERT INTO results (user_id, name, topic, score) VALUES (?, ?, ?, ?)",
                            (res['user_id'], res['name'], topic, res['score'])
                        )

    def get_user_stats(self, user_id):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute("SELECT topic, MAX(score) as max_score, COUNT(*) as attempts FROM results WHERE user_id = %s GROUP BY topic", (user_id,))
            else:
                cur.execute("SELECT topic, MAX(score) as max_score, COUNT(*) as attempts FROM results WHERE user_id = ? GROUP BY topic", (user_id,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def get_group_rating(self, topic):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute("SELECT name, MAX(score) as max_score FROM results WHERE topic = %s GROUP BY user_id, name ORDER BY max_score DESC LIMIT 10", (topic,))
            else:
                cur.execute("SELECT name, MAX(score) as max_score FROM results WHERE topic = ? GROUP BY user_id, name ORDER BY max_score DESC LIMIT 10", (topic,))
            rows = cur.fetchall()
            return [dict(row) for row in rows]

    def issue_certificate(self, user_id, name, topic):
        with self.transaction() as cur:
            if self.is_postgres:
                cur.execute(
                    "INSERT INTO certificates (user_id, name, topic) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, name, topic)
                )
                cert_id = cur.fetchone()['id']
            else:
                cur.execute(
                    "INSERT INTO certificates (user_id, name, topic) VALUES (?, ?, ?)",
                    (user_id, name, topic)
                )
                cert_id = cur.lastrowid
            return cert_id

    def get_all_chats_and_users(self):
        with self.transaction() as cur:
            cur.execute("SELECT DISTINCT chat_id FROM active_polls")
            chats = [row['chat_id'] if self.is_postgres else row[0] for row in cur.fetchall()]
            
            cur.execute("SELECT DISTINCT user_id FROM results")
            users = [row['user_id'] if self.is_postgres else row[0] for row in cur.fetchall()]
            
            # Combine and remove duplicates
            return list(set(chats + users))

db = Database()
