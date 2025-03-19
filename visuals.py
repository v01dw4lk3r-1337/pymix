import sys
import time
import threading

# ANSI color codes for formatting
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Loader animation function
def spinning_cursor(stop_event, message="Fetching info"):
    """Displays a rotating loader until `stop_event` is set."""
    cursor = ["/", "-", "\\", "|"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{BOLD}{CYAN}{message}... {cursor[i]} {RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(cursor)
    sys.stdout.write("\r" + " " * 30 + "\r")  # Clear line
    sys.stdout.flush()