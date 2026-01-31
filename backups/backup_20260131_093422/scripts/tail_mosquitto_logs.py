from pathlib import Path

LOG_DIR = Path("C:/mosquitto/log")
LOG_FILES = ["mosquitto_stdout.log", "mosquitto_stderr.log", "mosquitto.log"]

for name in LOG_FILES:
    path = LOG_DIR / name
    print(f"\n== {name} ==")
    if not path.exists():
        print("missing")
        continue
    data = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in data[-20:]:
        print(line)
