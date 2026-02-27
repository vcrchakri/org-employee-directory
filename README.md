# 🏢 Org Employee Directory

A full-stack web application that helps organizations manage and search employee information quickly and efficiently.

This system provides a centralized employee directory with search, filters, and sorting features to improve accessibility of employee data.

---

# 🚀 Features

* 🔍 Search employees by **name or employee ID**
* 📊 Filter employees by **active / exited status**
* 🔃 Sort employees by **name or joining date**
* 📄 View employee details in a clean interface
* ⚡ Fast backend API responses
* 📱 Responsive UI

---

# 🧰 Tech Stack

## Frontend

* React.js
* HTML
* CSS
* JavaScript

## Backend

* Django
* Python
* REST APIs

## Database

* MySQL

## Tools

* Git & GitHub
* VS Code
* Postman

---

# 📂 Project Structure

```
org-employee-directory
│
├── backend
│   ├── manage.py
│   ├── requirements.txt
│   └── django apps
│
├── frontend
│   ├── src
│   ├── components
│   └── pages
│
├── .gitignore
└── README.md
```

---

# ⚙️ Installation Guide

## 1️⃣ Clone the repository

```
git clone https://github.com/vcrchakri/org-employee-directory.git
cd org-employee-directory
```

---

# Backend Setup

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

Server runs on

```
http://127.0.0.1:8000
```

---

# Frontend Setup

```
cd frontend
npm install
npm start
```

Frontend runs on

```
http://localhost:3000
```

---

# 🔌 Example API Endpoints

### Get Employees

```
GET /api/employees
```

### Search Employees

```
GET /api/employees?search=John
```

### Filter Employees

```
GET /api/employees?status=active
```

---

# 📊 Use Case

HR teams and organizations can use this system to:

* Maintain employee records
* Search employees instantly
* Track employment status
* Manage workforce data efficiently

---

# 🔮 Future Improvements

* Authentication system
* Admin dashboard
* Pagination
* Role-based access
* Cloud deployment
* Analytics dashboard

---

# 👨‍💻 Author

**Chakradhar**

Full Stack Developer
Python • React • AI Projects

---

# ⭐ Support

If you found this project useful, give it a star on GitHub!
