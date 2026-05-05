<![CDATA[<div align="center">

# 💰 Expense Tracker

<p>
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
  <img src="https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" alt="Chart.js" />
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/ReportLab-PDF-red?style=for-the-badge" alt="ReportLab" />
</p>

**A full-featured personal finance web application built with Flask, SQLite, and Chart.js.**  
Track income & expenses, visualize spending trends, and export professional reports — all from a sleek, responsive dashboard.

---

</div>

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **User Authentication** | Secure register & login with hashed passwords (Werkzeug) and session management |
| 📊 **Interactive Dashboard** | Real-time summary cards for Income, Expenses, and Net Savings with month selection |
| 🍩 **Category Doughnut Chart** | Visual breakdown of expenses by category using Chart.js |
| 📈 **6-Month Trend Chart** | Side-by-side bar chart comparing Income vs Expense over the last 6 months |
| ➕ **Add Transactions** | Add income or expense entries with amount, category, description, and date |
| 📜 **Transaction History** | View, filter (by month/type/category), and delete past transactions |
| 📁 **CSV Export** | Download transaction data as a `.csv` file for any selected month |
| 📄 **PDF Reports** | Generate styled PDF reports with summary, category breakdown, and transaction table using ReportLab |
| 📱 **Fully Responsive** | Mobile-first sidebar with hamburger menu, adapts to all screen sizes |
| 🎨 **Modern Dark Sidebar UI** | Premium design with Inter font, smooth transitions, and a polished color palette |
| 🗂️ **8 Default Categories** | Food, Travel, Rent, Entertainment, Shopping, Health, Education, Other |
| 🌱 **Auto Seed Data** | Pre-populated sample transactions spanning 3 months for instant demo |

---

## 🏗️ Project Structure

```
expense_tracker/
│
├── app.py                  # Main Flask application (routes, auth, API endpoints)
├── database.py             # SQLite setup, table creation, seed data
├── reports.py              # CSV & PDF report generation (ReportLab)
├── users.json              # JSON-based user credential store
├── expenses.db             # SQLite database (auto-created on first run)
│
├── static/
│   ├── style.css           # Complete stylesheet (734 lines, responsive design)
│   └── script.js           # Dashboard charts, form validation, mobile menu
│
└── templates/
    ├── base.html            # Base layout with sidebar navigation
    ├── login.html           # Login page
    ├── register.html        # Registration page
    ├── dashboard.html       # Main dashboard with charts & recent transactions
    ├── add.html             # Add new transaction form
    ├── history.html         # Transaction history with filters
    └── reports.html         # Reports page with CSV/PDF export
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Flask (Python) | Web framework, routing, session auth |
| **Database** | SQLite3 | Lightweight relational data storage |
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Structure, styling, interactivity |
| **Charts** | Chart.js (CDN) | Doughnut & bar chart visualizations |
| **PDF Generation** | ReportLab | Styled PDF report export |
| **Auth Security** | Werkzeug | Password hashing (`generate_password_hash` / `check_password_hash`) |
| **User Storage** | JSON file (`users.json`) | Simple file-based user credentials |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.x** installed on your system
- **pip** (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/expense-tracker.git
   cd expense-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install flask reportlab
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open in browser**
   ```
   http://127.0.0.1:5001
   ```

> 💡 The database (`expenses.db`) and user file (`users.json`) are **auto-created** on the first run. Sample transactions spanning 3 months are seeded automatically for demo purposes.

---

## 📸 Pages Overview

| Page | Route | Description |
|------|-------|-------------|
| **Login** | `/login` | Authenticate with username & password |
| **Register** | `/register` | Create a new account (3–32 char username, 8+ char password) |
| **Dashboard** | `/` | Monthly summary cards, doughnut chart, trend chart, recent transactions |
| **Add Transaction** | `/add` | Form with type toggle (Income/Expense), amount, category, date, description |
| **History** | `/history` | Filterable transaction list with delete option and balance pill |
| **Reports** | `/reports` | Monthly report view with CSV & PDF export buttons |

---

## 🔌 API Endpoints

The app exposes three JSON API endpoints used by the dashboard charts:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/summary?month=YYYY-MM` | `GET` | Returns `{ income, expense, savings }` for the selected month |
| `/api/category-breakdown?month=YYYY-MM` | `GET` | Returns array of `{ category, total }` for expense categories |
| `/api/monthly-trend` | `GET` | Returns 6-month array of `{ month, income, expense }` |

---

## 📤 Export Options

| Format | Route | Details |
|--------|-------|---------|
| **CSV** | `/export/csv?month=YYYY-MM` | Downloads a `.csv` file with Date, Type, Category, Amount, Description columns |
| **PDF** | `/export/pdf?month=YYYY-MM` | Downloads a styled PDF with summary table, category breakdown, and full transaction list |

---

## 🗃️ Database Schema

```sql
-- Categories table
CREATE TABLE categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- Transactions table
CREATE TABLE transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL CHECK (type IN ('income', 'expense')),
    amount      REAL NOT NULL CHECK (amount > 0),
    category_id INTEGER NOT NULL,
    description TEXT,
    date        TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
```

**Default Categories:** Food · Travel · Rent · Entertainment · Shopping · Health · Education · Other

---

## 🎨 Design Highlights

- **Dark sidebar** (`#1e1e2e`) with active link highlighting using a violet accent (`#7c3aed`)
- **Summary cards** with green for income (`#22c55e`) and red for expenses (`#ef4444`)
- **Smooth 160ms transitions** on hover states, buttons, and navigation links
- **Responsive breakpoints** at `1040px`, `820px`, and `560px` for tablet and mobile
- **Auth pages** with a gradient background (`#1e1e2e → #334155`) and centered card layout
- **Inter font family** with `system-ui` fallback for clean, modern typography

---

## 🔒 Security Features

- ✅ Passwords hashed using Werkzeug's `generate_password_hash`
- ✅ Session-based authentication with `@app.before_request` guard
- ✅ Open redirect prevention via `safe_next_url()` validation
- ✅ Server-side + client-side form validation
- ✅ SQL injection protection via parameterized queries
- ✅ Foreign key constraints enforced (`PRAGMA foreign_keys = ON`)
- ✅ Delete confirmation dialog on the client side

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `flask` | Web framework (routing, templates, sessions) |
| `reportlab` | PDF report generation |

> Both are installable via: `pip install flask reportlab`  
> SQLite and Werkzeug come bundled with Python and Flask respectively.

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork this repository, open issues, or submit pull requests.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## 📝 License

This project is open source and available for personal and educational use.

---

<div align="center">

**⭐ Star this repo if you found it useful!**

Made with ❤️ using Python & Flask

</div>
]]>
