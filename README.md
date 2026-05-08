# 🧠 MindHaven — Mental Wellness Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?style=for-the-badge&logo=django)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0-brightgreen?style=for-the-badge&logo=mongodb)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**A comprehensive AI-powered mental wellness platform for students**

*Empowering students with intelligent support, real-time counsellor access, and evidence-based wellness tools*

</div>

---

## 🔄 Project Evolution

> **MindHaven** is the fully redesigned and enhanced version of **Wellify** — a college group project.
>
> The original **Wellify** was built as a team project during college. After the project, I independently redesigned the entire platform, added major new features, improved the UI/UX, and rebranded it as **MindHaven**.
>
> **Key upgrades from Wellify → MindHaven:**
> - 🆕 Real-time 2-way Counsellor ↔ Student Chat
> - 🆕 Emergency Flag & Risk Override for Counsellors
> - 🆕 Session Notes & Care Task Assignment
> - 🆕 Dark / Light Mode Toggle
> - 🆕 Multi-language Support (English, Hindi, Gujarati)
> - 🆕 Password Reset functionality
> - 🆕 Admin User Create/Delete
> - 🆕 Appointment Time Slot booking
> - 🎨 Complete UI redesign with modern dark theme

---

## 🌟 Overview

MindHaven is a full-stack mental wellness platform built with Django, designed to support students through AI-powered chat, clinical assessments, guided wellness content, and direct counsellor communication. The platform bridges the gap between students in distress and professional mental health support.

---

## ✨ Features

### 🎓 For Students
| Feature | Description |
|---------|-------------|
| 🤖 **AI Chatbot** | Intelligent mental health support with stress detection |
| 📋 **PHQ-9 & GAD-7** | Clinical depression and anxiety assessments |
| 🧘 **Guided Meditation** | Curated video-based meditation sessions |
| 🌬️ **Breathing Exercises** | Evidence-based breathing techniques |
| ✍️ **Personal Journal** | Private mood tracking and reflection |
| 💡 **Motivational Content** | Recovery-focused inspirational content |
| 📅 **Session Booking** | Book counselling sessions with time slots |
| 💬 **2-Way Counsellor Chat** | Real-time messaging with assigned counsellor |
| 🔑 **Password Reset** | Self-service account recovery |

### 👨‍⚕️ For Counsellors
| Feature | Description |
|---------|-------------|
| 💬 **Live Chat** | Real-time 2-way chat with students |
| 🚨 **Emergency Flag** | Instant high-risk alert with priority session |
| ⚡ **Risk Override** | Manually update student risk levels |
| 📋 **Session Notes** | Clinical notes with action plans |
| ✅ **Care Tasks** | Assign recovery tasks to students |
| 📊 **Student Dashboard** | PHQ-9, GAD-7, stress level overview |
| 📅 **Appointment Management** | Approve and complete session pipeline |

### 🔧 For Admins
| Feature | Description |
|---------|-------------|
| 📈 **Analytics Dashboard** | System-wide stats with charts |
| 👤 **User Management** | Create and delete users |
| 📊 **Reports** | Export CSV/PDF wellness reports |
| 🔍 **Risk Monitoring** | Monitor high-risk student cases |

---

## 🛠️ Tech Stack

```
Backend     → Django 4.2 (Python)
Database    → SQLite (Auth) + MongoDB (Chat, Assessments, Wellness)
Frontend    → HTML5, CSS3, JavaScript (Vanilla)
AI          → Built-in stress detection + Optional OpenAI GPT integration
Charts      → Chart.js
PDF Export  → ReportLab
```

---

## 🌐 Multi-Language Support

The platform supports **3 languages** across all pages:
- 🇬🇧 English
- 🇮🇳 Hindi (हिंदी)
- 🇮🇳 Gujarati (ગુજરાતી)

---

## 🎨 UI Features

- 🌙 **Dark / Light Mode Toggle** — Persistent theme preference
- 📱 **Fully Responsive** — Works on mobile, tablet, desktop
- ✨ **Smooth Animations** — Stagger-in effects and transitions
- 🎯 **Role-Based Dashboards** — Separate views for Student, Counsellor, Admin

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MongoDB (local or Atlas)
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/jinalmore019/MindHaven-.git
cd MindHaven-

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run migrations
python manage.py makemigrations
python manage.py migrate

# 6. Populate wellness content
python manage.py populate_wellness_content

# 7. Create admin account
python manage.py createsuperuser

# 8. Start server
python manage.py runserver
```

Visit `http://localhost:8000` 🎉

---

## ⚙️ Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

MONGODB_NAME=wellness_connect_db
MONGODB_URI=mongodb://localhost:27017/wellness_connect_db

# Optional: Enable AI-powered chatbot
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini
```

> 💡 Without `OPENAI_API_KEY`, the chatbot uses the built-in stress detection engine.

---

## 📁 Project Structure

```
MindHaven/
├── accounts/          # Authentication, user profiles, risk engine
├── student/           # Chatbot, assessments, wellness content, journal
├── counsellor/        # Counsellor dashboard, chat, session tools
├── admin_panel/       # Admin dashboard, user management, reports
├── templates/         # Shared base templates
├── static/css/        # Global stylesheet with dark/light theme
├── wellness_connect/  # Django settings, URLs, middleware
└── manage.py
```

---

## 🔐 User Roles

```
Student    →  Chatbot, Assessments, Wellness Tools, Book Sessions, Chat with Counsellor
Counsellor →  Student Management, Live Chat, Risk Tools, Session Notes
Admin      →  System Analytics, User Management, Reports
```

---

## 🧠 Risk Assessment System

The platform uses a **multi-factor risk engine**:

```
PHQ-9 Score (0-27)  →  Depression severity
GAD-7 Score (0-21)  →  Anxiety severity
Chat Stress Level   →  Low / Medium / High
─────────────────────────────────────────
Final Risk Level    →  Low / Medium / High
```

High-risk students automatically trigger:
- ✅ Counsellor notification
- ✅ Priority appointment creation
- ✅ Emergency flag option for counsellors

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👩‍💻 Developer

<div align="center">

**Jinal More**

[![GitHub](https://img.shields.io/badge/GitHub-jinalmore019-black?style=flat&logo=github)](https://github.com/jinalmore019)

*Built with ❤️ for student mental wellness*

*Originally developed as Wellify (college group project) — independently redesigned and enhanced as MindHaven*

</div>
