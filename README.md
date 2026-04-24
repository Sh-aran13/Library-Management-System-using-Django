# 📚 Library Management System (Django)

A full-featured **Library Management System** built using Django that supports **student and librarian roles**, book issuing, requests, renewals, fine calculation, and QR-based profile access.

---

## 🚀 Features

### 👨‍🎓 Student Features

* Register & login as student
* Browse and search books
* Request books
* View issued books and due dates
* Request renewal of books
* Track fines (real-time calculation)
* View borrowing history
* Generate QR profile for quick identification

---

### 👨‍💼 Librarian Features

* Add, update, and delete books
* Issue books to students
* Manage book requests (approve/reject)
* Handle book returns
* Approve/reject renewal requests
* Circulation desk (quick check-in / check-out)
* View dashboard statistics:

  * Total books
  * Active issues
  * Overdue books
  * Total students

---

## ⚙️ Core Functionalities

### 📊 Dashboard

* Role-based dashboard:

  * **Librarian:** stats + recent issues
  * **Student:** current borrowings + fine tracking

---

### 📖 Book Management

* Create, update, delete books
* Search by:

  * Title
  * Author
  * Category
  * ISBN

---

### 🔄 Issue & Return System

* Atomic transactions for safe issuing
* Prevents over-issuing of books
* Tracks:

  * Issue date
  * Due date
  * Return status
* Fine calculation for overdue books

---

### 📩 Book Requests

* Students can request unavailable books
* Librarian can:

  * Approve → issue book
  * Reject request

---

### 🔁 Renewal System

* Students request renewal
* Librarian approval extends due date
* Prevents duplicate pending requests

---

### 💰 Fine Management

* Automatic fine calculation
* Based on overdue days
* Real-time display in dashboard

---

### 🔐 Role-Based Access Control

* **Student**
* **Librarian (Admin / Group-based)**

Access control handled using:

* `@login_required`
* `@user_passes_test`

---

### 🔍 Search & Filtering

* Search books and issues
* Filter by:

  * Category
  * Status (pending/returned)
  * Keywords

---

### 📦 Circulation Desk

* Quick check-in / check-out system
* Barcode / ISBN based operations
* Fast library workflow support

---

### 📱 QR Code Feature

* Generate QR code for user profile
* Contains:

  * Name
  * Roll number
  * Branch
  * Email
* Fallback to frontend QR if backend library not installed

---

## 🏗️ Tech Stack

* **Backend:** Django
* **Database:** SQLite / PostgreSQL
* **Frontend:** HTML, CSS, JavaScript
* **Libraries:**

  * Django ORM
  * qrcode (optional for QR generation)

---

## 📂 Project Structure (Simplified)

```
library/
│
├── models.py        # Book, Issue, Request, Renewal models
├── views.py         # Core logic (this file)
├── forms.py         # Django forms
├── templates/       # HTML templates
├── static/          # CSS, JS
```

---

## 🔄 Workflow

### 📌 Book Issue Flow

1. Student requests book
2. Librarian reviews request
3. Book issued if available
4. Due date assigned automatically

---

### 📌 Renewal Flow

1. Student submits renewal request
2. Librarian approves/rejects
3. If approved → due date extended

---

### 📌 Return Flow

1. Librarian marks book as returned
2. Fine calculated (if overdue)
3. Book becomes available again

---

## 🧠 Key Concepts Used

* Django ORM queries (`filter`, `select_related`)
* Atomic transactions (`transaction.atomic`)
* Role-based authorization
* Dynamic fine calculation
* Query filtering with `Q`
* JSON APIs (`JsonResponse`)

---

## ⚡ Installation

```bash
git clone https://github.com/your-username/library-management-system.git
cd library-management-system

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🔑 Default Roles

| Role      | Access       |
| --------- | ------------ |
| Student   | Limited      |
| Librarian | Full control |

---

## 📈 Future Enhancements

* Online payment for fines 💳
* Email notifications 📧
* Book recommendations 🤖
* Mobile app integration 📱
* AI-based search 🔍

---

## 👨‍💻 Author

Developed by Allada Sai Satya Sharan
