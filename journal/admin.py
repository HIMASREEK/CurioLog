from django.contrib import admin
from .models import Entry, Category, Tag

admin.site.register(Entry)
admin.site.register(Category)
admin.site.register(Tag)