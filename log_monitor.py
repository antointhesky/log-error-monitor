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