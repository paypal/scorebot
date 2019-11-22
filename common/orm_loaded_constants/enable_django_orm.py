"""
    This will setup Django ORM and models so they can be used outside of the Django server.
    NOTE: Only import this from code that is not a part of the Django server.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scorebot.settings")
import django


def enable_django_orm():
    django.setup()
