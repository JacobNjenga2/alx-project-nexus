from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from django.db.models import Count, Q, F
from django.utils import timezone
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Poll, PollOption, Vote, VoteSession
from .serializers import (
    PollCreateSerializer, PollDetailSerializer, PollListSerializer,
    VoteSerializer, PollResultSerializer, VoteStatsSerializer
)

# Set up logger
logger = logging.getLogger(__name__)


class PollListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating polls.
    GET: List all active polls with pagination
    POST: Create a new poll (requires authentication)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PollCreateSerializer
        return PollListSerializer
    
    def get_queryset(self):
        queryset = Poll.objects.filter(is_active=True).select_related('created_by')
        
        # Add annotations for efficient querying
        queryset = queryset.annotate(
            total_votes=Count('options__votes'),
            option_count=Count('options'),
            is_expired=Q(expires_at__lt=timezone.now())
        )
        
        # Filter by search query
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        # Filter by active/expired status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'expired':
            queryset = queryset.filter(expires_at__lt=timezone.now())
        elif status_filter == 'active':
            queryset = queryset.filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @swagger_auto_schema(
        operation_description="List all active polls with optional filtering",
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY, 
                description="Search polls by title or description",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'status', openapi.IN_QUERY,
                description="Filter by poll status (active/expired)",
                type=openapi.TYPE_STRING,
                enum=['active', 'expired']
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new poll with options",
        request_body=PollCreateSerializer,
        responses={201: PollDetailSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PollDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting individual polls.
    GET: Retrieve poll details with options
    PUT/PATCH: Update poll (only by creator)
    DELETE: Delete poll (only by creator)
    """
    serializer_class = PollDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Poll.objects.select_related('created_by').prefetch_related(
            'options'
        ).annotate(
            total_votes=Count('options__votes'),
            is_expired=Q(expires_at__lt=timezone.now())
        )
    
    def get_permissions(self):
        """
        Instantiate and return the list of permissions required for this view.
        """
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def update(self, request, *args, **kwargs):
        """Only allow poll creator to update"""
        poll = self.get_object()
        if poll.created_by != request.user:
            return Response(
                {'error': 'You can only update your own polls.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only allow poll creator to delete"""
        poll = self.get_object()
        if poll.created_by != request.user:
            return Response(
                {'error': 'You can only delete your own polls.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class VoteCreateView(generics.CreateAPIView):
    """
    API view for casting votes.
    POST: Cast a vote for a poll option
    """
    serializer_class = VoteSerializer
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Cast a vote for a poll option",
        request_body=VoteSerializer,
        responses={
            201: openapi.Response(
                description="Vote cast successfully",
                schema=VoteSerializer
            ),
            400: openapi.Response(
                description="Validation error (duplicate vote, expired poll, etc.)"
            ),
            429: openapi.Response(
                description="Rate limit exceeded"
            )
        }
    )
    @ratelimit(key='ip', rate='10/m', method='POST', block=True)
    def post(self, request, *args, **kwargs):
        logger.info(f"Vote attempt from IP: {self.get_client_ip(request)}")
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == 201:
                logger.info(f"Vote successfully cast for option: {request.data.get('option')}")
            return response
        except Exception as e:
            logger.error(f"Error casting vote: {str(e)}")
            raise
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PollResultsView(generics.RetrieveAPIView):
    """
    API view for retrieving poll results.
    GET: Get real-time poll results with vote counts and percentages
    """
    permission_classes = [AllowAny]
    serializer_class = PollResultSerializer
    
    def get_object(self):
        poll_id = self.kwargs['pk']
        try:
            poll = Poll.objects.get(pk=poll_id)
            return poll.get_results()
        except Poll.DoesNotExist:
            return None
    
    def retrieve(self, request, *args, **kwargs):
        results = self.get_object()
        if results is None:
            return Response(
                {'error': 'Poll not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(results)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Get real-time poll results with vote counts and percentages"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    operation_description="Get voting statistics and analytics",
    responses={200: VoteStatsSerializer}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def vote_statistics(request):
    """
    API endpoint for voting statistics and analytics.
    Returns overall statistics about polls and votes.
    """
    # Calculate statistics
    total_polls = Poll.objects.count()
    total_votes = Vote.objects.count()
    active_polls = Poll.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    ).count()
    
    # Recent votes (last 24 hours)
    recent_votes = Vote.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=1)
    ).count()
    
    # Top polls by vote count
    top_polls = Poll.objects.annotate(
        vote_count=Count('options__votes')
    ).filter(
        vote_count__gt=0
    ).order_by('-vote_count')[:5].values(
        'id', 'title', 'vote_count', 'created_at'
    )
    
    stats = {
        'total_polls': total_polls,
        'total_votes': total_votes,
        'active_polls': active_polls,
        'recent_votes': recent_votes,
        'top_polls': list(top_polls)
    }
    
    serializer = VoteStatsSerializer(stats)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Get user's voting history",
    responses={200: VoteSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_votes(request):
    """
    API endpoint for retrieving user's voting history.
    Returns all votes cast by the authenticated user.
    """
    votes = Vote.objects.filter(user=request.user).select_related(
        'option', 'option__poll'
    ).order_by('-created_at')
    
    serializer = VoteSerializer(votes, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Get polls created by the authenticated user",
    responses={200: PollListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_polls(request):
    """
    API endpoint for retrieving polls created by the authenticated user.
    """
    polls = Poll.objects.filter(created_by=request.user).annotate(
        total_votes=Count('options__votes'),
        option_count=Count('options'),
        is_expired=Q(expires_at__lt=timezone.now())
    ).order_by('-created_at')
    
    serializer = PollListSerializer(polls, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    operation_description="Toggle poll active status",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        }
    ),
    responses={200: PollDetailSerializer}
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_poll_status(request, pk):
    """
    API endpoint for toggling poll active status.
    Only poll creator can toggle status.
    """
    try:
        poll = Poll.objects.get(pk=pk)
    except Poll.DoesNotExist:
        return Response(
            {'error': 'Poll not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if poll.created_by != request.user:
        return Response(
            {'error': 'You can only modify your own polls.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    is_active = request.data.get('is_active')
    if is_active is not None:
        poll.is_active = bool(is_active)
        poll.save()
    
    serializer = PollDetailSerializer(poll)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Health check endpoint for monitoring",
    responses={
        200: openapi.Response(
            description="Service is healthy",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING),
                    'version': openapi.Schema(type=openapi.TYPE_STRING),
                    'database': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    Returns service status and basic system information.
    """
    from django.db import connection
    from django.conf import settings
    
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected',
            'environment': 'production' if not settings.DEBUG else 'development'
        }
        
        logger.info("Health check passed")
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            {
                'status': 'unhealthy',
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )