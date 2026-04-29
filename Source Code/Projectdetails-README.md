# 🎓 Smart Attend: AI-Powered Classroom Attendance System

## 📌 Project Overview

Smart Attend is an AI-powered classroom attendance system that automates attendance marking using facial recognition and real-time location verification. The system reduces manual effort, improves accuracy, and prevents proxy attendance.

---

## ⚙️ Key Features

* 🎯 Face Recognition-based Attendance
* 📍 Real-Time Location Verification
* 🤖 AI Chatbot for Attendance Queries
* 📊 Automatic Attendance Report Generation
* 🗄️ SQLite Database Storage

---

## 🧩 System Modules

### 📊 Dashboard

* View overall attendance statistics
* Visualize attendance trends through graphs
* Quick access to key performance metrics

---

### 👨‍🎓 Student Management

* Add new students with details
* View and manage student records
* Assign students to specific classes

---

### 📅 Attendance Management

* Mark attendance class-wise
* Multiple attendance status options (Present, Absent, Late)
* Bulk attendance marking
* Edit and update attendance records

---

### 📈 Reports & Analytics

* Generate reports by class or date range
* Export reports in CSV format
* View attendance statistics and trends

---

## 🧠 System Workflow

1. Camera captures real-time video
2. Faces are detected using OpenCV
3. Face recognition identifies students
4. Location verification checks presence
5. Attendance is marked automatically
6. Data is stored in the database

---

## 📍 Location Detection System

### 🔄 Smart Fallback Mechanism

Real GPS → IP-Based Location → Demo Mode

---

### 🌍 Location Detection Methods

#### 1. Windows Location Services

* Uses system GPS
* Requires Windows 10+ and enabled location access

#### 2. IP-Based Geolocation

```python
import geocoder
g = geocoder.ip('me')
```

#### 3. Demo Mode

* Used when GPS is unavailable
* Simulates location for testing

---

### ⚙️ Configuration

```python
self.school_location = (28.6139, 77.2090)
self.allowed_radius = 0.5
```

Update coordinates using Google Maps

---

### 🔧 Installation (Location Support)

```bash
pip install geocoder
pip install geopy
pip install requests
```

---

### 🔒 Security

* Location is used only for attendance verification
* No external sharing of data
* Stored locally

---

## 🤖 AI Chatbot System

### 🧠 Overview

An AI-based chatbot allows users to interact with attendance data using natural language queries.

---

### ⚙️ Features

* Check attendance status
* Calculate attendance percentage
* Count absences
* View student records
* Query attendance by date

---

### 🧩 Working Mechanism

* Uses regex-based intent detection
* Extracts date, student name, and class
* Fetches data from SQLite database
* Generates human-readable responses

---

### 💬 Example Queries

* "Did I attend yesterday?"
* "My attendance percentage"
* "How many days absent this month?"
* "Check attendance for yesterday"

---

### 📊 Capabilities

* Attendance tracking
* Percentage calculation
* Absence monitoring
* Class-level reporting
* Daily summary generation

---

## 🛠️ Technologies Used

* Python
* OpenCV
* face_recognition
* SQLite
* PyQt5
* Geolocation APIs

---

## 📁 Project Structure

```
Source Code/
├── main.py
├── attendance_system.py
├── database.py
├── chatbot.py
├── auth.py
├── ui_styles.py
├── requirements.txt
├── attendance.db
└── student_photos/
```

---

## 🚀 Future Scope

* Mobile application integration
* Cloud-based database
* Improved AI accuracy
* Multi-institution deployment

---
