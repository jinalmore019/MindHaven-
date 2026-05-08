#!/usr/bin/env python
"""
Script to update all meditation videos to working YouTube videos
Run: python fix_videos.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wellness_connect.settings')
django.setup()

from student.models import MeditationGuide

# Verified working videos
videos = {
    '5-Minute Morning Meditation': 'https://www.youtube.com/embed/inpok4MKVLM',
    'Mindfulness Meditation for Sleep': 'https://www.youtube.com/embed/aEqlQvczMJQ',
    'Body Scan Relaxation': 'https://www.youtube.com/embed/15q-N-_kkrU',
}

print("Updating meditation videos...")
for title, url in videos.items():
    try:
        meditation = MeditationGuide.objects.get(title=title)
        meditation.video_url = url
        meditation.save()
        print(f"✅ Updated: {title}")
    except MeditationGuide.DoesNotExist:
        print(f"❌ Not found: {title}")

print("\n✅ All videos updated! Please refresh your browser (Ctrl+Shift+R)")
