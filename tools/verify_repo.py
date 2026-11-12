#!/usr/bin/env python3
"""Offline repository checks: links, pinned vendor bytes, portable package and source hygiene."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/ai-investment-research'
EXCLUDED = {'.git', '__pycache__', '.venv', 'venv', 'dist', '.validation', '.pytest_cache'}

def files(root=ROOT):
    return sorted(p for p in root.rglob('*') if p.is_file() and not any(x in EXCLUDED for x in p.relative_to(ROOT).parts))

def verify():
    errors, warnings = [], []
    required = ['README.md', 'README.zh-CN.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'CHANGELOG.md',
        'CONTRIBUTING.md', 'docs/index.md', 'tools/demo.py', 'tools/build_package.py',
        'skills/ai-investment-research/SKILL.md', 'skills/ai-investment-research/scripts/install.py',
        'skills/ai-investment-research/scripts/publisher.py', 'showcase/manifest.json']
    for name in required:
        if not (ROOT / name).is_file(): errors.append('missing required file: ' + name)
    manifest = json.loads((SKILL / 'upstream-manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        path = SKILL / item['path']
        if not path.is_file(): errors.append('missing pinned vendor file: ' + item['path']); continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            errors.append('changed pinned vendor bytes: ' + item['path'])
    expected_vendor = {item['path'] for item in manifest['files']}
    actual_vendor = {p.relative_to(SKILL).as_posix() for p in files(SKILL / 'vendor')}
    if actual_vendor != expected_vendor:
        errors.append('vendor manifest path set mismatch: ' + repr(sorted(actual_vendor ^ expected_vendor)))
    settings = json.loads((SKILL / 'settings.json').read_text(encoding='utf-8'))
    if settings.get('default_project_root') is not None: errors.append('public default_project_root must be null')
    if settings.get('default_output_subdirectory') != 'reports': errors.append('portable default output must be reports')
    entry = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    if not re.search(r'^name:\s*ai-investment-research\s*$', entry, re.M): errors.append('skill name mismatch')
    if '1.1.0' not in entry: errors.append('skill version missing')
    # Check authored documentation. Vendor markdown is an immutable snapshot and may contain upstream-only links.
    checked_links = 0
    for path in files():
        rel = path.relative_to(ROOT).as_posix()
        if '/vendor/' in '/' + rel: continue
        if path.suffix.lower() == '.md':
            text = path.read_text(encoding='utf-8')
            text = re.sub(r'```.*?```', '', text, flags=re.S)
            for raw in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
                target = raw.strip()
                if target.startswith('<') and '>' in target: target = target[1:target.index('>')]
                else: target = target.split(' "', 1)[0]
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith('#'): continue
                decoded = unquote(parsed.path)
                if not decoded: continue
                checked_links += 1
                dest = (path.parent / decoded).resolve()
                if not dest.is_relative_to(ROOT) or not dest.exists():
                    errors.append(f'broken local link: {rel} -> {target}')
        if path.suffix.lower() in {'.pyc', '.pyo'} or path.name.startswith('.env') or path.name in {'id_rsa', 'id_ed25519'}:
            errors.append('disallowed generated/private file: ' + rel)
        if path.suffix.lower() in {'.md', '.py', '.ps1', '.json', '.yaml', '.yml', '.txt'}:
            text = path.read_text(encoding='utf-8-sig')
            patterns = {
                'machine-specific workspace': r'[A-Za-z]:[\\/]dev[\\/]sandbox[\\/]',
                'private user path': r'[A-Za-z]:[\\/]Users[\\/](?!Public[\\/])[^\s"\']+',
                'private network address': r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b',
                'private key material': r'-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----',
                'credential-shaped value': r'\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9]{30,})\b'}
            # This checker contains its own pattern definitions; they are not literal credentials.
            for label, pattern in patterns.items():
                if re.search(pattern, text): errors.append(f'{label}: {rel}')
    # Report snapshots are public copies; original documents and machine-local evidence are absent.
    showcase = ROOT / 'showcase/manifest.json'
    if showcase.is_file():
        value = json.loads(showcase.read_text(encoding='utf-8'))
        def verified_file(relative, expected):
            path = (ROOT / relative).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                errors.append('missing/escaping showcase file: ' + relative)
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                errors.append('showcase hash mismatch: ' + relative)
        verified_file(value['gallery']['local_file'], value['gallery']['sha256'])
        for report in value['reports']:
            verified_file(report['local_files']['pdf'], report['sha256'])
            verified_file(report['local_files']['detail_preview'], report['preview']['sha256'])
        if value.get('validation', {}).get('missing_links_pending_parent'):
            errors.append('unresolved showcase links')
    result = dict(valid=not errors, authored_local_links=checked_links, pinned_vendor_files=len(manifest['files']),
                  upstream_repositories=len(manifest['repositories']), errors=sorted(set(errors)), warnings=warnings,
                  notice='Offline packaging checks only; no financial truth, host discovery, visual quality or forecast-accuracy certification.')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--json-output')
    args = parser.parse_args(); result = verify()
    if args.json_output:
        output = Path(args.json_output); output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['valid'] else 1

if __name__ == '__main__': raise SystemExit(main())
