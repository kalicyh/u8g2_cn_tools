import argparse
import json
import os
import re
import subprocess
from pathlib import Path

STRING_LITERAL_RE = re.compile(r'"((?:\\.|[^"\\])*)"', re.DOTALL)
DEFAULT_SOURCE_ROOTS = (
    Path("applications/main"),
    Path("applications/services"),
    Path("applications/settings"),
    Path("lib"),
)
DEFAULT_ANIMATION_ROOT = Path("assets/dolphin")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate u8g2 .u8f fonts from project Chinese text sources."
    )
    parser.add_argument("--repo-root", required=True, help="Project root to scan.")
    parser.add_argument(
        "--strings",
        action="append",
        default=[],
        help="JSON files containing rows with a text field.",
    )
    parser.add_argument(
        "--source-dir",
        action="append",
        default=[],
        help="Relative source directories to scan for C string literals.",
    )
    parser.add_argument(
        "--animation-root",
        default="",
        help="Relative root containing dolphin-style meta.txt files.",
    )
    parser.add_argument("--tools-dir", required=True, help="Directory containing bdfconv.")
    parser.add_argument("--bdf", required=True, help="BDF font file to compile.")
    parser.add_argument("--work-dir", required=True, help="Directory for intermediate files.")
    parser.add_argument("--out-u8f", required=True, help="Final .u8f output path.")
    parser.add_argument("--out-map", help="Optional .map output path.")
    parser.add_argument("--out-c", help="Optional intermediate C output path.")
    parser.add_argument("--out-chars", help="Optional chars report output path.")
    parser.add_argument(
        "--font-name",
        default="primary_zh",
        help="Symbol/output base name used for bdfconv.",
    )
    return parser.parse_args()


def collect_chars_from_strings(strings_path: Path):
    data = json.loads(strings_path.read_text(encoding="utf-8"))
    chars = set()
    for row in data:
        text = row.get("text", "")
        for ch in text:
            if ord(ch) > 127:
                chars.add(ch)
    return chars


def iter_source_files(repo_root: Path, source_roots):
    for scan_root in source_roots:
        root = repo_root / scan_root
        if not root.is_dir():
            continue
        for pattern in ("*.c", "*.h"):
            yield from root.rglob(pattern)


def decode_c_string_literal(literal: str):
    escape_map = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "\\": "\\",
        '"': '"',
        "'": "'",
        "0": "\0",
    }
    result = []
    i = 0
    while i < len(literal):
        ch = literal[i]
        if ch == "\\" and i + 1 < len(literal):
            nxt = literal[i + 1]
            result.append(escape_map.get(nxt, nxt))
            i += 2
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def collect_chars_from_source_literals(repo_root: Path, source_roots):
    chars = set()
    for source_file in iter_source_files(repo_root, source_roots):
        contents = source_file.read_text(encoding="utf-8", errors="ignore")
        for match in STRING_LITERAL_RE.finditer(contents):
            literal = decode_c_string_literal(match.group(1))
            for ch in literal:
                if ord(ch) > 127:
                    chars.add(ch)
    return chars


def collect_chars_from_animation_text(repo_root: Path, animation_root: Path):
    chars = set()
    root = repo_root / animation_root
    if not root.is_dir():
        return chars

    for meta_file in root.rglob("meta.txt"):
        contents = meta_file.read_text(encoding="utf-8", errors="ignore")
        for line in contents.splitlines():
            if not line.startswith("Text:"):
                continue
            text = line[5:].strip().replace("\\n", "\n")
            for ch in text:
                if ord(ch) > 127:
                    chars.add(ch)
    return chars


def write_map(chars, path: Path):
    lines = ["32-128,"]
    for codepoint in sorted(ord(ch) for ch in chars):
        lines.append(f"${codepoint:04X},")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_chars_report(chars, path: Path):
    sorted_chars = sorted(chars, key=ord)
    lines = [f"count={len(sorted_chars)}", "".join(sorted_chars), ""]
    lines.extend(f"U+{ord(ch):04X} {ch}" for ch in sorted_chars)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def c_to_u8f(c_path: Path, u8f_path: Path):
    code = c_path.read_bytes().split(b' U8G2_FONT_SECTION("')[1].split(b'") =')[1].strip()
    font = b""
    for line in code.splitlines():
        if line.count(b'"') == 2:
            font += (
                line[line.find(b'"') + 1 : line.rfind(b'"')]
                .decode("unicode_escape")
                .encode("latin_1")
            )
    font += b"\0"
    u8f_path.parent.mkdir(parents=True, exist_ok=True)
    u8f_path.write_bytes(font)


def sanitize_symbol_name(name: str):
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def resolve_source_roots(args):
    if args.source_dir:
        return tuple(Path(item) for item in args.source_dir)
    return DEFAULT_SOURCE_ROOTS


def resolve_animation_root(args):
    if args.animation_root:
        return Path(args.animation_root)
    return DEFAULT_ANIMATION_ROOT


def main():
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    work_dir = Path(args.work_dir).resolve()
    out_u8f = Path(args.out_u8f).resolve()
    out_map = Path(args.out_map).resolve() if args.out_map else work_dir / f"{args.font_name}.map"
    out_c = Path(args.out_c).resolve() if args.out_c else work_dir / f"{args.font_name}.c"
    out_chars = Path(args.out_chars).resolve() if args.out_chars else work_dir / f"{args.font_name}_chars.txt"
    tools_dir = Path(args.tools_dir).resolve()
    bdf = Path(args.bdf).resolve()
    bdfconv = tools_dir / "bdfconv"
    source_roots = resolve_source_roots(args)
    animation_root = resolve_animation_root(args)

    work_dir.mkdir(parents=True, exist_ok=True)
    out_u8f.parent.mkdir(parents=True, exist_ok=True)

    if not bdfconv.is_file():
        raise FileNotFoundError(f"bdfconv not found: {bdfconv}")
    if not os.access(bdfconv, os.X_OK):
        bdfconv.chmod(bdfconv.stat().st_mode | 0o111)
    if not bdf.is_file():
        raise FileNotFoundError(f"BDF not found: {bdf}")

    chars = set()
    for strings_file in args.strings:
        chars.update(collect_chars_from_strings((repo_root / strings_file).resolve()))
    chars.update(collect_chars_from_source_literals(repo_root, source_roots))
    chars.update(collect_chars_from_animation_text(repo_root, animation_root))

    write_chars_report(chars, out_chars)
    write_map(chars, out_map)
    subprocess.run(
        [
            str(bdfconv),
            str(bdf),
            "-b",
            "0",
            "-f",
            "1",
            "-M",
            str(out_map),
            "-n",
            sanitize_symbol_name(args.font_name),
            "-o",
            str(out_c),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    c_to_u8f(out_c, out_u8f)


if __name__ == "__main__":
    main()
