from django.urls import path
from . import views

app_name = 'polls'

urlpatterns = [
    # Health check endpoint
    path('health/', views.health_check, name='health-check'),
    
    # Poll management endpoints
    path('polls/', views.PollListCreateView.as_view(), name='poll-list-create'),
    path('polls/<int:pk>/', views.PollDetailView.as_view(), name='poll-detail'),
    path('polls/<int:pk>/results/', views.PollResultsView.as_view(), name='poll-results'),
    path('polls/<int:pk>/toggle-status/', views.toggle_poll_status, name='poll-toggle-status'),
    
    # Voting endpoints
    path('vote/', views.VoteCreateView.as_view(), name='vote-create'),
    
    # User-specific endpoints
    path('user/votes/', views.user_votes, name='user-votes'),
    path('user/polls/', views.user_polls, name='user-polls'),
    
    # Statistics endpoint
    path('statistics/', views.vote_statistics, name='vote-statistics'),
]
