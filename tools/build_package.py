#!/usr/bin/env python3
"""Build a deterministic Skill-only ZIP and SHA-256 inventory after offline checks."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from verify_repo import verify
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/ai-investment-research'
VERSION='1.1.0'
EXCLUDED={'__pycache__','.pytest_cache','.git','.venv','venv','.validation','validation'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='dist');args=parser.parse_args()
    validation=verify()
    if not validation['valid']:
        print(json.dumps(validation,ensure_ascii=False,indent=2));return 1
    destination=Path(args.output).resolve();destination.mkdir(parents=True,exist_ok=True)
    if destination==SKILL or destination.is_relative_to(SKILL):parser.error('output cannot be inside the Skill directory')
    paths=sorted(p for p in SKILL.rglob('*') if p.is_file() and not any(x in EXCLUDED for x in p.relative_to(SKILL).parts) and p.suffix not in {'.pyc','.pyo'})
    archive=destination/f'ai-investment-research-v{VERSION}.zip';inventory=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as output:
        for p in paths:
            relative=(Path(SKILL.name)/p.relative_to(SKILL)).as_posix();raw=p.read_bytes()
            info=zipfile.ZipInfo(relative,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            output.writestr(info,raw);inventory.append(dict(path=relative,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    result=dict(version=VERSION,archive=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,file_count=len(inventory),files=inventory,
                scope='Installable Skill only. Excludes showcase reports, repository docs, research runs, environments, caches, credentials and proprietary fonts.')
    (destination/f'ai-investment-research-v{VERSION}.manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (destination/'SHA256SUMS').write_text(f'{result["sha256"]}  {archive.name}\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
