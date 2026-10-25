"""Log Error Monitor.

Reads an application log file and summarises the errors in it.

Expected line format:
    2026-10-24 09:15:32,123 ERROR [OrderGateway] Connection timeout after 30s
"""

import re

# A regular expression describing one log line.
# The (?P<name>...) parts capture pieces of the line under a name.
LINE_RE = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}) "
    r"(?P<time>\d{2}:\d{2}:\d{2})(?:[,.]\d+)? "
    r"(?P<level>[A-Z]+) "
    r"\[(?P<component>[^\]]+)\] "
    r"(?P<message>.*)$"
)

LEVELS = ("DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL")


def parse_line(line):
    """Return a dict for a valid log line, or None if it does not match."""
    match = LINE_RE.match(line.strip())
    if not match:
        return None
    entry = match.groupdict()
    if entry["level"] not in LEVELS:
        return None
    return entry

import re
from collections import Counter   
ERROR_LEVELS = ("ERROR", "CRITICAL", "FATAL")
def normalise(message):
    """Replace numbers and hex IDs so similar errors group together."""
    message = re.sub(r"0x[0-9a-fA-F]+", "<hex>", message)
    message = re.sub(r"\d+", "<n>", message)
    return message


def analyse(lines):
    """Read an iterable of lines and return summary statistics."""
    levels = Counter()
    error_messages = Counter()
    error_components = Counter()
    errors_per_minute = Counter()
    malformed = 0
    total = 0

    for line in lines:
        if not line.strip():
            continue
        total += 1
        entry = parse_line(line)
        if entry is None:
            malformed += 1
            continue
        levels[entry["level"]] += 1
        if entry["level"] in ERROR_LEVELS:
            error_messages[normalise(entry["message"])] += 1
            error_components[entry["component"]] += 1
            minute = f'{entry["date"]} {entry["time"][:5]}'
            errors_per_minute[minute] += 1

    return {
        "total": total,
        "malformed": malformed,
        "levels": levels,
        "error_messages": error_messages,
        "error_components": error_components,
        "errors_per_minute": errors_per_minute,
    }


def count_errors(stats):
    """Total number of ERROR, CRITICAL and FATAL lines."""
    return sum(stats["levels"][level] for level in ERROR_LEVELS)