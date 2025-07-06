from pathlib import Path
from typing import NoReturn


def ensure_parent(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def exists(path: str):
    p = Path(path)
    return p.exists()


def try_read_text(path: str):
    return read_text(path) if exists(path) else ""


def read_text(path: str):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise_error(f"File not found: {path}")


def write_text(path: str, data: str):
    ensure_parent(path)
    with open(path, "w") as f:
        return f.write(data)


def append_text(path: str, data: str):
    ensure_parent(path)
    with open(path, "a") as f:
        return f.write(data)


def raise_error(x: str) -> NoReturn:
    print(x)
    import sys

    sys.exit(-1)


def now_as_str():
    import datetime

    now = datetime.datetime.now()
    # YYYYMMDD_HHMMSS
    return now.strftime("%Y%m%d_%H%M%S")


def archive_file(path: str):
    now = now_as_str()
    of = path + "." + now
    write_text(of, read_text(path))
    write_text(path, "")


def append_file(path: str, data: str):
    xx = read_text(path) if exists(path) else ""
    xx += data
    write_text(path, data)
