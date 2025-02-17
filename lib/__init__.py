"""
Utility functions for journal_xtractor.py
"""

import html


def escape_html(text_to_escape):
    """Use built-in HTML escape and replace apostrophe hex code with id"""
    return html.escape(text_to_escape).replace("#x27", "apos")
