# Log Error Monitor

A small Python command-line tool that reads an application log, summarises what went wrong and can act as a simple alert check. I built it to practise the kind of log review done in application support: spotting error patterns, separating background noise from incidents, and automating a repetitive check.

## What it does

- Counts log lines by level (INFO, WARN, ERROR and so on)
- Groups similar errors by replacing numbers and hex IDs, so `Order 123 rejected` and `Order 456 rejected` count as one issue
- Shows the top errors and which component produces the most
- Flags error spikes, meaning minutes with far more errors than average
- Counts lines that don't match the expected format instead of crashing
- Exits with code 1 when errors exceed `--threshold`, so it can be used in scripts or scheduled jobs

## Usage

```bash
python3 make_sample_log.py                       # create a fake log
python3 log_monitor.py sample_logs/app.log       # full report
python3 log_monitor.py sample_logs/app.log --top 3 --threshold 50
echo $?                                          # 1 if the threshold was exceeded
```

Exit codes: `0` = fine, `1` = errors over threshold, `2` = file not found.

Expected log format:

```
2026-10-24 09:15:32,123 ERROR [OrderGateway] Connection timeout after 30s
```

## Run the tests

```bash
pip install pytest
python3 -m pytest
```

## The same idea with Linux commands

The tool automates checks like these:

```bash
grep -c " ERROR " sample_logs/app.log                                                # count errors
grep " ERROR " sample_logs/app.log | awk '{print $4}' | sort | uniq -c | sort -rn    # errors by component
grep " ERROR " sample_logs/app.log | cut -c1-16 | sort | uniq -c | sort -rn | head   # busiest minutes
```

## Possible improvements

- Filter by time range or component
- Read compressed logs (`.gz`) and follow a live file
- Send an email or chat alert when the threshold is exceeded
- Support more than one log format