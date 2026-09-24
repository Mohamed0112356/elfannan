from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]

def load_artist(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return json.loads(p.read_text(encoding="utf-8"))
