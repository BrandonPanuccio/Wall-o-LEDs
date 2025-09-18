# colors.py — simple ANSI coloring (works in WSL/most terminals)
ANSI = {
    "reset":   "\033[0m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "cyan":    "\033[36m",
    "magenta": "\033[35m",
}

def apply_theme(text: str, theme: str, rainbow_step: int = 0) -> str:
    theme = (theme or "plain").lower()
    if theme == "plain":
        return text
    if theme in ANSI:
        return f"{ANSI[theme]}{text}{ANSI['reset']}"
    if theme == "rainbow":
        # 36-step simple palette; per-char color
        out = []
        for i, ch in enumerate(text):
            col = 16 + ((i + rainbow_step) % 36)  # 16..51 are visible enough
            out.append(f"\033[38;5;{col}m{ch}\033[0m")
        return "".join(out)
    return text
