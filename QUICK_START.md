# 🚀 Wellify - Quick Start Guide

## તમારે શું કરવાનું છે (What You Need To Do)

### 1️⃣ Virtual Environment Activate કરો
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2️⃣ Dependencies Install કરો
```bash
pip install -r requirements.txt
```

### 3️⃣ Environment Variables Setup કરો
```bash
# .env file બનાવો અને આ add કરો:
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
MONGODB_NAME=wellness_connect_db
MONGODB_URI=mongodb://localhost:27017/wellness_connect_db
```

### 4️⃣ MongoDB Start કરો
```bash
# MongoDB service start કરો (તમારા system પર)
# Windows: MongoDB Compass ખોલો અથવા service start કરો
# Mac: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

### 5️⃣ Database Migrations Run કરો
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6️⃣ Wellness Content Populate કરો
```bash
python manage.py populate_wellness_content
```

### 7️⃣ Superuser બનાવો (Optional)
```bash
python manage.py createsuperuser
```

### 8️⃣ Server Start કરો
```bash
python manage.py runserver
```

### 9️⃣ Browser માં ખોલો
```
http://localhost:8000
```

---

## 🎯 Test Users બનાવો

### Student Account
1. Register પર જાઓ
2. Role: Student select કરો
3. Email, Name, Password enter કરો
4. Login કરો

### Counsellor Account
1. Register પર જાઓ
2. Role: Counsellor select કરો
3. Email, Name, Password enter કરો
4. Login કરો

### Admin Account
```bash
python manage.py createsuperuser
# Role: Admin select કરો
```

---

## ✅ બધું કામ કરે છે કે નહીં Check કરો

### Student Dashboard પર:
- ✅ Chatbot કામ કરે છે?
- ✅ Assessment લઈ શકો છો?
- ✅ Meditation videos દેખાય છે?
- ✅ Breathing exercises દેખાય છે?
- ✅ Journal create કરી શકો છો?
- ✅ Motivation content દેખાય છે?
- ✅ Book Session કરી શકો છો?

### Counsellor Dashboard પર:
- ✅ Students by risk level દેખાય છે?
- ✅ Appointments manage કરી શકો છો?
- ✅ Chat history જોઈ શકો છો?

---

## 🐛 Problems થાય તો

### MongoDB Connection Error
```bash
# Check MongoDB is running:
# Windows: Services માં MongoDB service check કરો
# Mac: brew services list
# Linux: sudo systemctl status mongod
```

### Migration Errors
```bash
# Delete migrations and recreate:
python manage.py migrate --fake accounts zero
python manage.py migrate accounts
```

### Port Already in Use
```bash
# Different port use કરો:
python manage.py runserver 8001
```

---

## 📝 Important Notes

1. **MongoDB જરૂરી છે** - Without MongoDB, wellness features કામ નહીં કરે
2. **Wellness content populate કરવું જરૂરી છે** - નહીં તો meditation/breathing lists ખાલી રહેશે
3. **Logs check કરો** - Problems થાય તો `logs/wellness_connect.log` જુઓ

---

## 🎉 Success!

જો બધું કામ કરે છે, તો તમારો Wellify platform ready છે! 

Happy Coding! 🚀
