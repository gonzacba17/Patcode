"""
Sistema CLI profesional para PatCode.
Incluye comandos slash, plan mode y formatter.
"""

from cli.commands import command_registry, Command
from cli.formatter import formatter, OutputFormatter

__all__ = [
    'command_registry',
    'Command',
    'formatter',
    'OutputFormatter'
]
