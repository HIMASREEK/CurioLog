from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Entry(models.Model):
    ENTRY_TYPES = [
        ('Question', 'Question'),
        ('Fact', 'Fact'),
        ('Idea', 'Idea'),
        ('Experiment', 'Experiment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='Question')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
