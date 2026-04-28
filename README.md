<div align="center">

# 📚 Library Management System

### A full-featured, role-based Library Management System built with Django

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*Empowering librarians and students with a smart, efficient, and modern library experience.*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Highlights](#-key-highlights)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Roles & Access](#-roles--access)
- [Fine Policy](#-fine-policy)
- [Future Enhancements](#-future-enhancements)
- [Author](#-author)

---

## 🌟 Overview

The **Library Management System** is a robust, full-stack web application built with **Django** that streamlines every aspect of library operations. It supports two distinct roles — **Librarian** and **Student** — each with a dedicated dashboard and a carefully crafted set of features.

From managing the book catalog and physical copies to handling circulation, renewal requests, overdue fine calculations, and QR-based student identification, this system covers the complete lifecycle of a library transaction.

---

## ✨ Key Highlights

| Feature | Description |
|---|---|
| 🔐 Role-Based Access | Separate dashboards and permissions for Librarians and Students |
| 📖 Book Copy Inventory | Each book tracks individual physical copies with unique barcodes |
| 🔄 Full Issue Workflow | Request → Approve/Reject → Issue → Return, all in one system |
| 📅 Renewal Management | Students can request renewals; librarians approve or reject |
| 💰 Tiered Fine System | Automated, tiered fine calculation for overdue books |
| 🔍 Advanced Search | Search books by title, author, category, or ISBN |
| ⚡ Circulation Desk | Fast check-in / check-out via ISBN or barcode scan |
| 📲 QR Profile | Auto-generated QR code for instant student identification |
| 🔒 Atomic Transactions | Race-condition-safe book issuing using `transaction.atomic` |

---

## 🚀 Features

### 👨‍🎓 Student

- Register and log in to a personal account
- Browse and search the full book catalog
- Request books and track request status
- View currently issued books with due dates
- Submit renewal requests with a reason
- View complete borrowing history
- Live overdue fine/dues tracking
- Generate a QR code containing profile details (name, roll number, branch, email)

### 👩‍💼 Librarian

- Add, update, and delete books and manage physical copy inventory
- Issue books directly to students
- Approve or reject student book requests (auto-issues to waitlisted students on return)
- Process book returns with automatic fine calculation
- Approve or reject renewal requests and set new due dates
- **Circulation Desk** — fast check-in / check-out using ISBN or barcode
- Dashboard statistics at a glance:
  - 📚 Total books in catalog
  - 📋 Active issues
  - ⚠️ Overdue books
  - 👥 Total registered students

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django (Python) |
| **Database** | PostgreSQL *(defaultl)* |
| **Frontend** | HTML5 · CSS3 · JavaScript |
| **QR Generation** | `qrcode` Python library *(with frontend fallback)* |
| **Auth** | Django built-in authentication + custom `Profile` model |

---

## 📁 Project Structure

```
Library-Management-System-using-Django/
│
├── lms_project/               # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── library/                   # Core application
│   ├── models.py              # Profile, Book, BookCopy, BookIssue, BookRequest, BookRenewal
│   ├── views.py               # All business logic and view handlers
│   ├── forms.py               # Django forms
│   ├── urls.py                # App-level URL routing
│   ├── signals.py             # Django signals (e.g., auto-create Profile)
│   ├── admin.py               # Django admin registrations
│   ├── templates/             # HTML templates
│   └── migrations/            # Database migration files
│
├── templates/
│   └── registration/          # Login / signup templates
│
├── manage.py
├── db.sqlite3
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Sh-aran13/Library-Management-System-using-Django.git
cd Library-Management-System-using-Django

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Create a superuser (Librarian / Admin)
python manage.py createsuperuser

# 6. Start the development server
python manage.py runserver
```

Open your browser and navigate to **http://127.0.0.1:8000/**

> **Note:** To enable QR code generation, ensure the `qrcode` package is installed (`pip install qrcode[pil]`). If unavailable, the UI automatically falls back to a frontend-based QR renderer.

---

## 🔑 Roles & Access

| Role | Registration | Book Catalog | Request Books | Issue / Return | Manage Users | Fine Collection |
|---|---|---|---|---|---|---|
| **Student** | ✅ Self-register | ✅ Browse & Search | ✅ | ❌ | ❌ | View only |
| **Librarian** | Admin assigns | ✅ Full CRUD | ✅ Approve/Reject | ✅ Full control | ✅ | ✅ |

---

## 💰 Fine Policy

Overdue fines are calculated automatically using a **tiered rate structure**:

| Overdue Period | Rate |
|---|---|
| Days 1 – 7 | ₹2 per day |
| Days 8 – 30 | ₹5 per day *(cumulative)* |
| Days 31+ | ₹10 per day *(cumulative)* |

> Example: 35 days overdue → ₹14 (week 1) + ₹115 (days 8–30) + ₹50 (days 31–35) = **₹179**

---

## 🔮 Future Enhancements

- [ ] 💳 Online fine payments (Razorpay / Stripe integration)
- [ ] 📧 Email & SMS notifications for due dates and overdue alerts
- [ ] 🤖 AI-powered book recommendation engine
- [ ] 📱 Mobile app integration (React Native / Flutter)
- [ ] 📊 Advanced reporting & analytics dashboard
- [ ] 🌐 Multi-branch library support
- [ ] 📷 Book cover image upload

---

## 👨‍💻 Author

<div align="center">

**Allada Sai Satya Sharan**

[![GitHub](https://img.shields.io/badge/GitHub-Sh--aran13-181717?style=for-the-badge&logo=github)](https://github.com/Sh-aran13)

*Built with ❤️ using Django*

</div>
