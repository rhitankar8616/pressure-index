"""
Page modules for Pressure Index Application
"""

from .live_tracker import render_live_tracker
from .past_matches import render_past_matches
from .how_it_works import render_how_it_works

__all__ = [
    'render_live_tracker',
    'render_past_matches',
    'render_how_it_works'
]
