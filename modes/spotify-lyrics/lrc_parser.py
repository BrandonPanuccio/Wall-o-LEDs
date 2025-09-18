import re

def parse_lrc(lrc_text):
    pattern = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")
    lines = []
    for line in lrc_text.splitlines():
        match = pattern.match(line)
        if match:
            minutes, seconds, text = match.groups()
            timestamp_ms = int(minutes) * 60_000 + int(float(seconds) * 1000)
            lines.append((timestamp_ms, text.strip()))
    return sorted(lines, key=lambda x: x[0])
