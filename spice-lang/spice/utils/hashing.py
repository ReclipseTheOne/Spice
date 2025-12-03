import hashlib
from pathlib import Path

def generate_spc_stub(path: Path) -> str:
    """Generate a .spc temp stub name"""
    source = path.read_text(encoding='utf-8')
    full: str = path.resolve().as_posix() + source
    hash_str = hashlib.sha256(full.encode()).hexdigest()[:64]
    return f"spc_{hash_str}.spc"