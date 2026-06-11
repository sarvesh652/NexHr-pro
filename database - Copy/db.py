import sqlite3
from flask import current_app, g
from werkzeug.security import generate_password_hash

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(current_app.config['DATABASE'])
    db.row_factory = sqlite3.Row

    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'hr', 'manager')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            salary INTEGER NOT NULL,
            performance_score INTEGER DEFAULT 0,
            experience_years INTEGER DEFAULT 0,
            task_completion INTEGER DEFAULT 70,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            ai_score INTEGER,
            recommendation TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('present', 'absent', 'late', 'wfh')),
            marked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            UNIQUE(employee_id, date)
        );

        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            skill_score REAL DEFAULT 0,
            experience_years INTEGER DEFAULT 0,
            interview_score REAL DEFAULT 0,
            status TEXT DEFAULT 'applied' CHECK(status IN ('applied', 'shortlisted', 'interviewed', 'offered', 'rejected')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Seed default users
    existing = db.execute("SELECT id FROM users WHERE email = 'admin@hrpro.com'").fetchone()
    if not existing:
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ('Super Admin', 'admin@hrpro.com', generate_password_hash('Admin@123'), 'admin')
        )
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ('HR Manager', 'hr@hrpro.com', generate_password_hash('Hr@123'), 'hr')
        )
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ('Team Manager', 'manager@hrpro.com', generate_password_hash('Manager@123'), 'manager')
        )
        # Seed sample employees
        employees = [
            ('Alice Johnson', 'alice@hrpro.com', '+1-555-0101', 'Engineering', 'Senior Developer', 95000, 88, 6, 92),
            ('Bob Chen', 'bob@hrpro.com', '+1-555-0102', 'Engineering', 'Backend Developer', 82000, 75, 3, 78),
            ('Carol White', 'carol@hrpro.com', '+1-555-0103', 'Marketing', 'Marketing Lead', 78000, 91, 5, 88),
            ('David Kim', 'david@hrpro.com', '+1-555-0104', 'Sales', 'Sales Executive', 68000, 62, 2, 65),
            ('Emma Davis', 'emma@hrpro.com', '+1-555-0105', 'HR', 'HR Specialist', 72000, 85, 4, 90),
            ('Frank Miller', 'frank@hrpro.com', '+1-555-0106', 'Finance', 'Financial Analyst', 88000, 79, 7, 82),
            ('Grace Lee', 'grace@hrpro.com', '+1-555-0107', 'Engineering', 'Frontend Developer', 80000, 93, 4, 95),
            ('Henry Brown', 'henry@hrpro.com', '+1-555-0108', 'Marketing', 'Content Strategist', 65000, 70, 2, 71),
        ]
        db.executemany(
            "INSERT INTO employees (name, email, phone, department, designation, salary, performance_score, experience_years, task_completion) VALUES (?,?,?,?,?,?,?,?,?)",
            employees
        )
        # Seed sample candidates
        candidates = [
            ('Raj Kumar', 'raj@mail.com', 'Engineering', 72, 3, 68, 'shortlisted'),
            ('Priya Singh', 'priya@mail.com', 'Marketing', 85, 5, 80, 'interviewed'),
            ('Arun Patel', 'arun@mail.com', 'Finance', 60, 1, 55, 'applied'),
            ('Sona Mathew', 'sona@mail.com', 'HR', 90, 6, 88, 'offered'),
            ('Vikram Nair', 'vikram@mail.com', 'Engineering', 45, 0, 50, 'rejected'),
        ]
        db.executemany(
            "INSERT INTO candidates (name, email, department, skill_score, experience_years, interview_score, status) VALUES (?,?,?,?,?,?,?)",
            candidates
        )
        # Seed attendance for today
        import datetime
        today = datetime.date.today().isoformat()
        attendance_data = [
            (1, today, 'present'),
            (2, today, 'present'),
            (3, today, 'wfh'),
            (4, today, 'late'),
            (5, today, 'present'),
            (6, today, 'absent'),
            (7, today, 'present'),
            (8, today, 'wfh'),
        ]
        db.executemany(
            "INSERT OR IGNORE INTO attendance (employee_id, date, status) VALUES (?,?,?)",
            attendance_data
        )
    db.commit()
    db.close()
