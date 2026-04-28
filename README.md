# Library Management System using Django

A role-based Library Management System built with **Django** that helps librarians manage books and circulation, and helps students browse, request, renew, and track dues/fines.

---

## Highlights

- Student & Librarian roles (role-based dashboards)
- Book catalog management (CRUD)
- Request → Approve/Reject → Issue workflow
- Renewal requests with approval flow
- Return handling + overdue fine calculation
- Search & filtering across books and issues
- Circulation desk for quick check-in/check-out
- QR-based student profile access

---

## Features

### Student

- Register / Login
- Browse & search books
- Request books
- View currently issued books & due dates
- Request renewal
- View borrowing history
- Live fine/dues calculation for overdue books
- Generate QR code for quick profile identification

### Librarian

- Add / update / delete books
- Issue books to students
- Manage book requests (approve / reject)
- Handle returns
- Approve / reject renewal requests
- Circulation desk operations (fast check-in / check-out using ISBN/barcode)
- Dashboard stats
  - Total books
  - Active issues
  - Overdue books
  - Total students

---

## Core Modules

### Dashboard

- **Librarian Dashboard**: statistics + recent activity
- **Student Dashboard**: active borrowings + fine tracking

### Book Management

- Full CRUD for books
- Search by **Title**, **Author**, **Category**, **ISBN**

### Issue & Return

- Safe issuing with `transaction.atomic`
- Prevents over-issuing
- Tracks issue date, due date, and return status
- Fine calculation based on overdue days

### Requests & Renewals

- Students can request books
- Librarian can approve (issue) or reject
- Renewal requests are validated to prevent duplicate pending renewals

### QR Profile

- Generates a QR code containing student profile details (name, roll number, branch, email)
- If the Python `qrcode` library is unavailable, the UI falls back to a frontend-based QR

---

## Tech Stack

- **Backend**: Django
- **Database**: SQLite (default) / PostgreSQL (optional)
- **Frontend**: HTML, CSS, JavaScript
- **Key Django Concepts**: ORM filtering (`filter`, `select_related`), `Q` objects, JSON responses (`JsonResponse`)

---

## Project Structure (simplified)

```
library/
├── models.py        # Book, Issue, Request, Renewal models
├── views.py         # Core business logic
├── forms.py         # Django forms
├── templates/       # HTML templates
└── static/          # CSS / JS
```

---

## Installation & Setup

```bash
# clone
git clone https://github.com/Sh-aran13/Library-Management-System-using-Django.git
cd Library-Management-System-using-Django

# install dependencies
pip install -r requirements.txt

# migrate
python manage.py migrate

# create admin user
python manage.py createsuperuser

# run
python manage.py runserver
```

---

## Default Roles

| Role | Access |
|------|--------|
| Student | Limited |
| Librarian | Full control |

---

## Future Enhancements

- Online fine payments
- Email notifications
- Book recommendations
- Mobile app integration
- AI-based search

---

## Author

Developed by **Allada Sai Satya Sharan**
