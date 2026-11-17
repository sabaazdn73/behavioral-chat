"""Behavioral Chat: read-only, symmetric behaviour analysis of two-person chat exports."""
from .analyze import analyze
from .parsers import parse_path, parse_text

__all__ = ["analyze", "parse_path", "parse_text"]
__version__ = "0.1.0"
