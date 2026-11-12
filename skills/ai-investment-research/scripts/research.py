#!/usr/bin/env python3
"""Python 3.10+ stdlib research workspace, structural checks and document exports.

This tool never fetches facts or certifies that supplied evidence is true.
All paths stored in a run are relative to that run. No third-party imports.
"""
from __future__ import annotations

import argparse
import base64
import struct
from datetime import date, datetime, timezone
import hashlib
import html
import importlib.util
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
import xml.etree.ElementTree as ET

MODULES = ('industry', 'company', 'event', 'technical', 'macro')
LABELS = dict(zip(MODULES, ('行业', '公司', '事件', '周线', '宏观')))
FORMATS = {'md', 'html', 'docx', 'pdf'}
DIRECTORIES = ('00_brief', '01_sources/raw', '02_analysis/industry',
               '02_analysis/companies', '02_analysis/events', '02_analysis/technical',
               '02_analysis/macro', '03_models', '04_deliverables', '99_internal')
DEFAULT_HORIZON = '3-5年行业/1-3个月公司路径/周线条件判断'


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def inside(run, value):
    """Reject traversal, Windows absolute paths on any OS, and escaping symlinks."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError('路径必须是非空相对路径')
    parts = value.replace('\\', '/').split('/')
    win = PureWindowsPath(value)
    if Path(value).is_absolute() or win.drive or win.root or '..' in parts:
        raise ValueError(f'不安全路径: {value}')
    target = (run / Path(*parts)).resolve()
    if not target.is_relative_to(run.resolve()):
        raise ValueError(f'路径解析后逃出研究目录: {value}')
    return target


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('要求 YYYY-MM-DD')
    return date.fromisoformat(value)


def source_date(value):
    if not isinstance(value, str):
        raise ValueError('要求 ISO 日期或时间')
    if len(value) == 10:
        return parse_date(value)
    if not re.match(r'^\d{4}-\d{2}-\d{2}T', value):
        raise ValueError('要求 ISO 日期或时间')
    return datetime.fromisoformat(value.replace('Z', '+00:00')).date()


def formats(value):
    items = list(dict.fromkeys(value.split(',')))
    if not items or any(item not in FORMATS for item in items):
        raise ValueError('format 仅支持 md,html,docx,pdf（逗号分隔）')
    return items


def valid_metadata(meta, run):
    """Validate the run contract only; draft evidence and reports may be absent."""
    if not isinstance(meta, dict) or meta.get('schema_version') != '1.0':
        return False
    strings = ('run_id', 'topic', 'market', 'as_of', 'mode', 'horizon', 'report_path', 'status', 'created_at')
    if any(not isinstance(meta.get(k), str) or not meta[k].strip() for k in strings):
        return False
    if (meta['market'] not in ('CN', 'HK', 'US', 'GLOBAL')
            or meta['mode'] not in ('full', *MODULES, 'update')
            or meta['status'] not in ('draft', 'complete', 'limited')):
        return False
    if (not isinstance(meta.get('formats'), list) or not meta['formats']
            or any(not isinstance(x, str) or x not in FORMATS for x in meta['formats'])
            or not isinstance(meta.get('companies'), list)
            or any(not isinstance(x, str) or not x.strip() for x in meta['companies'])):
        return False
    modules = meta.get('modules')
    if not isinstance(modules, dict):
        return False
    for name in MODULES:
        module = modules.get(name)
        if (not isinstance(module, dict) or module.get('status') not in ('pending', 'complete', 'limited', 'skipped')
                or any(not isinstance(module.get(k), str) for k in ('reason', 'artifact'))):
            return False
    try:
        parse_date(meta['as_of']); source_date(meta['created_at'])
        inside(run, meta['report_path'])
        for module in modules.values():
            if not isinstance(module, dict):
                return False
            if module.get('artifact'):
                inside(run, module['artifact'])
    except (ValueError, TypeError, OSError, RuntimeError):
        return False
    return True


def init_run(args):
    run = Path(args.output)
    if not run.is_absolute():
        raise ValueError('--output 必须是绝对路径')
    parse_date(args.as_of)
    requested = formats(args.format)
    if run.exists():
        try:
            prior = json.loads(inside(run, 'research.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            raise ValueError('目标已存在且不是研究目录；拒绝写入') from None
        if not valid_metadata(prior, run):
            raise ValueError('目标已存在且不是研究目录；拒绝写入')
        return {'action': 'resume', 'run': str(run), 'run_id': prior['run_id'], 'written': []}
    if run.is_symlink():
        raise ValueError('目标不能是符号链接')
    run.mkdir(parents=True)  # Existing research directories returned above without any writes.
    for folder in DIRECTORIES:
        (run / folder).mkdir(parents=True, exist_ok=True)
    meta = dict(schema_version='1.0', run_id=str(uuid.uuid4()), topic=args.topic,
                market=args.market, as_of=args.as_of, mode=args.mode, horizon=args.horizon,
                formats=requested, companies=args.company or [],
                modules={name: {'status': 'pending', 'reason': '', 'artifact': ''} for name in MODULES},
                report_path='04_deliverables/report.md', status='draft',
                created_at=datetime.now(timezone.utc).isoformat())
    dump(run / 'research.json', meta)
    for name in ('sources', 'claims', 'forecasts'):
        dump(run / f'{name}.json', [])
    (run / '00_brief/brief.md').write_text(
        '# 研究对象与初始假设\n\n```json\n' + json.dumps(meta, ensure_ascii=False, indent=2)
        + '\n```\n\n尚未获取来源、建立事实或形成预测。研究对象和期限来自任务输入，'
          '不是已经验证的结论。后续假设须在 claims 中标记 assumption，预测须登记验证日期与失效条件。\n',
        encoding='utf-8')
    return {'action': 'created', 'run': str(run), 'run_id': meta['run_id']}


def check_run(run, strict=False):
    run = Path(run).resolve()
    issues = []

    def issue(code, location, message, soft=False):
        issues.append(dict(severity='warning' if soft and not strict else 'error',
                           code=code, location=location, message=message))

    def read_json(name, expected):
        try:
            data = json.loads(inside(run, name).read_text(encoding='utf-8'))
            if not isinstance(data, expected):
                raise ValueError(f'根值必须为 {expected.__name__}')
            return data
        except (OSError, ValueError) as exc:
            issue('json', name, str(exc))
            return expected()

    def path_check(value, location):
        try:
            return inside(run, value)
        except (ValueError, OSError, RuntimeError) as exc:
            issue('path', location, str(exc))

    def required(item, fields, location, soft=False):
        for field in fields.split():
            if field not in item or item[field] is None or item[field] == '':
                issue('required', f'{location}.{field}', '缺少必填字段', soft)

    def dated(value, location, source=False, soft=False):
        try:
            return source_date(value) if source else parse_date(value)
        except (ValueError, TypeError, OverflowError):
            issue('date', location, '无效 ISO 日期/时间' if source else '无效 YYYY-MM-DD 日期', soft)

    meta = read_json('research.json', dict)
    required(meta, 'schema_version run_id topic market as_of mode horizon formats companies modules report_path status created_at', 'research')
    if meta.get('schema_version') != '1.0':
        issue('schema', 'research.schema_version', '仅支持 1.0')
    for key, allowed in (('market', ('CN', 'HK', 'US', 'GLOBAL')),
                         ('mode', ('full', *MODULES, 'update')),
                         ('status', ('draft', 'complete', 'limited'))):
        if meta.get(key) not in allowed:
            issue('enum', f'research.{key}', '字段值不在契约范围内')
    for field in ('run_id', 'topic', 'horizon'):
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            issue('type', 'research.' + field, '必须是非空字符串')
    if not isinstance(meta.get('companies'), list) or any(not isinstance(x, str) or not x.strip() for x in meta.get('companies', [])):
        issue('type', 'research.companies', '必须是 ticker/name 字符串数组')
    if not isinstance(meta.get('formats'), list) or not meta.get('formats') or any(not isinstance(x, str) or x not in FORMATS for x in meta.get('formats', [])):
        issue('type', 'research.formats', '必须是合法格式数组')
    dated(meta.get('as_of'), 'research.as_of')
    dated(meta.get('created_at'), 'research.created_at', source=True)
    records = {name: read_json(f'{name}.json', list) for name in ('sources', 'claims', 'forecasts')}
    ids = {}
    for name, rows in records.items():
        ids[name] = set()
        for i, item in enumerate(rows):
            loc = f'{name}[{i}]'
            if not isinstance(item, dict):
                issue('type', loc, '条目必须为对象')
                continue
            identifier = item.get('id')
            if not isinstance(identifier, str) or not identifier.strip():
                issue('id', loc, 'id 必须为非空字符串')
            elif identifier in ids[name]:
                issue('duplicate_id', loc, f'重复 id: {identifier}')
            else:
                ids[name].add(identifier)
    for name, rows in records.items():
        for i, item in enumerate(rows):
            if not isinstance(item, dict):
                continue
            loc = f'{name}[{i}]'
            if name == 'sources':
                required(item, 'id title publisher url published_at retrieved_at source_type period', loc)
                for field in ('title', 'publisher', 'url', 'published_at', 'retrieved_at', 'source_type', 'period'):
                    if not isinstance(item.get(field), str) or not item[field].strip():
                        issue('type', loc + '.' + field, '必须是非空字符串')
                published = None
                if item.get('published_at') == 'unknown':
                    issues.append(dict(severity='warning', code='unknown_publication', location=loc, message='发布日期明确未知，不能确认资料在截止日已知'))
                else:
                    published = dated(item.get('published_at'), loc + '.published_at', True)
                retrieved = dated(item.get('retrieved_at'), loc + '.retrieved_at', True)
                if retrieved and retrieved > date.today():
                    issue('future_retrieval', loc, '取数日期晚于当前日期')
                if published and retrieved and published > retrieved:
                    issue('source_chronology', loc, '发布日期晚于取数日期')
                url = item.get('url')
                if isinstance(url, str) and url.startswith('local:'):
                    local = path_check(item.get('local_path'), loc + '.local_path')
                    if local and not local.is_file():
                        issue('local_source_missing', loc, '本地来源文件不存在')
                    issues.append(dict(severity='warning', code='local_source', location=loc, message='本地用户资料；未核验网络来源'))
                elif not isinstance(url, str) or not re.match(r'^https?://[^\s/]+', url, re.I):
                    issue('url', loc + '.url', '来源需提供 http(s) URL 或 local: 与存在的 local_path')
                if item.get('local_path') is not None:
                    path_check(item['local_path'], loc + '.local_path')
                if item.get('market') is not None and item['market'] not in ('CN', 'HK', 'US', 'GLOBAL'):
                    issue('enum', loc + '.market', '无效市场')
                continue
            refs = item.get('source_ids')
            if not isinstance(refs, list) or any(not isinstance(x, str) for x in refs):
                issue('type', loc + '.source_ids', 'source_ids 必须是字符串数组')
                refs = []
            for ref in refs:
                if ref not in ids['sources']:
                    issue('source_reference', loc, f'不存在来源: {ref}')
                else:
                    source = next(s for s in records['sources'] if isinstance(s, dict) and s.get('id') == ref)
                    try:
                        if source_date(source.get('published_at')) > parse_date(item.get('as_of')):
                            issue('lookahead', loc, f'来源 {ref} 发布日期晚于该结论/预测 as_of，存在前视资料', True)
                    except (TypeError, ValueError):
                        pass  # Invalid or explicitly unknown dates are diagnosed on their own fields.
            if name == 'claims':
                required(item, 'id text kind source_ids as_of confidence', loc)
                dated(item.get('as_of'), loc + '.as_of')
                if not isinstance(item.get('text'), str) or not item['text'].strip():
                    issue('type', loc + '.text', '必须是非空字符串')
                if 'calculation' in item and not isinstance(item['calculation'], str):
                    issue('type', loc + '.calculation', '必须是字符串')
                if item.get('kind') not in ('fact', 'calculation', 'assumption', 'inference', 'scenario'):
                    issue('enum', loc + '.kind', '无效 claim kind')
                if item.get('confidence') not in ('high', 'medium', 'low'):
                    issue('enum', loc + '.confidence', '无效 confidence')
                if item.get('kind') in ('fact', 'calculation') and not refs:
                    issue('evidence', loc, '事实或计算缺少来源；结构检查不能证明事实真实', True)
                if item.get('kind') == 'calculation' and not isinstance(item.get('calculation'), str):
                    issue('calculation', loc, '计算需提供 calculation 公式/方法字符串', True)
            else:
                required(item, 'id subject forecast_type horizon leading_indicators status source_ids', loc)
                required(item, 'baseline as_of validation_date', loc, True)
                as_of = dated(item.get('as_of'), loc + '.as_of', soft=True)
                validation = dated(item.get('validation_date'), loc + '.validation_date', soft=True)
                if as_of and validation and validation < as_of:
                    issue('forecast_chronology', loc, '验证日期早于预测日期')
                if item.get('forecast_type') not in ('industry', 'fundamental', 'valuation', 'event', 'technical', 'macro'):
                    issue('enum', loc + '.forecast_type', '无效 forecast_type')
                if item.get('status') not in ('open', 'realized', 'failed', 'partial', 'unverifiable'):
                    issue('enum', loc + '.status', '无效预测状态')
                if not isinstance(item.get('leading_indicators'), list):
                    issue('type', loc + '.leading_indicators', '必须是数组')
                elif not item['leading_indicators']:
                    issue('leading_indicators', loc, '缺少先行验证指标', True)
                scenarios = item.get('scenarios', [])
                if not isinstance(scenarios, list):
                    issue('type', loc + '.scenarios', '必须是情景对象数组')
                    scenarios = []
                probabilities, probability_present = [], False
                for j, scenario in enumerate(scenarios):
                    sloc = f'{loc}.scenarios[{j}]'
                    if not isinstance(scenario, dict):
                        issue('type', sloc, '必须是情景对象')
                        continue
                    required(scenario, 'name trigger', sloc)
                    required(scenario, 'invalidation', sloc, True)
                    for field in ('name', 'trigger', 'invalidation'):
                        if field in scenario and (not isinstance(scenario[field], str) or not scenario[field].strip()):
                            issue('type', sloc + '.' + field, '必须是非空字符串', field == 'invalidation')
                    if 'probability' in scenario:
                        probability_present = True
                        p = scenario['probability']
                        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
                            issue('probability', sloc, '概率必须为 0-1 有限数值')
                        else:
                            probabilities.append(p)
                if not scenarios:
                    issue('invalidation', loc, '预测缺少情景与明确失效条件', True)
                if probability_present and (len(probabilities) != len(scenarios) or not math.isclose(sum(probabilities), 1, abs_tol=1e-6)):
                    issue('probability_sum', loc, '概率序列不完整或合计不为 1')
                if item.get('forecast_type') == 'technical' and item.get('target') is not None:
                    issues.append(dict(severity='warning', code='technical_target', location=loc, message='技术目标仅是条件路径，不能作为估值或基本面价值证明'))
    report = path_check(meta.get('report_path'), 'research.report_path')
    body = ''
    if report:
        try:
            body = report.read_text(encoding='utf-8')
        except OSError:
            issue('report_missing', 'report', '报告正文尚未撰写', True)
        if not body.strip() and report.exists():
            issue('report_empty', 'report', '报告正文为空', True)
        if re.search(r'\{\{[^}]+\}\}|\bTODO\b', body):
            issue('placeholder', 'report', '发现明确的 {{...}} 或 TODO 占位符', True)
    modules = meta.get('modules')
    if not isinstance(modules, dict):
        issue('modules', 'research.modules', '必须为模块对象字典')
        modules = {}
    # Only text within a limitations section counts as disclosure.
    sections = re.findall(r'^#{1,6}\s+([^\n]+)\n(.*?)(?=^#{1,6}\s|\Z)', body, re.M | re.S)
    limitations = '\n'.join(text for title, text in sections if re.search(r'limitations|资料缺口|局限', title, re.I))
    for name in MODULES:
        module = modules.get(name)
        if not isinstance(module, dict) or module.get('status') not in ('pending', 'complete', 'limited', 'skipped'):
            issue('module_status', f'modules.{name}', '需 {status,reason,artifact} 对象及合法状态')
            continue
        required(module, 'status', f'modules.{name}')
        for key in ('reason', 'artifact'):
            if not isinstance(module.get(key), str):
                issue('module_schema', f'modules.{name}.{key}', '必须提供字符串')
        if module.get('artifact'):
            artifact = path_check(module['artifact'], f'modules.{name}.artifact')
            if artifact and not artifact.is_file():
                issue('artifact_missing', f'modules.{name}', '模块 artifact 不存在')
        if module['status'] == 'skipped' and not module.get('reason'):
            issues.append(dict(severity='warning', code='skip_reason', location=f'modules.{name}', message='跳过模块未说明原因'))
        if module['status'] == 'complete' and not module.get('artifact'):
            issue('artifact_required', f'modules.{name}', '已完成模块必须有可核验的 artifact', True)
        if meta.get('mode') == 'full' and module['status'] != 'complete':
            legitimately_skipped = module['status'] == 'skipped' and bool(module.get('reason', '').strip())
            if meta.get('status') == 'complete' and not legitimately_skipped:
                issue('false_completion', f'modules.{name}', 'full 尚有适用但未完成的模块，不能标记 complete')
            aliases = {'technical': '周线|技术', 'event': '事件|情景', 'macro': '宏观', 'industry': '行业', 'company': '公司'}
            if not re.search(rf'(?:\b{re.escape(name)}\b|{aliases[name]})[^\n]*(?:pending|limited|skipped|未完成|未获取|缺|不足|跳过|待|不适用)', limitations, re.I):
                issue('module_disclosure', f'modules.{name}', '未完成模块须在报告 limitations/资料缺口章节实际披露', True)
    errors = [x for x in issues if x['severity'] == 'error']
    warnings = [x for x in issues if x['severity'] == 'warning']
    return dict(valid=not errors, issues=issues, errors=errors, warnings=warnings,
                notice='仅检查结构、引用关系与披露；不证明数据或结论真实。')


IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
IMAGE_LIMIT = 10 * 1024 * 1024


def image_dimensions(data):
    """Read raster dimensions without executing decoders or loading third-party code."""
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 33 and data[12:16] == b'IHDR':
        width, height = struct.unpack('>II', data[16:24])
        mime, extension = 'image/png', 'png'
    elif data.startswith(b'\xff\xd8'):
        offset = 2
        while offset < len(data):
            if data[offset] != 255:
                raise ValueError('无效 JPEG 标记')
            while offset < len(data) and data[offset] == 255:
                offset += 1
            if offset >= len(data):
                break
            marker = data[offset]; offset += 1
            if marker in (0xd9, 0xda):
                break
            if marker in (0x01, *range(0xd0, 0xd9)):
                continue
            if offset + 2 > len(data):
                break
            length = int.from_bytes(data[offset:offset + 2], 'big')
            if length < 2 or offset + length > len(data):
                break
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf) and length >= 8:
                height, width = struct.unpack('>HH', data[offset + 3:offset + 7])
                mime, extension = 'image/jpeg', 'jpeg'
                break
            offset += length
        else:
            raise ValueError('JPEG 缺少尺寸')
        if 'width' not in locals():
            raise ValueError('JPEG 缺少有效尺寸')
    else:
        raise ValueError('仅支持有效 PNG/JPEG 图片')
    if width <= 0 or height <= 0:
        raise ValueError('图片尺寸必须为正数')
    return width, height, mime, extension


def prepare_images(content, run, source, result):
    def warning(code, message):
        item = dict(severity='warning', code=code, location='report', message=message)
        result['issues'].append(item); result['warnings'].append(item)

    def replace_inline(text):
        def replace(match):
            warning('image_inline_unsupported', f'不支持行内图片，保留 alt: {match[1]}')
            return match[1]
        return IMAGE.sub(replace, text)

    prepared = []
    for kind, value in content:
        match = IMAGE.fullmatch(value.strip()) if kind == 'paragraph' else None
        if match:
            alt, reference = match.groups()
            try:
                win = PureWindowsPath(reference)
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', reference) or reference.startswith('//'):
                    raise ValueError('拒绝外部 URL/数据 URI；不下载图片')
                if Path(reference).is_absolute() or win.drive or win.root:
                    raise ValueError('拒绝绝对图片路径')
                target = (source.parent / Path(*reference.replace('\\', '/').split('/'))).resolve()
                if not target.is_relative_to(run):
                    raise ValueError('图片路径解析后逃出研究目录（含符号链接）')
                if '_example' in target.relative_to(run).parts:
                    raise ValueError('拒绝把上游 _example 示例作为真实图表')
                if target.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
                    raise ValueError('仅支持 PNG/JPEG；SVG 不执行')
                with target.open('rb') as image:
                    data = image.read(IMAGE_LIMIT + 1)
                if len(data) > IMAGE_LIMIT:
                    raise ValueError('图片超过 10 MiB 大小限制')
                width, height, mime, extension = image_dimensions(data)
                prepared.append(('image', dict(alt=alt, data=data, width=width, height=height, mime=mime, extension=extension)))
            except (ValueError, OSError, RuntimeError) as exc:
                warning('image_rejected', f'图片未嵌入 [{alt}] ({reference}): {exc}')
                prepared.append(('paragraph', alt))
        elif kind == 'heading':
            prepared.append((kind, (value[0], replace_inline(value[1]))))
        elif kind == 'table':
            prepared.append((kind, [[replace_inline(cell) for cell in row] for row in value]))
        elif kind in ('ol', 'ul'):
            prepared.append((kind, [replace_inline(item) for item in value]))
        else:
            prepared.append((kind, replace_inline(value) if kind != 'code' else value))
    return prepared


def blocks(markdown):
    """Small Markdown block parser shared by HTML and OOXML exporters."""
    lines = markdown.splitlines()
    result, i = [], 0
    special = re.compile(r'^\s*(?:#{1,6}\s|```|[-*+]\s|\d+\.\s)')
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.lstrip().startswith('```'):
            code, i = [], i + 1
            while i < len(lines) and not lines[i].lstrip().startswith('```'):
                code.append(lines[i]); i += 1
            result.append(('code', '\n'.join(code))); i += 1
        elif IMAGE.fullmatch(line.strip()):
            result.append(('paragraph', line.strip())); i += 1
        elif re.match(r'^#{1,6}\s', line):
            m = re.match(r'^(#{1,6})\s+(.*)', line)
            result.append(('heading', (len(m[1]), m[2]))); i += 1
        elif i + 1 < len(lines) and '|' in line and re.fullmatch(r'\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*', lines[i + 1]):
            rows = [[x.strip() for x in line.strip().strip('|').split('|')]]
            i += 2
            while i < len(lines) and '|' in lines[i] and lines[i].strip():
                rows.append([x.strip() for x in lines[i].strip().strip('|').split('|')]); i += 1
            result.append(('table', rows))
        elif re.match(r'^\s*(?:[-*+]|\d+\.)\s+', line):
            ordered = bool(re.match(r'^\s*\d+\.', line))
            items = []
            while i < len(lines) and re.match(r'^\s*(?:\d+\.)\s+' if ordered else r'^\s*[-*+]\s+', lines[i]):
                items.append(re.sub(r'^\s*(?:[-*+]|\d+\.)\s+', '', lines[i])); i += 1
            result.append(('ol' if ordered else 'ul', items))
        else:
            para = [line]; i += 1
            while i < len(lines) and lines[i].strip() and not special.match(lines[i]) and not IMAGE.fullmatch(lines[i].strip()):
                if i + 1 < len(lines) and '|' in lines[i] and re.match(r'^\s*\|?\s*:?-{3,}', lines[i + 1]):
                    break
                para.append(lines[i]); i += 1
            result.append(('paragraph', ' '.join(para)))
    return result


def tokens(text):
    pattern = r'(\*\*[^*]+\*\*|\[[^\]]+\]\([^\s)]+\))'
    for part in re.split(pattern, text):
        if part.startswith('**') and part.endswith('**'):
            yield 'bold', part[2:-2], ''
        elif (match := re.fullmatch(r'\[([^\]]+)\]\(([^\s)]+)\)', part)):
            url = match[2]
            yield ('link', match[1], url) if re.match(r'^(?:https?://|mailto:|#)', url, re.I) else ('text', match[1] + ' (' + url + ')', '')
        else:
            yield 'text', part, ''


def inline_html(text):
    return ''.join('<strong>' + html.escape(t) + '</strong>' if kind == 'bold' else
                   '<a href="' + html.escape(url, quote=True) + '" rel="noreferrer">' + html.escape(t) + '</a>' if kind == 'link'
                   else html.escape(t) for kind, t, url in tokens(text))


def html_document(content, header):
    output, toc = [], []
    for kind, value in content:
        if kind == 'heading':
            level, text = value
            anchor = f'section-{len(toc) + 1}'
            toc.append(f'<li><a href="#{anchor}">{html.escape(text)}</a></li>')
            output.append(f'<h{level} id="{anchor}">{inline_html(text)}</h{level}>')
        elif kind == 'table':
            output.append('<table>' + ''.join('<tr>' + ''.join(f'<{"th" if i == 0 else "td"}>{inline_html(cell)}</{"th" if i == 0 else "td"}>' for cell in row) + '</tr>' for i, row in enumerate(value)) + '</table>')
        elif kind in ('ul', 'ol'):
            output.append(f'<{kind}>' + ''.join('<li>' + inline_html(t) + '</li>' for t in value) + f'</{kind}>')
        elif kind == 'image':
            uri = 'data:' + value['mime'] + ';base64,' + base64.b64encode(value['data']).decode('ascii')
            output.append('<figure><img src="' + uri + '" alt="' + html.escape(value['alt'], quote=True) + '"><figcaption>' + html.escape(value['alt']) + '</figcaption></figure>')
        elif kind == 'code':
            output.append('<pre><code>' + html.escape(value) + '</code></pre>')
        else:
            output.append('<p>' + inline_html(value) + '</p>')
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:; base-uri \'none\'">'
            '<title>研究报告</title><style>img{max-width:100%;height:auto}figure{margin:1em 0}body{font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif;max-width:1000px;margin:2em auto;padding:0 2em;line-height:1.7;color:#18212b}header{border-bottom:2px solid #29485b;padding:1em 0}table{border-collapse:collapse;width:100%;margin:1em 0}td,th{border:1px solid #ccd2d8;padding:.5em;text-align:left}th{background:#edf2f5}pre{white-space:pre-wrap;background:#f3f5f6;padding:1em;overflow-wrap:anywhere}a{color:#155a85;overflow-wrap:anywhere}@media print{body{margin:0;max-width:none;font-size:10pt}nav{break-after:page}h1,h2,h3{break-after:avoid}tr{break-inside:avoid}thead{display:table-header-group}}</style>'
            '<body><header>' + html.escape(header) + '</header><nav aria-label="目录"><h2>目录</h2><ol>' + ''.join(toc)
            + '</ol></nav><main>' + ''.join(output) + '</main></body></html>')


def write_docx(path, content, header):
    w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    r = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    relns = 'http://schemas.openxmlformats.org/package/2006/relationships'
    ET.register_namespace('w', w); ET.register_namespace('r', r)

    def el(tag, parent=None, **attrs):
        node = ET.Element(f'{{{w}}}{tag}', {f'{{{w}}}{k}': str(v) for k, v in attrs.items()})
        if parent is not None:
            parent.append(node)
        return node

    document = el('document'); body = el('body', document)
    relations = ET.Element('Relationships', xmlns=relns)
    ET.SubElement(relations, 'Relationship', Id='styles', Type=r + '/styles', Target='styles.xml')

    def paragraph(parent, text, style=None, literal=False):
        p = el('p', parent)
        if style:
            el('pStyle', el('pPr', p), val=style)
        for kind, text, url in ([('text', text, '')] if literal else tokens(text)):
            owner = p
            if kind == 'link':
                identifier = f'link{len(relations)}'
                ET.SubElement(relations, 'Relationship', Id=identifier, Type=r + '/hyperlink', Target=url, TargetMode='External')
                owner = el('hyperlink', p); owner.set(f'{{{r}}}id', identifier)
            run = el('r', owner)
            if kind in ('bold', 'link'):
                prop = el('rPr', run)
                el('b' if kind == 'bold' else 'color', prop, **({} if kind == 'bold' else {'val': '155A85'}))
            t = el('t', run); t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve'); t.text = text
        return p

    media = []

    def picture(value):
        number = len(media) + 1
        name = f'image{number}.{value["extension"]}'
        identifier = f'image{number}'
        media.append((name, value['data']))
        ET.SubElement(relations, 'Relationship', Id=identifier, Type=r + '/image', Target='media/' + name)
        # A4 usable width: 11906 - 2*1134 twips; 635 EMU per twip.
        cx = min(value['width'] * 9525, 9638 * 635)
        cy = max(1, round(cx * value['height'] / value['width']))
        wp = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
        a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
        pic = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
        drawing = el('drawing', el('r', el('p', body)))
        drawing.append(ET.fromstring(f'''<wp:inline xmlns:wp="{wp}" xmlns:a="{a}" xmlns:pic="{pic}" xmlns:r="{r}" distT="0" distB="0" distL="0" distR="0">
          <wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{number}" name="{name}"/>
          <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
          <a:graphic><a:graphicData uri="{pic}"><pic:pic><pic:nvPicPr><pic:cNvPr id="{number}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>
          <pic:blipFill><a:blip r:embed="{identifier}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
          <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
          </pic:pic></a:graphicData></a:graphic></wp:inline>'''))
        drawing.find(f'{{{wp}}}inline/{{{wp}}}docPr').set('descr', value['alt'])
        if value['alt']:
            paragraph(body, value['alt'])

    paragraph(body, header, 'Subtitle')
    for kind, value in content:
        if kind == 'heading':
            paragraph(body, value[1], f'Heading{value[0]}')
        elif kind == 'table':
            table = el('tbl', body); props = el('tblPr', table); borders = el('tblBorders', props)
            for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
                el(side, borders, val='single', sz='4', color='CCCCCC')
            grid = el('tblGrid', table)
            for _ in range(max(map(len, value))):
                el('gridCol', grid, w='2400')
            for row in value:
                tr = el('tr', table)
                for cell in row:
                    paragraph(el('tc', tr), cell)
        elif kind in ('ul', 'ol'):
            for i, text in enumerate(value, 1):
                paragraph(body, (f'{i}. ' if kind == 'ol' else '• ') + text)
        elif kind == 'image':
            picture(value)
        elif kind == 'code':
            for line in value.split('\n'):
                paragraph(body, line, 'Code', literal=True)
        else:
            paragraph(body, value)
    section = el('sectPr', body); el('pgSz', section, w='11906', h='16838')
    el('pgMar', section, top='1134', bottom='1134', left='1134', right='1134')
    styles = el('styles'); defaults = el('docDefaults', styles)
    props = el('rPr', el('rPrDefault', defaults))
    el('rFonts', props, ascii='Calibri', hAnsi='Calibri', eastAsia='Microsoft YaHei'); el('sz', props, val='22')
    for i in range(1, 7):
        style = el('style', styles, type='paragraph', styleId=f'Heading{i}')
        el('name', style, val=f'heading {i}'); el('outlineLvl', el('pPr', style), val=i - 1)
        prop = el('rPr', style); el('b', prop); el('sz', prop, val=max(24, 38 - i * 3))
    for name in ('Subtitle', 'Code'):
        el('name', el('style', styles, type='paragraph', styleId=name), val=name)
    types = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
             '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
    image_types = ''.join(f'<Default Extension="{ext}" ContentType="image/{ext}"/>' for ext in sorted({name.rsplit('.', 1)[1] for name, _ in media}))
    types = types.replace('</Types>', image_types + '</Types>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in media:
            archive.writestr('word/media/' + name, data)
        archive.writestr('[Content_Types].xml', types)
        archive.writestr('_rels/.rels', f'<Relationships xmlns="{relns}"><Relationship Id="office" Type="{r}/officeDocument" Target="word/document.xml"/></Relationships>')
        for name, element in (('word/document.xml', document), ('word/styles.xml', styles), ('word/_rels/document.xml.rels', relations)):
            archive.writestr(name, ET.tostring(element, encoding='utf-8', xml_declaration=True))


def browsers():
    found = []
    for name in ('msedge', 'chrome', 'google-chrome', 'chromium', 'chromium-browser'):
        if executable := shutil.which(name):
            found.append(executable)
    for env in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
        base = os.environ.get(env)
        if base:
            for suffix in ('Microsoft/Edge/Application/msedge.exe', 'Google/Chrome/Application/chrome.exe'):
                path = Path(base) / suffix
                if path.is_file():
                    found.append(str(path))
    return list(dict.fromkeys(found))


def render_run(run, requested=None):
    run = Path(run).resolve()
    result = check_run(run)
    if not result['valid']:
        return dict(valid=False, check=result, exports=[], message='检查存在错误，拒绝导出')
    meta = json.loads(inside(run, 'research.json').read_text(encoding='utf-8'))
    requested = formats(requested) if requested else meta['formats']
    source = inside(run, meta['report_path'])
    if not source.is_file() or not source.read_text(encoding='utf-8').strip():
        raise ValueError('请先撰写 report.md 正文再导出')
    text = source.read_text(encoding='utf-8')
    content = prepare_images(blocks(text), run, source, result)
    sources = json.loads(inside(run, 'sources.json').read_text(encoding='utf-8'))
    if sources:
        content.append(('heading', (2, '证据来源登记')))
        content.append(('ul', [f"{s['id']} {s['title']} — {s['publisher']}；发布 {s['published_at']}；取数 {s['retrieved_at']}；{s['url']}" for s in sources]))
        content.extend(('paragraph', f"[{s['id']} 来源链接]({s['url']})") for s in sources)
    header = f"研究状态: {meta['status']} | 数据截止: {meta['as_of']} | {meta['topic']} | 结构检查不证明真实性"
    # Validate every destination before writing any export, including internal symlinks.
    for relative in ['99_internal', '99_internal/check.json', '99_internal/delivery_manifest.json'] + [f'04_deliverables/report.{x}' for x in requested if x != 'md']:
        inside(run, relative)
    if 'pdf' in requested:
        inside(run, '04_deliverables/report.html')
    outputs = []
    for extension in ('md', 'html', 'docx'):
        if extension not in requested and not (extension == 'html' and 'pdf' in requested):
            continue
        destination = source if extension == 'md' else inside(run, f'04_deliverables/report.{extension}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if extension == 'html':
            destination.write_text(html_document(content, header), encoding='utf-8')
        elif extension == 'docx':
            write_docx(destination, content, header)
        outputs.append(dict(format=extension, status='available', path=str(destination.relative_to(run)), size=destination.stat().st_size,
                            sha256=hashlib.sha256(destination.read_bytes()).hexdigest()))
    if 'pdf' in requested:
        destination = inside(run, '04_deliverables/report.pdf')
        pdf = dict(format='pdf', status='unavailable', reason='未发现已安装的 Chrome/Edge/Chromium', size=0, magic_valid=False)
        for browser in browsers():
            try:
                with tempfile.TemporaryDirectory(prefix='pdf-', dir=destination.parent) as temporary:
                    temp = Path(temporary); generated = temp / 'report.pdf'
                    command = [browser, '--headless=new', '--no-pdf-header-footer', '--allow-file-access-from-files',
                               '--user-data-dir=' + str(temp / 'profile'), '--print-to-pdf=' + str(generated),
                               inside(run, '04_deliverables/report.html').as_uri()]
                    completed = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False)
                    size = generated.stat().st_size if generated.is_file() else 0
                    magic = generated.is_file() and generated.read_bytes().startswith(b'%PDF-')
                    if completed.returncode != 0 or size < 5 or not magic:
                        pdf['reason'] = f'浏览器打印失败或 PDF 无效（退出码 {completed.returncode}）'
                        continue
                    generated.replace(destination)
                    pdf = dict(format='pdf', status='available', path=str(destination.relative_to(run)), size=size,
                               magic_valid=True, sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
                    break
            except (OSError, subprocess.TimeoutExpired) as exc:
                pdf['reason'] = f'PDF 渲染失败: {type(exc).__name__}'
        outputs.append(pdf)
    manifest = dict(valid=all(x['status'] == 'available' for x in outputs), created_at=datetime.now(timezone.utc).isoformat(),
                    run_id=meta['run_id'], research_status=meta['status'], as_of=meta['as_of'], exports=outputs, check=result)
    internal = inside(run, '99_internal'); internal.mkdir(exist_ok=True)
    dump(inside(run, '99_internal/check.json'), result)
    dump(inside(run, '99_internal/delivery_manifest.json'), manifest)
    return manifest


def doctor(root):
    root = Path(root).resolve()
    optional = {}
    for name in ('requests', 'yfinance', 'docx', 'reportlab', 'fitz', 'PIL', 'matplotlib', 'pandas', 'numpy'):
        try:
            optional[name] = importlib.util.find_spec(name) is not None
        except (ValueError, ImportError, AttributeError):
            optional[name] = False
    return dict(python=sys.version.split()[0], python_supported=sys.version_info >= (3, 10),
                skill_root=str(root), files={p: (root / p).is_file() for p in ('SKILL.md', 'scripts/research.py', 'scripts/test_research.py')},
                optional_modules=optional, browsers=browsers(), notice='仅检测存在状态；不安装、不下载、不读取密钥。')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init')
    for name in ('output', 'topic', 'as-of'):
        init.add_argument('--' + name, required=True)
    init.add_argument('--market', choices=('CN', 'HK', 'US', 'GLOBAL'), required=True)
    init.add_argument('--mode', choices=('full', *MODULES, 'update'), required=True)
    init.add_argument('--format', default='md,html,pdf')
    init.add_argument('--horizon', default=DEFAULT_HORIZON)
    init.add_argument('--company', action='append')
    check = commands.add_parser('check'); check.add_argument('--run', required=True); check.add_argument('--strict', action='store_true')
    render = commands.add_parser('render'); render.add_argument('--run', required=True); render.add_argument('--formats')
    diagnostic = commands.add_parser('doctor'); diagnostic.add_argument('--skill-root', default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            result = init_run(args)
        elif args.command == 'check':
            result = check_run(args.run, args.strict)
        elif args.command == 'render':
            result = render_run(args.run, args.formats)
        else:
            result = doctor(args.skill_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get('valid', True) else 1
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
        print(json.dumps(dict(valid=False, errors=[str(exc)]), ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
