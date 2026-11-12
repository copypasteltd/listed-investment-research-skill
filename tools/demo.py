#!/usr/bin/env python3
"""Create an explicitly synthetic offline research run; no network calls or real securities."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'ai-investment-research'

def load_research():
    spec = importlib.util.spec_from_file_location('air_demo_research', SKILL / 'scripts' / 'research.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='new absolute directory; existing data is never replaced')
    parser.add_argument('--pdf', action='store_true', help='also run the optional offline PDF publisher')
    parser.add_argument('--font-body', help='local TTF/TTC body font for PDF')
    parser.add_argument('--font-head', help='local TTF/TTC heading font for PDF')
    args = parser.parse_args()
    run = Path(args.output)
    if not run.is_absolute() or run.exists():
        parser.error('--output must be a new absolute directory')
    core = load_research()
    core.init_run(argparse.Namespace(output=str(run), topic='SYNTHETIC DEMO / 合成示例', market='GLOBAL',
        as_of='2025-01-02', mode='company', horizon='synthetic 12-month scenario',
        format='md,html,pdf' if args.pdf else 'md,html', company=['DEMO — not a listed security']))
    synthetic = {
        'notice': 'SYNTHETIC DATA ONLY. No real issuer, quote, forecast, or financial claim.',
        'unit': 'synthetic million units',
        'years': ['Y1', 'Y2', 'Y3'], 'revenue': [100, 120, 135], 'cfo': [8, 11, 13], 'capex': [5, 6, 7]}
    dump(run / '01_sources/raw/synthetic.json', synthetic)
    source = dict(id='DEMO_SOURCE', title='Explicitly fabricated offline fixture', publisher='Demo generator',
        url='https://example.invalid/synthetic-fixture', published_at='2025-01-01', retrieved_at='2025-01-02',
        source_type='synthetic_fixture', period='fictional Y1–Y3', local_path='01_sources/raw/synthetic.json', market='GLOBAL')
    dump(run / 'sources.json', [source])
    dump(run / 'claims.json', [dict(id='DEMO_C1', text='Synthetic Y3 cash proxy is 6 units; this is not issuer research.',
        kind='calculation', source_ids=['DEMO_SOURCE'], as_of='2025-01-02', confidence='high',
        calculation='synthetic CFO13 - synthetic capex7 = 6; all numbers fabricated for offline validation')])
    dump(run / 'forecasts.json', [dict(id='DEMO_F1', subject='SYNTHETIC ONLY', forecast_type='fundamental',
        as_of='2025-01-02', horizon='fictional 12 months', baseline='fictional Y3 revenue135',
        leading_indicators=['synthetic revenue and cash conversion'], validation_date='2026-01-02',
        status='unverifiable', source_ids=['DEMO_SOURCE'], scenarios=[dict(name='illustration',
            trigger='synthetic revenue grows', invalidation='synthetic cash conversion declines')],
        review_notes='A parser fixture, never a real forecast or accuracy observation.')])
    artifact = run / '02_analysis/companies/synthetic.md'
    artifact.write_text('# Synthetic analysis\n\nAll values are fabricated. No investment conclusion.\n', encoding='utf-8')
    meta = json.loads((run / 'research.json').read_text(encoding='utf-8'))
    meta['modules']['company'] = dict(status='complete', reason='Complete only as an offline software fixture.',
                                      artifact='02_analysis/companies/synthetic.md')
    for key in ('industry', 'event', 'technical', 'macro'):
        meta['modules'][key] = dict(status='skipped', reason='Out of scope for the synthetic company-mode fixture.', artifact='')
    meta['status'] = 'limited'
    dump(run / 'research.json', meta)
    report = ('# SYNTHETIC OFFLINE DEMO / 合成离线示例\n\n'
        'This is fabricated data for demonstrating the evidence and publishing pipeline.\n\n'
        '| Fictional period | Revenue | CFO | Capex |\n|---|---:|---:|---:|\n'
        '| Y1 | 100 | 8 | 5 |\n| Y2 | 120 | 11 | 6 |\n| Y3 | 135 | 13 | 7 |\n\n'
        'Synthetic cash proxy: 13 - 7 = 6. [DEMO_SOURCE]\n\n'
        '## Limitations / 资料缺口\n\n'
        'This is not financial research. All numbers and dates are fixture values. '
        'industry, event, technical, macro are skipped; company is complete only as a software example. '
        'No network request, live quote, accuracy backtest, or visual review is performed.\n\n'
        '## Sources\n\n[DEMO_SOURCE] Fabricated offline fixture: https://example.invalid/synthetic-fixture\n')
    (run / '04_deliverables/report.md').write_text(report, encoding='utf-8')
    result = core.check_run(run, strict=True)
    dump(run / '99_internal/check.json', result)
    if not result['valid']:
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 2
    exported = core.render_run(run, 'md,html')
    dump(run / '99_internal/core-export.json', exported)
    if args.pdf:
        # A small deterministic graph is drawn locally; it is visibly labeled synthetic.
        from PIL import Image, ImageDraw
        graph = Image.new('RGB', (1200, 400), 'white'); draw = ImageDraw.Draw(graph)
        draw.text((40, 20), 'SYNTHETIC FIXTURE - NOT FINANCIAL DATA', fill='black')
        for index, value in enumerate(synthetic['revenue']):
            x = 180 + index * 300
            draw.rectangle((x, 345 - value * 2, x + 130, 345), fill='#244B69')
            draw.text((x + 30, 355), f'Y{index + 1}: {value}', fill='black')
        chart = run / '03_models/synthetic-chart.png'; graph.save(chart)
        content = dict(title='SYNTHETIC OFFLINE DEMO', subtitle='Publishing pipeline fixture / 合成示例',
            ticker='DEMO — NOT A SECURITY', as_of='2025-01-02',
            quote_note='No real quote. Every number is synthetic.', judgment='No investment conclusion.',
            filename='synthetic-demo.pdf', cover_metrics=[dict(value='135', label='Synthetic Y3 revenue')], pages=[
                dict(section='SYNTHETIC', title='Fabricated values and explicit evidence', blocks=[
                    dict(type='chart', path='03_models/synthetic-chart.png', title='Synthetic revenue, arbitrary units', source='DEMO_SOURCE; fabricated locally'),
                    dict(type='p', text='All values are synthetic. This page demonstrates charts, Chinese text 中文, tables and source references.'),
                    dict(type='table', headers=['Period', 'Revenue', 'Cash proxy'], rows=[['Y3', '135', '6']]),
                    dict(type='note', text='No live data or forecast. Structural checks do not establish financial truth.')]),
                dict(section='Limitations', title='Limitations / 资料缺口', blocks=[
                    dict(type='p', text='All five modules here are fixture behavior, not real coverage. No vision model reviewed this PDF.'),
                    dict(type='source', id='DEMO_SOURCE', title=source['title'], publisher=source['publisher'], url=source['url'], published_at=source['published_at'], period=source['period'])])])
        dump(run / '99_internal/content.json', content)
        command = [sys.executable, '-B', str(SKILL / 'scripts/publisher.py'), '--run', str(run), '--content', '99_internal/content.json']
        for key in ('font_body', 'font_head'):
            value = getattr(args, key)
            if value: command.extend(['--' + key.replace('_', '-'), value])
        completed = subprocess.run(command, check=False, capture_output=True, text=True, encoding='utf-8')
        (run / '99_internal/publisher-output.txt').write_text(completed.stdout + completed.stderr, encoding='utf-8')
        if completed.returncode: print(completed.stderr, file=sys.stderr); return completed.returncode
        manifest = json.loads((run / '99_internal/report_manifest.json').read_text(encoding='utf-8'))
        if manifest['status'] == 'fail': return 2
    print(json.dumps(dict(status='synthetic-demo-created', output=str(run), strict_valid=result['valid'],
        warnings=result['warnings'], pdf=args.pdf, live_data=False), ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
