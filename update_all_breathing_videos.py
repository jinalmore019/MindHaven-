#!/usr/bin/env python
"""
Update all breathing exercise videos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_connect.settings')
django.setup()

from student.models import BreathingExercise

videos = {
    'Box Breathing': 'https://www.youtube.com/embed/QM7BMujkIvo',
    'Diaphragmatic Breathing': 'https://www.youtube.com/embed/f7T3Opv9x0c',
    '4-7-8 Breathing Technique': 'https://www.youtube.com/embed/YJ2jUAm5AkQ',  # Keep existing
}

print("Updating breathing exercise videos...")
for title, url in videos.items():
    try:
        exercise = BreathingExercise.objects.get(title=title)
        exercise.video_url = url
        exercise.save()
        print(f"✅ {title}: {url.split('/')[-1]}")
    except BreathingExercise.DoesNotExist:
        print(f"❌ Not found: {title}")

print("\n✅ All breathing videos updated!")
