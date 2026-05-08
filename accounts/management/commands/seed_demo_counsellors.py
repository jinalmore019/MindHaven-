from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Create 2 demo counsellor users for realistic testing."

    def handle(self, *args, **options):
        demos = [
            {
                "email": "counsellor.riya@wellify.demo",
                "name": "Dr. Riya Sharma",
                "password": "Wellify@123",
            },
            {
                "email": "counsellor.arjun@wellify.demo",
                "name": "Dr. Arjun Mehta",
                "password": "Wellify@123",
            },
        ]
        created = 0
        for item in demos:
            user = User.objects.filter(email=item["email"]).first()
            if user:
                if user.role != "Counsellor":
                    user.role = "Counsellor"
                    user.name = item["name"]
                    user.set_password(item["password"])
                    user.save(update_fields=["role", "name", "password"])
                    self.stdout.write(self.style.WARNING(f"Updated existing user to counsellor: {item['email']}"))
                else:
                    self.stdout.write(f"Already exists: {item['email']}")
                continue

            User.objects.create_user(
                email=item["email"],
                name=item["name"],
                role="Counsellor",
                password=item["password"],
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"Created: {item['email']}"))

        self.stdout.write(self.style.SUCCESS(f"Done. New counsellors created: {created}"))
