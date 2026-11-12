#!/usr/bin/env python3
"""Install this skill into an explicit parent skills directory, without replacement."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

NAME = 'ai-investment-research'
IGNORED = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}


def ignored(name):
    return name in IGNORED or name.endswith(('.pyc', '.pyo'))


def linked(path):
    # FILE_ATTRIBUTE_REPARSE_POINT also detects junctions on Python 3.10/3.11.
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def fingerprint(root):
    result = {}
    for current, directories, files in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if not ignored(name)]
        for name in directories + files:
            path = Path(current) / name
            if linked(path):
                raise ValueError(f'Unexpected nested link; inspect manually: {path}')
        for name in files:
            if not ignored(name):
                path = Path(current) / name
                result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def install(target, mode='copy', dry_run=False, source=None):
    source = Path(source or Path(__file__).resolve().parent.parent).resolve()
    if not (source / 'SKILL.md').is_file():
        raise ValueError(f'SKILL.md missing in source: {source}')
    parent = Path(target).expanduser().absolute()
    destination = parent / NAME
    result = {'name': NAME, 'source': str(source), 'destination': str(destination),
              'mode': mode, 'dry_run': dry_run}
    if mode not in ('copy', 'link'):
        raise ValueError('mode must be copy or link')
    if destination.resolve() == source:
        return dict(result, status='already-source')
    if os.path.lexists(destination):
        if linked(destination) or not destination.is_dir():
            raise ValueError(f'Existing destination differs; refusing to replace or redirect: {destination}')
        if fingerprint(source) == fingerprint(destination):
            return dict(result, status='already-installed')
        raise ValueError(f'Existing destination differs; refusing to overwrite: {destination}')
    if destination.resolve().is_relative_to(source) or source.is_relative_to(destination.resolve()):
        raise ValueError('Install destination must not contain or be inside the source skill')
    if parent.exists() and not parent.is_dir():
        raise ValueError(f'Target must be a parent skills directory: {parent}')
    if dry_run:
        return dict(result, status='would-install')
    parent.mkdir(parents=True, exist_ok=True)
    if mode == 'copy':
        shutil.copytree(source, destination,
                        ignore=lambda folder, names: [name for name in names if ignored(name)])
    else:
        try:
            destination.symlink_to(source, target_is_directory=True)
        except OSError as exc:
            if os.name != 'nt':
                raise ValueError(f'Cannot create link: {exc}. Use --mode copy.') from exc
            completed = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J',
                                        str(destination), str(source)], capture_output=True, timeout=15)
            if completed.returncode:
                raise ValueError('Cannot create Windows link/junction. Use --mode copy or enable '
                                 'Developer Mode. No existing installation was changed.') from exc
    return dict(result, status='installed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True, help='parent skills directory; no host-specific default')
    parser.add_argument('--mode', choices=('copy', 'link'), default='copy')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(install(args.target, args.mode, args.dry_run), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f'install error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
