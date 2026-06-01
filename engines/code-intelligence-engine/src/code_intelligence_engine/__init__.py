"""Code Intelligence Engine — Code analysis, indexing, and understanding"""
from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class CodeIndex:
    id: str = field(default_factory=lambda: f"IDX-{uuid.uuid4().hex[:8]}")
    path: str = ""
    language: str = ""
    symbols: list[dict] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    complexity: int = 0
    lines: int = 0


class CodeIntelligenceEngine:
    """Analyze and index codebases for intelligent navigation."""

    def __init__(self):
        self.indexes: dict[str, CodeIndex] = {}

    def index_file(self, path: str, content: str) -> CodeIndex:
        language = self._detect_language(path)
        lines = content.count("\n") + 1
        symbols = self._extract_symbols(content, language)
        index = CodeIndex(path=path, language=language, symbols=symbols, lines=lines)
        self.indexes[index.id] = index
        return index

    def _detect_language(self, path: str) -> str:
        ext_map = {".py": "python", ".js": "javascript", ".ts": "typescript",
                   ".rs": "rust", ".go": "go", ".java": "java"}
        for ext, lang in ext_map.items():
            if path.endswith(ext):
                return lang
        return "unknown"

    def _extract_symbols(self, content: str, language: str) -> list[dict]:
        symbols = []
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if language == "python":
                if stripped.startswith("def "):
                    symbols.append({"type": "function", "name": stripped[4:].split("(")[0], "line": i})
                elif stripped.startswith("class "):
                    symbols.append({"type": "class", "name": stripped[6:].split("(")[0].split(":")[0], "line": i})
            elif language in ("javascript", "typescript"):
                if "function " in stripped or "=>" in stripped:
                    symbols.append({"type": "function", "name": stripped[:50], "line": i})
        return symbols

    def search_symbols(self, query: str) -> list[dict]:
        results = []
        for idx in self.indexes.values():
            for sym in idx.symbols:
                if query.lower() in sym.get("name", "").lower():
                    results.append({**sym, "file": idx.path})
        return results
