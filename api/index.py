"""Vercel entry point: runs the Flask app in backend/ as a serverless function.

vercel.json sends every /api/* request here; Flask routes it as usual.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from app import app  # noqa: E402  (Vercel looks for a WSGI variable named `app`)
