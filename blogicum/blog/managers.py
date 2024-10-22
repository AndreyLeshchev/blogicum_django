from django.db import models
from django.db.models import Count
from django.utils import timezone


class PostManager(models.Manager):
    def get_queryset(self):
        result = super().get_queryset()
        return result.select_related(
            'category',
            'author',
        ).filter(
            is_published=True,
            category__is_published=True,
            pub_date__lt=timezone.now(),
        ).order_by(
            '-pub_date',
        ).annotate(
            comment_count=Count('comments'),
        )
