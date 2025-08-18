"""Command handlers for strukt2meta.
"""

from .base import BaseCommand
from .generate import GenerateCommand
from .inject import InjectCommand
from .discover import DiscoverCommand
from .analyze import AnalyzeCommand
from .batch import BatchCommand
from .dirmeta import DirmetaCommand
from .clearmeta import ClearmetaCommand
from .unlist import UnlistCommand
from .kriterien import KriterienCommand
from .ofs import OfsCommand

__all__ = [
    'GenerateCommand',
    'InjectCommand',
    'DiscoverCommand',
    'AnalyzeCommand',
    'BatchCommand',
    'DirmetaCommand',
    'ClearmetaCommand',
    'UnlistCommand',
    'KriterienCommand',
    'OfsCommand'
]