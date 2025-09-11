from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class Poll(models.Model):
    """
    Model representing a poll with multiple options.
    Optimized for efficient querying and real-time result computation.
    """
    title = models.CharField(max_length=200, help_text="Poll title")
    description = models.TextField(blank=True, help_text="Poll description")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_polls',
        help_text="User who created this poll"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Poll expiration date (optional)"
    )
    is_active = models.BooleanField(default=True, help_text="Whether the poll is active")
    allow_multiple_votes = models.BooleanField(
        default=False, 
        help_text="Allow users to vote multiple times"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        """Validate poll data"""
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError("Expiration date must be in the future.")

    def is_expired(self):
        """Check if poll has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def total_votes(self):
        """Get total number of votes for this poll"""
        return Vote.objects.filter(option__poll=self).count()

    def get_results(self):
        """
        Get poll results with vote counts for each option.
        Optimized query for real-time result computation.
        """
        from django.db.models import Count
        
        results = self.options.annotate(
            vote_count=Count('votes')
        ).values('id', 'text', 'vote_count').order_by('-vote_count')
        
        total_votes = sum(option['vote_count'] for option in results)
        
        # Add percentage calculation
        for option in results:
            if total_votes > 0:
                option['percentage'] = round((option['vote_count'] / total_votes) * 100, 2)
            else:
                option['percentage'] = 0
        
        return {
            'poll_id': self.id,
            'poll_title': self.title,
            'total_votes': total_votes,
            'options': list(results),
            'is_expired': self.is_expired(),
            'created_at': self.created_at,
            'expires_at': self.expires_at
        }


class PollOption(models.Model):
    """
    Model representing an option within a poll.
    Optimized with indexes for efficient vote counting.
    """
    poll = models.ForeignKey(
        Poll, 
        on_delete=models.CASCADE, 
        related_name='options',
        help_text="Poll this option belongs to"
    )
    text = models.CharField(max_length=200, help_text="Option text")
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(
        default=0, 
        help_text="Display order of the option"
    )

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['poll', 'order']),
        ]
        unique_together = ['poll', 'text']

    def __str__(self):
        return f"{self.poll.title} - {self.text}"

    def vote_count(self):
        """Get vote count for this option"""
        return self.votes.count()


class Vote(models.Model):
    """
    Model representing a vote cast by a user for a specific poll option.
    Optimized for preventing duplicate votes and efficient counting.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='votes',
        null=True,
        blank=True,
        help_text="User who cast the vote (optional for anonymous voting)"
    )
    option = models.ForeignKey(
        PollOption, 
        on_delete=models.CASCADE, 
        related_name='votes',
        help_text="Option that was voted for"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of the voter (for duplicate prevention)"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string for additional duplicate detection"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['option']),
            models.Index(fields=['user', 'option']),
            models.Index(fields=['ip_address', 'option']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        voter = self.user.username if self.user else f"Anonymous ({self.ip_address})"
        return f"{voter} voted for {self.option.text}"

    def clean(self):
        """Validate vote to prevent duplicates"""
        if not self.option.poll.allow_multiple_votes:
            # Check for existing vote by same user
            if self.user:
                existing_vote = Vote.objects.filter(
                    user=self.user,
                    option__poll=self.option.poll
                ).exclude(pk=self.pk).exists()
                
                if existing_vote:
                    raise ValidationError("User has already voted in this poll.")
            
            # Check for existing vote by same IP address
            existing_ip_vote = Vote.objects.filter(
                ip_address=self.ip_address,
                option__poll=self.option.poll
            ).exclude(pk=self.pk).exists()
            
            if existing_ip_vote:
                raise ValidationError("A vote from this IP address already exists for this poll.")

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class VoteSession(models.Model):
    """
    Model to track voting sessions for analytics and duplicate prevention.
    """
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['-last_activity']),
        ]

    def __str__(self):
        return f"Session {self.session_key} from {self.ip_address}"