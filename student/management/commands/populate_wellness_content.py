"""
Django management command to populate sample wellness content.
Run with: python manage.py populate_wellness_content
"""

from django.core.management.base import BaseCommand

from student.models import BreathingExercise, MeditationGuide, MotivationalContent


class Command(BaseCommand):
    help = "Populate database with sample wellness content"

    def handle(self, *args, **options):
        meditations = [
            {
                "title": "5-Minute Morning Meditation",
                "description": "Start your day with clarity and calm. A gentle 5-minute meditation to set positive intentions.",
                "video_url": "https://www.youtube.com/embed/inpok4MKVLM",
                "duration": 5,
                "difficulty": "Beginner",
            },
            {
                "title": "Mindfulness Meditation for Sleep",
                "description": "Wind down in the evening with this soothing meditation designed to help you relax and sleep better.",
                "video_url": "https://www.youtube.com/embed/aEqlQvczMJQ",
                "duration": 15,
                "difficulty": "Beginner",
            },
            {
                "title": "Body Scan Relaxation",
                "description": "Release tension from your body while improving awareness and relaxation through guided scanning.",
                "video_url": "https://www.youtube.com/embed/15q-N-_kkrU",
                "duration": 10,
                "difficulty": "Beginner",
            },
            {
                "title": "Meditation for Exam Stress",
                "description": "A focused guided meditation to reduce academic pressure, improve concentration, and calm your mind before study sessions.",
                "video_url": "https://www.youtube.com/embed/O-6f5wQXSu8",
                "duration": 10,
                "difficulty": "Beginner",
            },
            {
                "title": "10-Minute Anxiety Reset",
                "description": "A grounding meditation for moments of anxious thinking, physical tension, and emotional overload.",
                "video_url": "https://www.youtube.com/embed/ZToicYcHIOU",
                "duration": 10,
                "difficulty": "Intermediate",
            },
            {
                "title": "Guided Meditation for Deep Sleep",
                "description": "Slow down racing thoughts and prepare your body for deep, restorative sleep.",
                "video_url": "https://www.youtube.com/embed/69o0P7s8GHE",
                "duration": 20,
                "difficulty": "Beginner",
            },
            {
                "title": "Mindfulness for Overthinking",
                "description": "Learn to observe thoughts without being pulled into them with a practical mindfulness session.",
                "video_url": "https://www.youtube.com/embed/ssss7V1_eyA",
                "duration": 12,
                "difficulty": "Intermediate",
            },
            {
                "title": "Self-Compassion Meditation",
                "description": "A supportive meditation for students dealing with self-criticism, setbacks, or emotional exhaustion.",
                "video_url": "https://www.youtube.com/embed/IvtZBUSplr4",
                "duration": 14,
                "difficulty": "Beginner",
            },
        ]

        count = 0
        for med in meditations:
            try:
                MeditationGuide.objects.get(title=med["title"])
            except MeditationGuide.DoesNotExist:
                MeditationGuide(
                    title=med["title"],
                    description=med["description"],
                    video_url=med["video_url"],
                    duration=med["duration"],
                    difficulty=med["difficulty"],
                ).save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Created {count} new meditation guides"))

        exercises = [
            {
                "title": "4-7-8 Breathing Technique",
                "description": "A calming breathing pattern that helps reduce anxiety and promote relaxation.",
                "instructions": "Step 1: Exhale completely through your mouth.\nStep 2: Close your mouth, inhale through nose for count of 4.\nStep 3: Hold your breath for count of 7.\nStep 4: Exhale through mouth for count of 8.\nRepeat 4 more times.",
                "video_url": "https://www.youtube.com/embed/1Dv-ldGLnIY",
                "duration": 5,
            },
            {
                "title": "Box Breathing",
                "description": "Also known as square breathing, this technique helps calm the nervous system.",
                "instructions": "Step 1: Breathe in through your nose for 4 counts.\nStep 2: Hold for 4 counts.\nStep 3: Exhale through your mouth for 4 counts.\nStep 4: Hold for 4 counts.\nRepeat 5-10 times.",
                "video_url": "https://www.youtube.com/embed/tEmt1Znux58",
                "duration": 5,
            },
            {
                "title": "Diaphragmatic Breathing",
                "description": "Deep belly breathing that activates your parasympathetic nervous system.",
                "instructions": "Step 1: Sit or lie in a comfortable position.\nStep 2: Place one hand on your chest and one on your belly.\nStep 3: Breathe in slowly through your nose, letting your belly expand, not your chest.\nStep 4: Hold for 2-3 seconds.\nStep 5: Exhale slowly through your mouth.\nDo this for 5-10 minutes daily.",
                "video_url": "https://www.youtube.com/embed/kgTL5G1ibIo",
                "duration": 10,
            },
            {
                "title": "Physiological Sigh",
                "description": "A fast-acting breathing reset that can quickly reduce stress and lower physical tension.",
                "instructions": "Step 1: Take one full inhale through your nose.\nStep 2: Take a second smaller inhale through the nose.\nStep 3: Exhale slowly through the mouth for a long breath out.\nStep 4: Repeat for 1-3 minutes.",
                "video_url": "https://www.youtube.com/embed/rBdhqBGqiMc",
                "duration": 3,
            },
            {
                "title": "Coherent Breathing",
                "description": "A balanced breathing rhythm that supports calm focus, especially useful during study breaks.",
                "instructions": "Step 1: Inhale gently for 5 counts.\nStep 2: Exhale gently for 5 counts.\nStep 3: Keep shoulders relaxed and jaw soft.\nStep 4: Repeat for 5 minutes.",
                "video_url": "https://www.youtube.com/embed/gz4G31LGyog",
                "duration": 5,
            },
            {
                "title": "Breathing for Panic Relief",
                "description": "A guided breathing practice designed to slow the body when panic sensations or overwhelm start rising.",
                "instructions": "Step 1: Place both feet on the ground.\nStep 2: Inhale for 4 counts.\nStep 3: Exhale for 6 counts.\nStep 4: Name one thing you can see while breathing.\nStep 5: Continue for 2-4 minutes.",
                "video_url": "https://www.youtube.com/embed/odADwWzHR24",
                "duration": 4,
            },
        ]

        count = 0
        for ex in exercises:
            try:
                BreathingExercise.objects.get(title=ex["title"])
            except BreathingExercise.DoesNotExist:
                BreathingExercise(
                    title=ex["title"],
                    description=ex["description"],
                    instructions=ex["instructions"],
                    video_url=ex["video_url"],
                    duration=ex["duration"],
                ).save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Created {count} new breathing exercises"))

        motivations = [
            {
                "title": "You Are Stronger Than You Think",
                "content": "Every challenge you face is an opportunity to grow. The difficulties you face build your character and resilience. Remember: what feels impossible today will feel like nothing once you overcome it. You have the strength within you to handle whatever comes your way.",
                "author": "Wellify Team",
                "category": "Resilience",
            },
            {
                "title": "Progress, Not Perfection",
                "content": "Mental health is not a destination - it is a journey. Small steps forward are still progress. You do not need to be perfect; you just need to keep trying. Celebrate every small victory, every moment of self-care, and every time you choose your wellbeing.",
                "author": "Wellify Team",
                "category": "Recovery",
            },
            {
                "title": "You Are Not Alone",
                "content": "Millions of people struggle with anxiety, depression, and stress. You are not broken, and you are not alone. Reaching out for help is a sign of strength, not weakness. Your feelings are valid, and your experience matters. There are people ready to support you.",
                "author": "Wellify Team",
                "category": "Support",
            },
            {
                "title": "Self-Care Is Not Selfish",
                "content": "Taking care of yourself is essential, not optional. When you invest in your wellbeing, you are better able to show up for others. Self-care is an investment in your ability to live fully.",
                "author": "Wellify Team",
                "category": "Inspiration",
            },
            {
                "title": "Your Story Is Not Over",
                "content": "No matter what you are going through right now, remember that this is not the end of your story - it is just a chapter. You have survived every hard day so far. Keep going.",
                "author": "Wellify Team",
                "category": "Hope",
            },
            {
                "title": "Rest Is Part of the Work",
                "content": "You do not need to earn rest by burning out first. Recovery is part of performance, not the opposite of it. Real strength includes knowing when to pause, reset, and return with clarity.",
                "author": "Wellify Team",
                "category": "Balance",
            },
            {
                "title": "One Small Step Still Counts",
                "content": "When everything feels too much, shrink the goal. Open the document. Drink water. Sit by the window. Send one message. Tiny actions are often the doorway back into motion.",
                "author": "Wellify Team",
                "category": "Motivation",
            },
            {
                "title": "You Deserve Support Before a Crisis",
                "content": "You do not have to wait until things fall apart to ask for help. Support is not only for emergencies. It is also for confusion, stress, loneliness, pressure, and those days when you do not know how to hold everything together.",
                "author": "Wellify Team",
                "category": "Support",
            },
        ]

        count = 0
        for mot in motivations:
            try:
                MotivationalContent.objects.get(title=mot["title"])
            except MotivationalContent.DoesNotExist:
                MotivationalContent(
                    title=mot["title"],
                    content=mot["content"],
                    author=mot["author"],
                    category=mot["category"],
                ).save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Created {count} new motivational content items"))
        self.stdout.write(self.style.SUCCESS("Wellness content population complete."))
