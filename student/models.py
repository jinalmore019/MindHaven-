"""
MongoEngine models stored in MongoDB: ChatLog, Assessment, Appointment.
user_id / student_id / counsellor_id refer to Django User id (integer).
"""
from mongoengine import Document, IntField, StringField, DateTimeField, FloatField
from datetime import datetime


class ChatLog(Document):
    user_id = IntField(required=True)
    message = StringField(required=True)
    response = StringField(required=True)
    stress_level = StringField(required=True)  # 'Low', 'Medium', 'High'
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'chat_logs',
        'indexes': ['user_id', '-timestamp']
    }


class Assessment(Document):
    user_id = IntField(required=True)
    total_score = IntField(required=True)  # legacy; use phq_score + gad_score
    stress_level = StringField(required=True)  # legacy; use final_level
    date = DateTimeField(default=datetime.utcnow)
    # Risk engine extension
    phq_score = IntField(default=0)
    gad_score = IntField(default=0)
    chat_stress_level = StringField(default='')
    final_level = StringField(default='')  # 'Low', 'Medium', 'High'
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'assessments',
        'indexes': ['user_id', '-created_at', 'stress_level']
    }


class Appointment(Document):
    student_id = IntField(required=True)
    counsellor_id = IntField(required=True)
    date = StringField(required=True)  # e.g. "2024-02-20"
    time_slot = StringField(default='')  # e.g. "10:00 AM"
    status = StringField(required=True, default='Pending')  # Pending, Approved, Completed

    meta = {
        'collection': 'appointments',
        'indexes': ['student_id', 'counsellor_id', 'status']
    }


class MeditationGuide(Document):
    """Pre-loaded meditation guides with videos."""
    title = StringField(required=True)
    description = StringField()
    video_url = StringField()  # YouTube embed URL
    duration = IntField()  # in minutes
    difficulty = StringField(default='Beginner')  # Beginner, Intermediate, Advanced
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'meditation_guides'}


class BreathingExercise(Document):
    """Pre-loaded breathing techniques."""
    title = StringField(required=True)
    description = StringField()
    instructions = StringField()  # Step-by-step guide
    video_url = StringField()  # YouTube embed URL
    duration = IntField()  # in minutes
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'breathing_exercises'}


class JournalEntry(Document):
    """Student journal entries for mood tracking and reflection."""
    user_id = IntField(required=True)
    content = StringField(required=True)
    mood = StringField()  # Happy, Sad, Anxious, Calm, etc.
    stress_level = StringField()  # Low, Medium, High
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'journal_entries',
        'indexes': ['user_id', '-created_at']
    }


class MotivationalContent(Document):
    """Motivational quotes and articles."""
    title = StringField(required=True)
    content = StringField(required=True)  # Quote or article text
    author = StringField()  # Author/source
    category = StringField()  # Inspiration, Recovery, Resilience, etc.
    image_url = StringField()  # Optional image
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'motivational_content'}


class DailyPost(Document):
    """Daily student post for community-style check-ins."""
    user_id = IntField(required=True)
    content = StringField(required=True)
    image_url = StringField(default="")
    language = StringField(default='en')  # en, hi, gu
    stress_level = StringField(default='Low')  # Low, Medium, High
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'daily_posts',
        'indexes': ['user_id', '-created_at', 'stress_level']
    }


class CounsellorMessage(Document):
    """Direct counsellor-to-student communication logs."""
    student_id = IntField(required=True)
    counsellor_id = IntField(required=True)
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "counsellor_messages",
        "indexes": ["student_id", "counsellor_id", "-created_at"],
    }


class CounsellorSessionNote(Document):
    """Structured notes after each counsellor follow-up."""
    student_id = IntField(required=True)
    counsellor_id = IntField(required=True)
    summary = StringField(required=True)
    action_plan = StringField(default="")
    next_follow_up_date = StringField(default="")  # YYYY-MM-DD
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "counsellor_session_notes",
        "indexes": ["student_id", "counsellor_id", "-created_at", "next_follow_up_date"],
    }


class StudentReply(Document):
    """Student reply to counsellor messages - enables 2-way chat."""
    student_id = IntField(required=True)
    counsellor_id = IntField(required=True)
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "student_replies",
        "indexes": ["student_id", "counsellor_id", "-created_at"],
    }


class CareTask(Document):
    """Actionable care plan tasks assigned by counsellor."""
    student_id = IntField(required=True)
    counsellor_id = IntField(required=True)
    title = StringField(required=True)
    details = StringField(default="")
    due_date = StringField(default="")  # YYYY-MM-DD
    status = StringField(default="Pending")  # Pending, Completed
    created_at = DateTimeField(default=datetime.utcnow)
    completed_at = DateTimeField()

    meta = {
        "collection": "care_tasks",
        "indexes": ["student_id", "counsellor_id", "status", "-created_at"],
    }
