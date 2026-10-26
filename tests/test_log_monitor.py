import os
import sys

# Let the tests import log_monitor.py from the folder above.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import log_monitor as lm


def test_parse_valid_line():
    entry = lm.parse_line("2026-10-24 09:15:32,123 ERROR [Gateway] Timeout after 30s")
    assert entry["level"] == "ERROR"
    assert entry["component"] == "Gateway"
    assert entry["message"] == "Timeout after 30s"


def test_parse_bad_line_returns_none():
    assert lm.parse_line("not a log line") is None


def test_normalise_groups_similar_messages():
    assert lm.normalise("Order 123 rejected") == lm.normalise("Order 456 rejected")


def test_analyse_counts_levels_and_malformed():
    lines = [
        "2026-10-24 09:00:01,000 INFO [A] ok",
        "2026-10-24 09:00:02,000 ERROR [A] Timeout after 5s",
        "2026-10-24 09:00:03,000 ERROR [B] Timeout after 9s",
        "garbage",
    ]
    stats = lm.analyse(lines)
    assert stats["levels"]["INFO"] == 1
    assert lm.count_errors(stats) == 2
    assert stats["malformed"] == 1
    assert stats["error_messages"]["Timeout after <n>s"] == 2


def test_find_spikes_flags_busy_minute():
    per_minute = {"09:00": 1, "09:01": 1, "09:02": 1, "09:03": 20}
    assert lm.find_spikes(per_minute) == [("09:03", 20)]


def test_threshold_exit_code(tmp_path):
    log = tmp_path / "t.log"
    log.write_text("2026-10-24 09:00:01,000 ERROR [A] boom\n" * 3)
    assert lm.main([str(log), "--threshold", "2"]) == 1
    assert lm.main([str(log), "--threshold", "10"]) == 0