"""WSGI entry point for running the app under a production server.

gunicorn wsgi:app        # Render Web Service
"""
from app import create_app

app = create_app()