from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta

from .models import Poll, PollOption, Vote


class PollModelTest(TestCase):
    """Test cases for Poll model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_poll_creation(self):
        """Test basic poll creation"""
        poll = Poll.objects.create(
            title='Test Poll',
            description='Test Description',
            created_by=self.user
        )
        
        self.assertEqual(poll.title, 'Test Poll')
        self.assertEqual(poll.created_by, self.user)
        self.assertTrue(poll.is_active)
        self.assertFalse(poll.allow_multiple_votes)
        
    def test_poll_expiration(self):
        """Test poll expiration logic"""
        # Create expired poll
        expired_poll = Poll.objects.create(
            title='Expired Poll',
            created_by=self.user,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        # Create active poll
        active_poll = Poll.objects.create(
            title='Active Poll',
            created_by=self.user,
            expires_at=timezone.now() + timedelta(days=1)
        )
        
        self.assertTrue(expired_poll.is_expired())
        self.assertFalse(active_poll.is_expired())
        
    def test_poll_results(self):
        """Test poll results computation"""
        poll = Poll.objects.create(
            title='Test Poll',
            created_by=self.user
        )
        
        # Create options
        option1 = PollOption.objects.create(poll=poll, text='Option 1', order=1)
        option2 = PollOption.objects.create(poll=poll, text='Option 2', order=2)
        
        # Create votes
        Vote.objects.create(option=option1, ip_address='192.168.1.1')
        Vote.objects.create(option=option1, ip_address='192.168.1.2')
        Vote.objects.create(option=option2, ip_address='192.168.1.3')
        
        results = poll.get_results()
        
        self.assertEqual(results['total_votes'], 3)
        self.assertEqual(len(results['options']), 2)
        self.assertEqual(results['options'][0]['vote_count'], 2)  # Option 1
        self.assertEqual(results['options'][1]['vote_count'], 1)  # Option 2


class VoteModelTest(TestCase):
    """Test cases for Vote model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.poll = Poll.objects.create(
            title='Test Poll',
            created_by=self.user
        )
        self.option = PollOption.objects.create(
            poll=self.poll,
            text='Test Option',
            order=1
        )
        
    def test_vote_creation(self):
        """Test basic vote creation"""
        vote = Vote.objects.create(
            user=self.user,
            option=self.option,
            ip_address='192.168.1.1'
        )
        
        self.assertEqual(vote.user, self.user)
        self.assertEqual(vote.option, self.option)
        self.assertEqual(vote.ip_address, '192.168.1.1')
        
    def test_anonymous_vote(self):
        """Test anonymous vote creation"""
        vote = Vote.objects.create(
            option=self.option,
            ip_address='192.168.1.1'
        )
        
        self.assertIsNone(vote.user)
        self.assertEqual(vote.option, self.option)


class PollAPITest(APITestCase):
    """Test cases for Poll API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_create_poll(self):
        """Test poll creation via API"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'Test Poll',
            'description': 'Test Description',
            'options': [
                {'text': 'Option 1', 'order': 1},
                {'text': 'Option 2', 'order': 2}
            ]
        }
        
        response = self.client.post('/api/v1/polls/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Poll.objects.count(), 1)
        self.assertEqual(PollOption.objects.count(), 2)
        
    def test_list_polls(self):
        """Test poll listing via API"""
        poll = Poll.objects.create(
            title='Test Poll',
            created_by=self.user
        )
        
        response = self.client.get('/api/v1/polls/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_poll_detail(self):
        """Test poll detail retrieval via API"""
        poll = Poll.objects.create(
            title='Test Poll',
            created_by=self.user
        )
        option = PollOption.objects.create(
            poll=poll,
            text='Test Option',
            order=1
        )
        
        response = self.client.get(f'/api/v1/polls/{poll.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Poll')
        self.assertEqual(len(response.data['options']), 1)


class VoteAPITest(APITestCase):
    """Test cases for Vote API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.poll = Poll.objects.create(
            title='Test Poll',
            created_by=self.user
        )
        self.option = PollOption.objects.create(
            poll=self.poll,
            text='Test Option',
            order=1
        )
        
    def test_cast_vote(self):
        """Test vote casting via API"""
        data = {'option': self.option.id}
        
        response = self.client.post('/api/v1/vote/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vote.objects.count(), 1)
        
    def test_duplicate_vote_prevention(self):
        """Test duplicate vote prevention"""
        # Cast first vote
        data = {'option': self.option.id}
        response1 = self.client.post('/api/v1/vote/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Try to cast duplicate vote from same IP
        response2 = self.client.post('/api/v1/vote/', data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_poll_results(self):
        """Test poll results retrieval"""
        # Create votes
        Vote.objects.create(option=self.option, ip_address='192.168.1.1')
        Vote.objects.create(option=self.option, ip_address='192.168.1.2')
        
        response = self.client.get(f'/api/v1/polls/{self.poll.id}/results/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_votes'], 2)
        self.assertEqual(len(response.data['options']), 1)
        self.assertEqual(response.data['options'][0]['vote_count'], 2)


class StatisticsAPITest(APITestCase):
    """Test cases for Statistics API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_vote_statistics(self):
        """Test vote statistics endpoint"""
        # Create test data
        poll = Poll.objects.create(title='Test Poll', created_by=self.user)
        option = PollOption.objects.create(poll=poll, text='Option', order=1)
        Vote.objects.create(option=option, ip_address='192.168.1.1')
        
        response = self.client.get('/api/v1/statistics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_polls', response.data)
        self.assertIn('total_votes', response.data)
        self.assertIn('active_polls', response.data)
        self.assertIn('top_polls', response.data)
        
        self.assertEqual(response.data['total_polls'], 1)
        self.assertEqual(response.data['total_votes'], 1)