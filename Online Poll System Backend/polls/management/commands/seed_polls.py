from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from polls.models import Poll, PollOption
import random


class Command(BaseCommand):
    help = 'Seed the database with sample polls for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--polls',
            type=int,
            default=5,
            help='Number of polls to create (default: 5)'
        )
        parser.add_argument(
            '--users',
            type=int,
            default=3,
            help='Number of users to create (default: 3)'
        )

    def handle(self, *args, **options):
        polls_count = options['polls']
        users_count = options['users']

        self.stdout.write('Creating sample users...')
        users = self.create_users(users_count)
        
        self.stdout.write('Creating sample polls...')
        polls = self.create_polls(polls_count, users)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {len(users)} users and {len(polls)} polls'
            )
        )

    def create_users(self, count):
        """Create sample users"""
        users = []
        for i in range(1, count + 1):
            username = f'user{i}'
            email = f'user{i}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'User',
                    'last_name': f'{i}',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username}')
            else:
                self.stdout.write(f'User already exists: {username}')
            
            users.append(user)
        
        return users

    def create_polls(self, count, users):
        """Create sample polls with options"""
        sample_polls = [
            {
                'title': 'Favorite Programming Language',
                'description': 'Vote for your favorite programming language',
                'options': ['Python', 'JavaScript', 'Java', 'C++', 'Go']
            },
            {
                'title': 'Best Web Framework',
                'description': 'Which web framework do you prefer?',
                'options': ['Django', 'Flask', 'FastAPI', 'Express.js', 'Spring Boot']
            },
            {
                'title': 'Preferred Development Environment',
                'description': 'What is your preferred development environment?',
                'options': ['VS Code', 'PyCharm', 'Sublime Text', 'Vim', 'IntelliJ IDEA']
            },
            {
                'title': 'Database of Choice',
                'description': 'Which database do you use most often?',
                'options': ['PostgreSQL', 'MySQL', 'MongoDB', 'SQLite', 'Redis']
            },
            {
                'title': 'Cloud Platform Preference',
                'description': 'Which cloud platform do you prefer?',
                'options': ['AWS', 'Google Cloud', 'Azure', 'Digital Ocean', 'Heroku']
            },
            {
                'title': 'Operating System for Development',
                'description': 'What OS do you use for development?',
                'options': ['Linux', 'macOS', 'Windows', 'FreeBSD']
            },
            {
                'title': 'Version Control System',
                'description': 'Which version control system do you use?',
                'options': ['Git', 'SVN', 'Mercurial', 'Bazaar']
            },
            {
                'title': 'Testing Framework Preference',
                'description': 'Which testing framework do you prefer?',
                'options': ['pytest', 'unittest', 'Jest', 'JUnit', 'Mocha']
            }
        ]

        polls = []
        for i in range(count):
            poll_data = sample_polls[i % len(sample_polls)]
            creator = random.choice(users)
            
            # Create poll with random expiration (some with, some without)
            expires_at = None
            if random.choice([True, False]):
                expires_at = timezone.now() + timedelta(
                    days=random.randint(7, 30)
                )
            
            poll = Poll.objects.create(
                title=poll_data['title'],
                description=poll_data['description'],
                created_by=creator,
                expires_at=expires_at,
                is_active=True,
                allow_multiple_votes=random.choice([True, False])
            )

            # Create poll options
            for j, option_text in enumerate(poll_data['options']):
                PollOption.objects.create(
                    poll=poll,
                    text=option_text,
                    order=j + 1
                )

            polls.append(poll)
            self.stdout.write(f'Created poll: {poll.title}')

        return polls
