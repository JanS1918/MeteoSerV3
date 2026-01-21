from pathlib import Path


def tail(path: Path, lines: int = 40) -> list[str]:
    if not path.exists():
        return [f"{path.name} missing"]
    data = path.read_text(errors="ignore").splitlines()
    suffix = data[-lines:] if len(data) >= lines else data
    return suffix or [f"{path.name} is empty"]


def main() -> None:
    base = Path("C:/mosquitto/log")
    for name in ["mosquitto.log", "mosquitto_stdout.log", "mosquitto_stderr.log"]:
        path = base / name
        print("===", name, "===")
        print("\n".join(tail(path)))
        print()


if __name__ == "__main__":
    main()
