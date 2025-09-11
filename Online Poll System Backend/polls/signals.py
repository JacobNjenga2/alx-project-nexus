from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Poll, Vote


@receiver(post_save, sender=Vote)
def invalidate_poll_cache(sender, instance, created, **kwargs):
    """
    Invalidate poll results cache when a new vote is cast.
    This ensures real-time result updates.
    """
    if created:
        poll_id = instance.option.poll.id
        cache_keys = [
            f'poll_results_{poll_id}',
            f'poll_stats',
            f'top_polls'
        ]
        cache.delete_many(cache_keys)


@receiver(post_save, sender=Poll)
def invalidate_poll_list_cache(sender, instance, created, **kwargs):
    """
    Invalidate poll list cache when a poll is created or updated.
    """
    cache_keys = [
        'poll_list',
        'active_polls',
        'poll_stats'
    ]
    cache.delete_many(cache_keys)


@receiver(pre_delete, sender=Poll)
def cleanup_poll_cache(sender, instance, **kwargs):
    """
    Clean up poll-specific cache entries when a poll is deleted.
    """
    poll_id = instance.id
    cache_keys = [
        f'poll_results_{poll_id}',
        'poll_list',
        'active_polls',
        'poll_stats',
        'top_polls'
    ]
    cache.delete_many(cache_keys)
