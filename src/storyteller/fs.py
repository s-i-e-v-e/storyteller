from pathlib import Path
def ensure_parent(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

def exists(path: str):
    p = Path(path)
    return p.exists()

def read_text(path: str):
    with open(path, 'r') as f:
        return f.read()

def write_text(path: str, data: str):
    ensure_parent(path)
    with open(path, 'w') as f:
        return f.write(data)

def append_text(path: str, data: str):
    ensure_parent(path)
    with open(path, 'a') as f:
        return f.write(data)
