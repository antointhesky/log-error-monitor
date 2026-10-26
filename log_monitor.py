"""Log Error Monitor.

Reads an application log file and summarises the errors in it.

Expected line format:
    2026-10-24 09:15:32,123 ERROR [OrderGateway] Connection timeout after 30s
"""

import argparse
import re
import sys
from collections import Counter

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
ERROR_LEVELS = ("ERROR", "CRITICAL", "FATAL")


def parse_line(line):
    """Return a dict for a valid log line, or None if it does not match."""
    match = LINE_RE.match(line.strip())
    if not match:
        return None
    entry = match.groupdict()
    if entry["level"] not in LEVELS:
        return None
    return entry


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


def find_spikes(errors_per_minute, factor=3):
    """Return minutes where errors are at least `factor` x the average."""
    if not errors_per_minute:
        return []
    average = sum(errors_per_minute.values()) / len(errors_per_minute)
    limit = max(average * factor, 2)
    return sorted(
        (minute, count)
        for minute, count in errors_per_minute.items()
        if count >= limit
    )


def print_report(stats, top):
    """Print the summary in a readable format."""
    print(f"Lines read:      {stats['total']}")
    print(f"Unparsed lines:  {stats['malformed']}")
    print(f"Total errors:    {count_errors(stats)}\n")

    print("Messages by level")
    for level, count in stats["levels"].most_common():
        print(f"  {level:<9}{count}")

    print(f"\nTop {top} error messages")
    for message, count in stats["error_messages"].most_common(top):
        print(f"  {count:>4}  {message}")

    print("\nErrors by component")
    for component, count in stats["error_components"].most_common():
        print(f"  {count:>4}  {component}")

    spikes = find_spikes(stats["errors_per_minute"])
    print("\nError spikes (per minute)")
    if spikes:
        for minute, count in spikes:
            print(f"  {minute}  {count} errors")
    else:
        print("  none found")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Summarise errors in a log file.")
    parser.add_argument("logfile", help="path to the log file")
    parser.add_argument("--top", type=int, default=5,
                        help="how many top error messages to show (default 5)")
    parser.add_argument("--threshold", type=int, default=None,
                        help="exit with code 1 if total errors exceed this number")
    args = parser.parse_args(argv)

    try:
        with open(args.logfile, encoding="utf-8", errors="replace") as handle:
            stats = analyse(handle)
    except FileNotFoundError:
        print(f"Error: file not found: {args.logfile}", file=sys.stderr)
        return 2

    print_report(stats, args.top)

    if args.threshold is not None and count_errors(stats) > args.threshold:
        print(f"\nALERT: errors exceed threshold of {args.threshold}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())