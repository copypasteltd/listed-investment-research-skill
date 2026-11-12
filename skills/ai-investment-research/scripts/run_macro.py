#!/usr/bin/env python3
"""Run the pinned macro helper with an available local Python environment."""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',required=True)
    parser.add_argument('--days',type=int,default=600)
    parser.add_argument('--as-of',default=date.today().isoformat())
    parser.add_argument('--python',dest='interpreter')
    parser.add_argument('--probe',action='store_true',help='Check imports only; no financial-data requests')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    project_runtime=root.parent.parent/'runtime'/'ai-investment-research'/'venv'
    candidates=[project_runtime/'Scripts'/'python.exe',project_runtime/'bin'/'python']
    interpreter=Path(args.interpreter) if args.interpreter else next((p for p in candidates if p.is_file()),Path(sys.executable))
    if not interpreter.is_file():
        parser.error('Python executable not found')
    try:
        as_of=date.fromisoformat(args.as_of)
    except ValueError:
        parser.error('--as-of must be YYYY-MM-DD')
    if not args.probe and as_of!=date.today():
        print(json.dumps({'valid':False,'reason':'This upstream helper fetches current data and has no point-in-time input contract. Historical/future as-of requests require frozen dated inputs, not this live helper.'},ensure_ascii=False))
        return 2
    if args.days<30 or args.days>5000:
        parser.error('--days must be between 30 and 5000')
    if args.probe:
        # Inherited stdio avoids pipe restrictions and never reads credential values.
        code="import json,sys,requests,yfinance; print(json.dumps({'valid':True,'python':sys.executable,'requests':requests.__version__,'yfinance':yfinance.__version__}))"
        return subprocess.run([str(interpreter),'-B','-c',code],check=False,timeout=60).returncode
    output=Path(args.output_dir)
    if not output.is_absolute():
        parser.error('--output-dir must be absolute')
    source=root/'vendor'/'tradermonty'/'skills'/'macro-regime-detector'/'scripts'/'macro_regime_detector.py'
    if not source.is_file():
        parser.error('Pinned macro script is missing')
    command=[str(interpreter),'-B',str(source),'--output-dir',str(output),'--days',str(args.days)]
    return subprocess.run(command,cwd=str(root/'vendor'/'tradermonty'),check=False).returncode


if __name__=='__main__':
    raise SystemExit(main())
