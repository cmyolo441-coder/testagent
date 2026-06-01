"""Diff Viewer Widget — Code diff display"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiffLine:
    line_number_old: Optional[int] = None
    line_number_new: Optional[int] = None
    content: str = ""
    line_type: str = "context"  # context, addition, deletion, header


@dataclass
class DiffHunk:
    header: str = ""
    lines: list[DiffLine] = field(default_factory=list)
    start_old: int = 0
    start_new: int = 0
    length_old: int = 0
    length_new: int = 0


@dataclass
class DiffFile:
    old_path: str = ""
    new_path: str = ""
    hunks: list[DiffHunk] = field(default_factory=list)
    status: str = "modified"  # added, deleted, modified, renamed


class DiffViewer:
    """Code diff display widget."""

    def __init__(self, context_lines: int = 3):
        self.context_lines = context_lines
        self.files: list[DiffFile] = []
        self.selected_file_index: int = 0
        self.show_line_numbers: bool = True
        self.wrap_lines: bool = False
        self.max_line_width: int = 80

    def add_file_diff(self, old_path: str, new_path: str,
                      status: str = "modified") -> DiffFile:
        file_diff = DiffFile(
            old_path=old_path,
            new_path=new_path,
            status=status,
        )
        self.files.append(file_diff)
        return file_diff

    def add_hunk(self, file_index: int, header: str = "",
                 start_old: int = 0, start_new: int = 0,
                 lines: list[tuple[str, str]] = None) -> Optional[DiffHunk]:
        if file_index < 0 or file_index >= len(self.files):
            return None

        hunk = DiffHunk(
            header=header,
            start_old=start_old,
            start_new=start_new,
        )

        if lines:
            old_num = start_old
            new_num = start_new
            for line_type, content in lines:
                if line_type == "+":
                    dl = DiffLine(line_number_new=new_num, content=content, line_type="addition")
                    new_num += 1
                elif line_type == "-":
                    dl = DiffLine(line_number_old=old_num, content=content, line_type="deletion")
                    old_num += 1
                else:
                    dl = DiffLine(line_number_old=old_num, line_number_new=new_num,
                                  content=content, line_type="context")
                    old_num += 1
                    new_num += 1
                hunk.lines.append(dl)

        self.files[file_index].hunks.append(hunk)
        return hunk

    def parse_unified_diff(self, diff_text: str, file_index: int = 0):
        lines = diff_text.split("\n")
        current_hunk = None

        for line in lines:
            if line.startswith("@@"):
                if current_hunk:
                    self.files[file_index].hunks.append(current_hunk)
                parts = line.split("@@")
                if len(parts) >= 3:
                    range_str = parts[1].strip()
                    old_range, new_range = range_str.split("+") if "+" in range_str else (range_str, "")
                    current_hunk = DiffHunk(
                        header=line,
                        start_old=int(old_range.split(",")[0].replace("-", "")) if "-" in old_range else 1,
                        start_new=int(new_range.split(",")[0]) if new_range else 1,
                    )
                else:
                    current_hunk = DiffHunk(header=line)
            elif current_hunk:
                if line.startswith("+"):
                    current_hunk.lines.append(DiffLine(content=line[1:], line_type="addition"))
                elif line.startswith("-"):
                    current_hunk.lines.append(DiffLine(content=line[1:], line_type="deletion"))
                else:
                    current_hunk.lines.append(DiffLine(content=line[1:] if line.startswith(" ") else line,
                                                       line_type="context"))

        if current_hunk:
            self.files[file_index].hunks.append(current_hunk)

    def get_added_lines(self) -> int:
        count = 0
        for f in self.files:
            for h in f.hunks:
                count += sum(1 for l in h.lines if l.line_type == "addition")
        return count

    def get_deleted_lines(self) -> int:
        count = 0
        for f in self.files:
            for h in f.hunks:
                count += sum(1 for l in h.lines if l.line_type == "deletion")
        return count

    def render_file_header(self, file_diff: DiffFile) -> str:
        status_icon = {"added": "+", "deleted": "-", "modified": "~", "renamed": "→"}.get(file_diff.status, "?")
        return f"─── [{status_icon}] {file_diff.new_path or file_diff.old_path} ───"

    def render_hunk(self, hunk: DiffHunk) -> str:
        lines = [f"@@ {hunk.header}" if hunk.header else "@@"]
        for dl in hunk.lines:
            prefix = "+" if dl.line_type == "addition" else "-" if dl.line_type == "deletion" else " "
            content = dl.content[:self.max_line_width]
            if self.show_line_numbers:
                old_num = f"{dl.line_number_old:>4}" if dl.line_number_old is not None else "    "
                new_num = f"{dl.line_number_new:>4}" if dl.line_number_new is not None else "    "
                lines.append(f"{old_num} {new_num} {prefix}{content}")
            else:
                lines.append(f" {prefix}{content}")
        return "\n".join(lines)

    def render_selected_file(self) -> str:
        if not self.files:
            return "  No diff loaded"
        file_diff = self.files[self.selected_file_index]
        parts = [self.render_file_header(file_diff)]
        for hunk in file_diff.hunks:
            parts.append(self.render_hunk(hunk))
        return "\n".join(parts)

    def render_stats(self) -> str:
        added = self.get_added_lines()
        deleted = self.get_deleted_lines()
        files = len(self.files)
        return f"  Files: {files}  +{added}  -{deleted}"

    def render(self) -> str:
        parts = [self.render_stats(), "", self.render_selected_file()]
        return "\n".join(parts)

    def get_stats(self) -> dict:
        return {
            "total_files": len(self.files),
            "added_lines": self.get_added_lines(),
            "deleted_lines": self.get_deleted_lines(),
            "selected_file": self.selected_file_index,
        }
