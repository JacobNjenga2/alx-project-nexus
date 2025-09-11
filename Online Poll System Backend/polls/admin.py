from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Poll, PollOption, Vote, VoteSession


class PollOptionInline(admin.TabularInline):
    """Inline admin for poll options"""
    model = PollOption
    extra = 2
    fields = ['text', 'order']
    ordering = ['order']


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    """Admin interface for Poll model"""
    list_display = [
        'title', 'created_by', 'is_active', 'created_at', 
        'expires_at', 'vote_count', 'option_count'
    ]
    list_filter = [
        'is_active', 'created_at', 'expires_at', 'allow_multiple_votes'
    ]
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'vote_count', 'option_count']
    inlines = [PollOptionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'created_by')
        }),
        ('Settings', {
            'fields': ('is_active', 'allow_multiple_votes', 'expires_at')
        }),
        ('Statistics', {
            'fields': ('vote_count', 'option_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('created_by').annotate(
            vote_count=Count('options__votes'),
            option_count=Count('options')
        )
    
    def vote_count(self, obj):
        """Display vote count"""
        return obj.vote_count
    vote_count.short_description = 'Total Votes'
    vote_count.admin_order_field = 'vote_count'
    
    def option_count(self, obj):
        """Display option count"""
        return obj.option_count
    option_count.short_description = 'Options'
    option_count.admin_order_field = 'option_count'
    
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        """Mark selected polls as active"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} poll(s) marked as active.'
        )
    make_active.short_description = "Mark selected polls as active"
    
    def make_inactive(self, request, queryset):
        """Mark selected polls as inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} poll(s) marked as inactive.'
        )
    make_inactive.short_description = "Mark selected polls as inactive"


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    """Admin interface for PollOption model"""
    list_display = ['text', 'poll', 'order', 'vote_count', 'created_at']
    list_filter = ['poll__is_active', 'created_at']
    search_fields = ['text', 'poll__title']
    readonly_fields = ['vote_count', 'created_at']
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('poll').annotate(
            vote_count=Count('votes')
        )
    
    def vote_count(self, obj):
        """Display vote count"""
        return obj.vote_count
    vote_count.short_description = 'Votes'
    vote_count.admin_order_field = 'vote_count'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin interface for Vote model"""
    list_display = [
        'get_voter', 'option', 'get_poll', 'ip_address', 'created_at'
    ]
    list_filter = [
        'created_at', 'option__poll__title', 'option__poll__is_active'
    ]
    search_fields = [
        'user__username', 'option__text', 'option__poll__title', 'ip_address'
    ]
    readonly_fields = ['created_at', 'ip_address', 'user_agent']
    
    fieldsets = (
        ('Vote Information', {
            'fields': ('user', 'option')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'option', 'option__poll')
    
    def get_voter(self, obj):
        """Display voter information"""
        if obj.user:
            return obj.user.username
        return f"Anonymous ({obj.ip_address})"
    get_voter.short_description = 'Voter'
    
    def get_poll(self, obj):
        """Display poll title"""
        return obj.option.poll.title
    get_poll.short_description = 'Poll'
    get_poll.admin_order_field = 'option__poll__title'
    
    def has_add_permission(self, request):
        """Disable manual vote creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable vote editing"""
        return False


@admin.register(VoteSession)
class VoteSessionAdmin(admin.ModelAdmin):
    """Admin interface for VoteSession model"""
    list_display = [
        'session_key', 'ip_address', 'created_at', 'last_activity'
    ]
    list_filter = ['created_at', 'last_activity']
    search_fields = ['session_key', 'ip_address']
    readonly_fields = ['session_key', 'ip_address', 'user_agent', 'created_at', 'last_activity']
    
    def has_add_permission(self, request):
        """Disable manual session creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable session editing"""
        return False


# Customize admin site headers
admin.site.site_header = "Online Poll System Administration"
admin.site.site_title = "Poll System Admin"
admin.site.index_title = "Welcome to Poll System Administration"