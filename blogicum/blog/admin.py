from django.contrib import admin

from .models import Category, Location, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'pub_date',
        'is_published',
        'author',
        'category',
        'location',
    )
    list_editable = (
        'is_published',
        'category',
        'location',
    )
    search_fields = (
        'title',
    )
    list_filter = (
        'category',
    )
    list_display_links = (
        'title',
    )


admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Post, PostAdmin)
admin.site.empty_value_display = 'Не задано'
