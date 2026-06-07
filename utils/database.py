import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fitness.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS body_parts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS exercises (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    body_part_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    FOREIGN KEY (body_part_id) REFERENCES body_parts(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS workout_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    exercise_id INTEGER NOT NULL,
                    sets INTEGER DEFAULT 1,
                    reps INTEGER DEFAULT 0,
                    weight REAL DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (exercise_id) REFERENCES exercises(id)
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS food_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    food_name TEXT NOT NULL,
                    amount_g REAL DEFAULT 100,
                    calories REAL DEFAULT 0,
                    protein REAL DEFAULT 0,
                    carbs REAL DEFAULT 0,
                    fat REAL DEFAULT 0
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS body_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    weight REAL,
                    neck REAL,
                    waist REAL,
                    hip REAL,
                    body_fat REAL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS stretch_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    video_url TEXT,
                    category TEXT,
                    date_added TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    note TEXT
                )''')

    conn.commit()
    conn.close()

def init_default_data():
    conn = get_conn()
    c = conn.cursor()

    parts = ["肱三头", "肱二头", "腹", "腿", "背", "胸", "肩", "功能性练习"]
    for part in parts:
        c.execute("INSERT OR IGNORE INTO body_parts (name) VALUES (?)", (part,))

    default_exercises = {
        "背": ["高位下拉", "反手下拉", "引体向上", "哑铃划船", "坐姿划船"],
        "胸": ["杠铃卧推", "哑铃飞鸟", "上斜卧推", "绳索夹胸"],
        "腿": ["深蹲", "腿举", "腿弯举", "罗马尼亚硬拉", "箭步蹲"],
        "肩": ["哑铃推举", "侧平举", "前平举", "面拉"],
        "肱二头": ["杠铃弯举", "哑铃弯举", "锤式弯举"],
        "肱三头": ["绳索下压", "窄距卧推", "臂屈伸"],
        "腹": ["卷腹", "平板支撑", "悬垂举腿", "俄罗斯转体"],
        "功能性练习": ["波比跳", "壶铃摇摆", "战绳", "药球砸地"]
    }

    for part_name, exercise_list in default_exercises.items():
        c.execute("SELECT id FROM body_parts WHERE name=?", (part_name,))
        row = c.fetchone()
        if row:
            part_id = row["id"]
            for ex in exercise_list:
                c.execute("INSERT OR IGNORE INTO exercises (body_part_id, name) VALUES (?, ?)",
                          (part_id, ex))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    init_default_data()
    print("数据库初始化完成！")