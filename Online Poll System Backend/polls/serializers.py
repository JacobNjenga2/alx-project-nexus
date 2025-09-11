from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Poll, PollOption, Vote, VoteSession


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class PollOptionSerializer(serializers.ModelSerializer):
    """Serializer for PollOption model"""
    vote_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = PollOption
        fields = ['id', 'text', 'order', 'vote_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'vote_count']

    def validate_text(self, value):
        """Validate option text"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Option text must be at least 2 characters long.")
        return value.strip()


class PollCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating polls"""
    options = PollOptionSerializer(many=True, write_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Poll
        fields = [
            'id', 'title', 'description', 'created_by', 'created_at', 
            'updated_at', 'expires_at', 'is_active', 'allow_multiple_votes', 
            'options'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate_title(self, value):
        """Validate poll title"""
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Poll title must be at least 5 characters long.")
        return value.strip()

    def validate_expires_at(self, value):
        """Validate expiration date"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future.")
        return value

    def validate_options(self, value):
        """Validate poll options"""
        if len(value) < 2:
            raise serializers.ValidationError("Poll must have at least 2 options.")
        if len(value) > 10:
            raise serializers.ValidationError("Poll cannot have more than 10 options.")
        
        # Check for duplicate options
        option_texts = [option['text'].strip().lower() for option in value]
        if len(option_texts) != len(set(option_texts)):
            raise serializers.ValidationError("Poll options must be unique.")
        
        return value

    def create(self, validated_data):
        """Create poll with options"""
        options_data = validated_data.pop('options')
        poll = Poll.objects.create(**validated_data)
        
        for i, option_data in enumerate(options_data):
            PollOption.objects.create(
                poll=poll,
                order=i + 1,
                **option_data
            )
        
        return poll


class PollDetailSerializer(serializers.ModelSerializer):
    """Serializer for poll details with options"""
    options = PollOptionSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    total_votes = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Poll
        fields = [
            'id', 'title', 'description', 'created_by', 'created_at', 
            'updated_at', 'expires_at', 'is_active', 'allow_multiple_votes',
            'options', 'total_votes', 'is_expired'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class PollListSerializer(serializers.ModelSerializer):
    """Serializer for poll list view"""
    created_by = UserSerializer(read_only=True)
    total_votes = serializers.IntegerField(read_only=True)
    option_count = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Poll
        fields = [
            'id', 'title', 'description', 'created_by', 'created_at', 
            'expires_at', 'is_active', 'total_votes', 'option_count', 
            'is_expired'
        ]


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for voting"""
    option_text = serializers.CharField(source='option.text', read_only=True)
    poll_title = serializers.CharField(source='option.poll.title', read_only=True)
    
    class Meta:
        model = Vote
        fields = [
            'id', 'option', 'option_text', 'poll_title', 'created_at',
            'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'created_at', 'ip_address', 'user_agent']

    def validate_option(self, value):
        """Validate voting option"""
        # Check if poll is active
        if not value.poll.is_active:
            raise serializers.ValidationError("This poll is not active.")
        
        # Check if poll has expired
        if value.poll.is_expired():
            raise serializers.ValidationError("This poll has expired.")
        
        return value

    def validate(self, data):
        """Validate vote data"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required.")
        
        option = data['option']
        poll = option.poll
        user = request.user if request.user.is_authenticated else None
        ip_address = self.get_client_ip(request)
        
        # Check for duplicate votes if not allowed
        if not poll.allow_multiple_votes:
            existing_votes = Vote.objects.filter(option__poll=poll)
            
            if user:
                if existing_votes.filter(user=user).exists():
                    raise serializers.ValidationError("You have already voted in this poll.")
            
            if existing_votes.filter(ip_address=ip_address).exists():
                raise serializers.ValidationError("A vote from your IP address already exists for this poll.")
        
        return data

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def create(self, validated_data):
        """Create vote with additional data"""
        request = self.context.get('request')
        
        validated_data['ip_address'] = self.get_client_ip(request)
        validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        if request.user.is_authenticated:
            validated_data['user'] = request.user
        
        return super().create(validated_data)


class PollResultSerializer(serializers.Serializer):
    """Serializer for poll results"""
    poll_id = serializers.IntegerField()
    poll_title = serializers.CharField()
    total_votes = serializers.IntegerField()
    is_expired = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)
    options = serializers.ListField(
        child=serializers.DictField()
    )


class VoteStatsSerializer(serializers.Serializer):
    """Serializer for voting statistics"""
    total_polls = serializers.IntegerField()
    total_votes = serializers.IntegerField()
    active_polls = serializers.IntegerField()
    recent_votes = serializers.IntegerField()
    top_polls = serializers.ListField(
        child=serializers.DictField()
    )
