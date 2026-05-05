import sqlite3
from datetime import date, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "expenses.db"

DEFAULT_CATEGORIES = [
    "Food",
    "Travel",
    "Rent",
    "Entertainment",
    "Shopping",
    "Health",
    "Education",
    "Other",
]


def get_connection():
    """Return a SQLite connection with dictionary-like rows and FK support."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables, seed categories, and add starter data on first run."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK (amount > 0),
                category_id INTEGER NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
            """
        )
        seed_categories(conn)
        seed_sample_transactions(conn)
        conn.commit()


def seed_categories(conn):
    for name in DEFAULT_CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            (name,),
        )


def seed_sample_transactions(conn):
    existing = conn.execute("SELECT COUNT(*) AS count FROM transactions").fetchone()
    if existing["count"] > 0:
        return

    categories = {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM categories")
    }
    current_month = date.today().replace(day=1)
    previous_month = subtract_months(current_month, 1)
    two_months_ago = subtract_months(current_month, 2)

    samples = [
        ("income", 4200.00, "Other", "Monthly salary", safe_day(current_month, 1)),
        ("expense", 1200.00, "Rent", "Apartment rent", safe_day(current_month, 2)),
        ("expense", 185.40, "Food", "Groceries and pantry", safe_day(current_month, 4)),
        ("expense", 42.75, "Travel", "Metro card recharge", safe_day(current_month, 5)),
        ("expense", 69.99, "Entertainment", "Streaming and movies", safe_day(current_month, 7)),
        ("income", 350.00, "Other", "Freelance invoice", safe_day(current_month, 10)),
        ("expense", 94.20, "Health", "Pharmacy and checkup", safe_day(current_month, 12)),
        ("expense", 210.00, "Shopping", "Work shoes", safe_day(current_month, 15)),
        ("income", 4200.00, "Other", "Monthly salary", safe_day(previous_month, 1)),
        ("expense", 1200.00, "Rent", "Apartment rent", safe_day(previous_month, 2)),
        ("expense", 244.80, "Food", "Groceries", safe_day(previous_month, 6)),
        ("expense", 135.00, "Education", "Online course", safe_day(previous_month, 9)),
        ("expense", 87.50, "Travel", "Fuel and parking", safe_day(previous_month, 13)),
        ("income", 180.00, "Other", "Cashback and rewards", safe_day(previous_month, 18)),
        ("expense", 156.25, "Shopping", "Home supplies", safe_day(previous_month, 22)),
        ("income", 4200.00, "Other", "Monthly salary", safe_day(two_months_ago, 1)),
        ("expense", 1200.00, "Rent", "Apartment rent", safe_day(two_months_ago, 2)),
        ("expense", 198.35, "Food", "Groceries and dining", safe_day(two_months_ago, 8)),
        ("expense", 74.00, "Entertainment", "Concert ticket", safe_day(two_months_ago, 14)),
        ("expense", 66.40, "Health", "Vitamins", safe_day(two_months_ago, 20)),
    ]

    conn.executemany(
        """
        INSERT INTO transactions (type, amount, category_id, description, date)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (kind, amount, categories[category], description, tx_date.isoformat())
            for kind, amount, category, description, tx_date in samples
        ],
    )


def subtract_months(value, months):
    month = value.month - months
    year = value.year
    while month > 12:
        month -= 12
        year += 1
    while month <= 0:
        month += 12
        year -= 1
    return value.replace(year=year, month=month, day=1)


def safe_day(month_start, day):
    next_month = subtract_months(month_start, -1)
    last_day = next_month - timedelta(days=1)
    return month_start.replace(day=min(day, last_day.day))
