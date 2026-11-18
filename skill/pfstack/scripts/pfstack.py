#!/usr/bin/env python3
"""pfstack helper used by the pfstack skill (also usable as a CLI).

  pfstack.py init <dir> [--dry-run]   copy templates; never overwrite existing files
  pfstack.py check <dir>              report missing files, unfilled placeholders, drift
  pfstack.py update <dir>             write <file>.pfstack-new where upstream templates changed
"""
import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TEMPLATES = REPO / 'templates'
PLACEHOLDER = re.compile(r'<(?:project|[a-z][a-z /.,()-]{2,60})>')


def template_files():
    return sorted(p for p in TEMPLATES.rglob('*') if p.is_file())


def init(target: Path, dry: bool) -> int:
    for src in template_files():
        rel = src.relative_to(TEMPLATES)
        dst = target / rel
        if dst.exists():
            print(f'kept     {rel}')
            continue
        print(f'{"would add" if dry else "added"}  {rel}')
        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    claude = target / 'CLAUDE.md'
    if not claude.exists() or '@AGENTS.md' not in claude.read_text():
        print(f'{"would" if dry else "will"} need  CLAUDE.md importing @AGENTS.md (the skill adds it)')
    return 0


def check(target: Path) -> int:
    issues = []
    for src in template_files():
        rel = src.relative_to(TEMPLATES)
        if '_example' in rel.parts:
            continue
        dst = target / rel
        if not dst.exists():
            issues.append(f'missing        {rel}')
            continue
        if dst.suffix in ('.md', '.py', '.sh'):
            text = re.sub(r'`[^`]*`', '', dst.read_text(errors='ignore'))  # usage text in code spans is not a placeholder
            left = sorted(set(PLACEHOLDER.findall(text)))
            if left and rel.name in ('AGENTS.md', 'DESIGN.md'):
                issues.append(f'placeholders   {rel}: {", ".join(left[:6])}')
    claude = target / 'CLAUDE.md'
    if not claude.exists() or '@AGENTS.md' not in claude.read_text():
        issues.append('CLAUDE.md      does not import @AGENTS.md')
    if not (target / 'tool/test_baseline.txt').exists():
        issues.append('baseline       tool/test_baseline.txt missing (run tool/test_diff.sh --update)')
    iters = target / 'docs/iterations'
    if iters.is_dir():
        for it in sorted(p for p in iters.iterdir() if p.is_dir() and p.name != '_example'):
            rounds = [r for r in it.glob('round-*') if r.is_dir()]
            if rounds and not any((r / 'STATE.md').exists() for r in rounds):
                issues.append(f'no STATE.md    {it.relative_to(target)}')
    print('\n'.join(issues) if issues else 'pfstack: all set')
    return 1 if issues else 0


def update(target: Path) -> int:
    n = 0
    for src in template_files():
        rel = src.relative_to(TEMPLATES)
        dst = target / rel
        if dst.exists() and not filecmp.cmp(src, dst, shallow=False):
            new = dst.with_name(dst.name + '.pfstack-new')
            shutil.copy2(src, new)
            print(f'differs  {rel}  -> {new.relative_to(target)}')
            n += 1
    print(f'{n} file(s) differ from the templates' if n else 'templates and project agree')
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('cmd', choices=['init', 'check', 'update'])
    p.add_argument('dir', nargs='?', default='.')
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    target = Path(a.dir).resolve()
    if not target.is_dir():
        sys.exit(f'{target} is not a directory')
    return {'init': lambda: init(target, a.dry_run), 'check': lambda: check(target),
            'update': lambda: update(target)}[a.cmd]()


if __name__ == '__main__':
    sys.exit(main())
