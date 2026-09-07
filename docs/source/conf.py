"""Sphinx configuration for the News Application."""

import os
import sys

import django

sys.path.insert(0, os.path.abspath("../.."))

os.environ["DJANGO_SETTINGS_MODULE"] = "news_project.settings"
django.setup()

project = "News Application"
copyright = "2026, Veronica"
author = "Veronica"
version = "1.0"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
