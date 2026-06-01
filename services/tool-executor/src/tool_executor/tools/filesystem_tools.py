"""Filesystem Tools — Safe file operations"""
import os
import shutil
from pathlib import Path
from typing import Optional


def read_file(path: str, encoding: str = "utf-8", max_lines: Optional[int] = None) -> dict:
    """Read file contents safely."""
    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}
    if not p.is_file():
        return {"error": f"Not a file: {path}"}
    try:
        content = p.read_text(encoding=encoding)
        lines = content.split("\n")
        if max_lines:
            lines = lines[:max_lines]
        return {
            "content": "\n".join(lines),
            "total_lines": len(content.split("\n")),
            "truncated": max_lines is not None and len(content.split("\n")) > max_lines,
            "size_bytes": p.stat().st_size,
        }
    except Exception as e:
        return {"error": str(e)}


def write_file(path: str, content: str, encoding: str = "utf-8",
               create_dirs: bool = True) -> dict:
    """Write content to file."""
    p = Path(path)
    try:
        if create_dirs:
            p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding=encoding)
        return {"success": True, "bytes_written": len(content.encode(encoding)), "path": path}
    except Exception as e:
        return {"error": str(e)}


def list_directory(path: str = ".", pattern: str = None,
                   recursive: bool = False, show_hidden: bool = False) -> dict:
    """List directory contents."""
    p = Path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}
    if not p.is_dir():
        return {"error": f"Not a directory: {path}"}

    items = []
    glob_pattern = pattern or ("**/*" if recursive else "*")
    for item in p.glob(glob_pattern):
        if not show_hidden and item.name.startswith("."):
            continue
        stat = item.stat()
        items.append({
            "name": item.name,
            "path": str(item),
            "type": "directory" if item.is_dir() else "file",
            "size": stat.st_size,
            "modified": stat.st_mtime,
        })

    items.sort(key=lambda x: (x["type"] != "directory", x["name"]))
    return {"items": items, "count": len(items), "path": str(p)}


def file_info(path: str) -> dict:
    """Get detailed file information."""
    p = Path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}
    stat = p.stat()
    return {
        "path": str(p.absolute()),
        "name": p.name,
        "type": "directory" if p.is_dir() else "file",
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
        "is_symlink": p.is_symlink(),
        "permissions": oct(stat.st_mode)[-3:],
    }


def copy_file(source: str, destination: str) -> dict:
    """Copy file or directory."""
    src = Path(source)
    dst = Path(destination)
    if not src.exists():
        return {"error": f"Source not found: {source}"}
    try:
        if src.is_dir():
            shutil.copytree(str(src), str(dst))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
        return {"success": True, "source": source, "destination": destination}
    except Exception as e:
        return {"error": str(e)}


def move_file(source: str, destination: str) -> dict:
    """Move file or directory."""
    src = Path(source)
    dst = Path(destination)
    if not src.exists():
        return {"error": f"Source not found: {source}"}
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"success": True, "source": source, "destination": destination}
    except Exception as e:
        return {"error": str(e)}


def delete_file(path: str, recursive: bool = False) -> dict:
    """Delete file or directory."""
    p = Path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}
    try:
        if p.is_dir():
            if recursive:
                shutil.rmtree(str(p))
            else:
                p.rmdir()
        else:
            p.unlink()
        return {"success": True, "path": path}
    except Exception as e:
        return {"error": str(e)}


def search_files(path: str, pattern: str, content_search: bool = False) -> dict:
    """Search for files by name or content."""
    p = Path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}

    results = []
    if content_search:
        for file in p.rglob("*"):
            if file.is_file():
                try:
                    content = file.read_text(errors="ignore")
                    if pattern.lower() in content.lower():
                        lines = content.split("\n")
                        matches = [
                            {"line": i + 1, "text": line.strip()}
                            for i, line in enumerate(lines)
                            if pattern.lower() in line.lower()
                        ]
                        results.append({"path": str(file), "matches": matches[:5]})
                except Exception:
                    pass
    else:
        for file in p.rglob(f"*{pattern}*"):
            results.append({"path": str(file), "name": file.name})

    return {"results": results[:50], "total": len(results)}
