"""Content-only, offline, sober business-report publisher. See publisher_contract.md."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import sys
from urllib.parse import urlsplit

import fitz
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, KeepTogether, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)

PAGE_W, PAGE_H = A4
LEFT = RIGHT = 48
TOP = 66
BOTTOM = 54
WIDTH = PAGE_W - LEFT - RIGHT
HEIGHT = PAGE_H - TOP - BOTTOM
BLACK = colors.black
LINE = colors.HexColor('#BFC3C7')
CJK = re.compile(r'[\u3400-\u9fff]')
TOKEN = re.compile(r'(\*\*.*?\*\*|https?://[^\s<>\u3000]+)', re.DOTALL)


def safe_url(value):
    value = str(value)
    parts = urlsplit(value)
    return value if parts.scheme.lower() in ('http', 'https') and parts.netloc else None


def inline(value, target='pdf'):
    """Treat all supplied text as text, allowing only bold and literal HTTP links."""
    value = str(value)
    out = []
    pos = 0
    for match in TOKEN.finditer(value):
        out.append(html.escape(value[pos:match.start()]))
        token = match.group()
        if token.startswith('**'):
            inner = inline(token[2:-2], target)
            out.append(('<font name="HeadCN">' + inner + '</font>') if target == 'pdf'
                       else ('<strong>' + inner + '</strong>'))
        else:
            # Sentence punctuation is not part of the hyperlink.
            tail = ''
            while token and token[-1] in '。，；、）】,;':
                tail = token[-1] + tail
                token = token[:-1]
            escaped = html.escape(token, quote=True)
            if safe_url(token):
                out.append(('<a href="' + escaped + '" color="black">' + escaped + '</a>')
                           if target == 'pdf' else ('<a href="' + escaped + '">' + escaped + '</a>'))
            else:
                out.append(escaped)
            out.append(html.escape(tail))
        pos = match.end()
    out.append(html.escape(value[pos:]))
    return ''.join(out).replace('\n', '<br/>')


def within(root, relative, label):
    rel = Path(relative)
    win = PureWindowsPath(relative)
    if rel.is_absolute() or win.drive or win.root or '..' in str(relative).replace('\\', '/').split('/'):
        raise ValueError(f'{label} must be relative to run: {relative}')
    path = (root / rel).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'{label} escapes run: {relative}')
    return path


def validate(run, content):
    for field in ('title', 'subtitle', 'ticker', 'as_of', 'quote_note', 'judgment', 'filename'):
        if field not in content or not isinstance(content[field], str):
            raise ValueError(f'content.{field} must be a string')
    name = content['filename']
    if not name or name in ('.', '..') or re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
        raise ValueError('filename must be a safe single filename/stem')
    if len(content.get('cover_metrics', [])) > 3:
        raise ValueError('cover_metrics allows at most 3 entries')
    for metric in content.get('cover_metrics', []):
        if not isinstance(metric, dict) or not all(k in metric for k in ('value', 'label')):
            raise ValueError('each cover metric requires value and label')
    pages = content.get('pages')
    if not isinstance(pages, list) or not pages:
        raise ValueError('pages must be a nonempty array')
    images = []
    for index, page in enumerate(pages):
        if page.get('type', 'page') not in ('page', 'toc'):
            raise ValueError(f'pages[{index}].type must be page or toc')
        for key in ('section', 'title'):
            if not isinstance(page.get(key), str) or not page[key].strip():
                raise ValueError(f'pages[{index}].{key} must be nonempty text')
        if not isinstance(page.get('blocks'), list):
            raise ValueError(f'pages[{index}].blocks must be an array')
        if page.get('type') == 'toc' and page['blocks']:
            raise ValueError('toc blocks must be empty; entries are generated from actual pagination')
        for block in page['blocks']:
            kind = block.get('type')
            if kind in ('p', 'sub', 'note'):
                if not isinstance(block.get('text'), str):
                    raise ValueError(f'{kind}.text must be a string')
            elif kind == 'table':
                headers, rows = block.get('headers'), block.get('rows')
                if not isinstance(headers, list) or not headers or not isinstance(rows, list):
                    raise ValueError('table requires nonempty headers and rows array')
                if any(not isinstance(row, list) or len(row) != len(headers) for row in rows):
                    raise ValueError('table rows must have the same length as headers')
                widths = block.get('widths')
                if widths is not None and (len(widths) != len(headers) or
                    any(not isinstance(w, (int, float)) or not math.isfinite(w) or w <= 0 for w in widths)
                    or abs(sum(widths) - 1) > 0.001):
                    raise ValueError('table widths must be positive fractions summing to 1')
            elif kind == 'chart':
                for key in ('path', 'title', 'source'):
                    if not isinstance(block.get(key), str):
                        raise ValueError(f'chart.{key} must be a string')
                path = within(run, block['path'], 'chart.path')
                if path.suffix.lower() not in ('.png', '.jpg', '.jpeg') or not path.is_file():
                    raise ValueError(f'chart must be an existing local PNG/JPEG: {path}')
                with PILImage.open(path) as image:
                    if image.format not in ('PNG', 'JPEG'):
                        raise ValueError(f'chart encoding must be PNG/JPEG: {path}')
                    w, h = image.size
                images.append({'path': block['path'], 'sha256': sha256(path), 'pixels': [w, h]})
            elif kind == 'source':
                for key in ('id', 'title', 'publisher', 'url', 'published_at', 'period'):
                    if not isinstance(block.get(key), str):
                        raise ValueError(f'source.{key} must be a string')
                if block['url'] and not safe_url(block['url']):
                    raise ValueError('source.url must be an HTTP(S) URL or empty')
            else:
                raise ValueError(f'unsupported block type: {kind}')
    return images


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def visible_text(content):
    values = [content[k] for k in ('title', 'subtitle', 'ticker', 'as_of', 'quote_note', 'judgment')]
    for metric in content.get('cover_metrics', []):
        values.extend(str(metric[k]) for k in ('value', 'label'))
    for page in content['pages']:
        values.extend((page['title'], page['section']))
        for block in page['blocks']:
            if block['type'] in ('p', 'sub', 'note'):
                values.append(block['text'])
            elif block['type'] == 'table':
                values.extend(str(v) for v in block['headers'])
                values.extend(str(v) for row in block['rows'] for v in row)
            elif block['type'] == 'chart':
                values.extend((block['title'], block['source']))
            elif block['type'] == 'source':
                values.append(source_text(block))
    return '\n'.join(values)


def register_fonts(font_body=None, font_head=None, text=''):
    from font_support import candidates, missing_message
    required = {ord(char) for char in CJK.findall(text)}
    paths = {}
    for name, role, provided, variable in (
            ('BodyCN', 'body', font_body, 'AIR_FONT_BODY'),
            ('HeadCN', 'head', font_head, 'AIR_FONT_HEAD')):
        explicit = provided or os.environ.get(variable)
        choices = [Path(explicit).expanduser()] if explicit else candidates(role)
        failures = []
        for path in choices:
            if not path.is_file():
                if explicit:
                    failures.append(f'File does not exist: {path}')
                continue
            try:
                font = TTFont(name, str(path), subfontIndex=0)
                absent = required - set(font.face.charToGlyph)
                if absent:
                    raise ValueError(f'{len(absent)} required Chinese glyphs absent')
                pdfmetrics.registerFont(font)
                paths[name] = str(path.resolve())
                break
            except Exception as exc:
                failures.append(f'{path}: {exc}')
        else:
            raise ValueError(missing_message(role, '; '.join(failures)))
    pdfmetrics.registerFontFamily('BodyCN', normal='BodyCN', bold='HeadCN', italic='BodyCN', boldItalic='HeadCN')
    return paths


def styles():
    def style(name, font='BodyCN', size=10, leading=16, **kw):
        return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                              textColor=BLACK, wordWrap='CJK', **kw)
    return {
        # Mixed Latin/CJK runs can exceed ReportLab's estimated line width by
        # part of a glyph; reserve a small gutter without reducing 10pt type.
        'p': style('body', spaceAfter=9, rightIndent=8),
        'sub': style('sub', 'HeadCN', 11.5, 18, spaceBefore=5, spaceAfter=7, keepWithNext=True),
        'note': style('note', size=8, leading=12, spaceAfter=7),
        'head': style('heading', 'HeadCN', 21, 29, spaceAfter=17),
        'section': style('section', 'HeadCN', 9, 14, spaceAfter=7, keepWithNext=True),
        'cell': style('cell', size=8.5, leading=13),
        'th': style('th', 'HeadCN', 8.5, 13),
        'cover': style('cover', 'HeadCN', 30, 42, spaceAfter=18),
        'subtitle': style('subtitle', 'BodyCN', 14, 23, spaceAfter=20),
        'metric': style('metric', 'HeadCN', 20, 28),
    }


class Marker(Flowable):
    def __init__(self, index):
        super().__init__()
        self.index = index
        self.width = self.height = 0

    def draw(self):
        pass


class ReportDoc(BaseDocTemplate):
    def __init__(self, path, content, **kw):
        super().__init__(str(path), pagesize=A4, leftMargin=LEFT, rightMargin=RIGHT,
                         topMargin=TOP, bottomMargin=BOTTOM, **kw)
        self.content = content
        self.starts = {}
        self.sections = {}
        self.regions = []
        self.current_index = -1
        frame = Frame(LEFT, BOTTOM, WIDTH, HEIGHT, leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0, id='body')
        self.addPageTemplates(PageTemplate(id='report', frames=[frame], onPage=self.decorate))

    def decorate(self, canvas, doc):
        canvas.setFillColor(BLACK)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.45)
        header = f"{self.content['ticker']}  |  {self.content['as_of']}"
        canvas.setFont('BodyCN', 8)
        canvas.drawString(LEFT, PAGE_H - 33, header)
        canvas.line(LEFT, PAGE_H - 43, PAGE_W - RIGHT, PAGE_H - 43)
        canvas.line(LEFT, 36, PAGE_W - RIGHT, 36)
        footer = '公开信息研究 · ' if CJK.search(visible_text(self.content)) else 'Public information research | '
        canvas.drawString(LEFT, 23, footer + self.content['ticker'])
        canvas.drawRightString(PAGE_W - RIGHT, 23, str(doc.page))

    def afterFlowable(self, flowable):
        if isinstance(flowable, Marker):
            self.current_index = flowable.index
            self.starts[flowable.index] = self.page
            if flowable.index >= 0:
                page = self.content['pages'][flowable.index]
                section = page['section']
                if section not in self.sections:
                    self.sections[section] = self.page
                    key = f'section-{flowable.index}'
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(section, key, 0, False)
                key = f'page-{flowable.index}'
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(page['title'], key, 1, False)
            else:
                self.canv.bookmarkPage('cover')
                self.canv.addOutlineEntry(self.content['title'], 'cover', 0, False)
        elif not isinstance(flowable, (PageBreak, Spacer)):
            height = getattr(flowable, 'height', 0)
            if height:
                # Regions originate from actual Platypus placement, not text guesses.
                y_bottom = self.frame._y + flowable.getSpaceAfter()
                self.regions.append({'page': self.page, 'input_page_index': self.current_index,
                                     'kind': type(flowable).__name__,
                                     'bounds': [LEFT, PAGE_H - y_bottom - height,
                                                PAGE_W - RIGHT, PAGE_H - y_bottom]})


def source_text(block):
    if CJK.search(''.join(str(v) for v in block.values())):
        details = f"发布机构：{block['publisher']}；发布日期：{block['published_at']}；适用期间：{block['period']}"
    else:
        details = f"Publisher: {block['publisher']}; Published: {block['published_at']}; Period: {block['period']}"
    return f"[{block['id']}] {block['title']}\n{details}\n{block['url']}"


def build_story(run, content, sty, actual_starts):
    def p(text, kind='p'):
        return Paragraph(inline(text), sty[kind])
    def table(block):
        widths = block.get('widths') or [1 / len(block['headers'])] * len(block['headers'])
        data = [[p(cell, 'th') for cell in block['headers']]]
        data += [[p(cell, 'cell') for cell in row] for row in block['rows']]
        result = Table(data, colWidths=[WIDTH * w for w in widths], repeatRows=1, hAlign='LEFT')
        result.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LINEABOVE', (0, 0), (-1, 0), 0.6, LINE),
            ('LINEBELOW', (0, 0), (-1, 0), 0.6, LINE),
            ('LINEBELOW', (0, 1), (-1, -1), 0.3, LINE),
        ]))
        return result
    story = [Marker(-1), Spacer(1, 45), p(content['title'], 'cover'),
             p(content['subtitle'], 'subtitle'), p(content['ticker'] + '  |  ' + content['as_of']),
             Spacer(1, 18), p(content['judgment'], 'sub'), p(content['quote_note'], 'note')]
    metrics = content.get('cover_metrics', [])
    if metrics:
        data = [[p(metric['value'], 'metric') for metric in metrics],
                [p(metric['label'], 'note') for metric in metrics]]
        metric_table = Table(data, colWidths=[WIDTH / len(metrics)] * len(metrics), hAlign='LEFT')
        metric_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, LINE),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, 0), 15),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ]))
        story.extend([Spacer(1, 25), metric_table])
    for index, page in enumerate(content['pages']):
        story.extend([PageBreak(), Marker(index), p(page['section'], 'section'), p(page['title'], 'head')])
        if page.get('type') == 'toc':
            entries = []
            for other_index, other in enumerate(content['pages']):
                if other.get('type') != 'toc':
                    entries.append([other['section'] + ' · ' + other['title'], str(actual_starts.get(other_index, '—'))])
            headers = ['章节 / 内容', '实际起页'] if CJK.search(visible_text(content)) else ['Section / content', 'Actual page']
            story.extend([table({'headers': headers, 'rows': entries, 'widths': [.88, .12]}), Spacer(1, 9)])
        for block in page['blocks']:
            kind = block['type']
            if kind in ('p', 'sub', 'note'):
                story.append(p(block['text'], kind))
            elif kind == 'table':
                story.extend([table(block), Spacer(1, 9)])
            elif kind == 'source':
                story.append(p(source_text(block), 'note'))
            elif kind == 'chart':
                path = within(run, block['path'], 'chart.path')
                with PILImage.open(path) as img:
                    w, h = img.size
                width = 480
                height = width * h / w
                title = p(block['title'], 'sub')
                caption = p(block['source'], 'note')
                title_h = title.wrap(WIDTH, HEIGHT)[1] + title.getSpaceBefore() + title.getSpaceAfter()
                caption_h = caption.wrap(WIDTH, HEIGHT)[1] + caption.getSpaceAfter()
                if height + title_h + caption_h + 8 > HEIGHT:
                    raise ValueError(f'chart too tall for one page at 480pt width: {block["path"]}')
                image = Image(str(path), width=width, height=height)
                image.hAlign = 'CENTER'
                story.append(KeepTogether([title, image, Spacer(1, 5), caption]))
    return story


def text_versions(run, content, starts):
    def md_text(value):
        # Markdown viewers must not execute supplied HTML either.
        return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    md = [f"# {md_text(content['title'])}", '', md_text(content['subtitle']), '',
          md_text(content['ticker'] + ' | ' + content['as_of']), '', md_text(content['judgment']), '', md_text(content['quote_note']), '']
    body = ['<article class="cover">', '<h1>' + inline(content['title'], 'html') + '</h1>',
            '<p class="subtitle">' + inline(content['subtitle'], 'html') + '</p>',
            '<p>' + inline(content['ticker'] + ' | ' + content['as_of'], 'html') + '</p>',
            '<p><strong>' + inline(content['judgment'], 'html') + '</strong></p>',
            '<p class="note">' + inline(content['quote_note'], 'html') + '</p>', '<div class="metrics">']
    for metric in content.get('cover_metrics', []):
        md += [f"**{md_text(metric['value'])}** — {md_text(metric['label'])}", '']
        body += ['<div><strong>' + inline(metric['value'], 'html') + '</strong><p>' + inline(metric['label'], 'html') + '</p></div>']
    body += ['</div></article>']
    for index, page in enumerate(content['pages']):
        md += ['---', '', f"## {md_text(page['section'])} · {md_text(page['title'])}", '']
        body += [f'<article id="page-{index}"><p class="section">' + inline(page['section'], 'html') + '</p><h2>' + inline(page['title'], 'html') + '</h2>']
        if page.get('type') == 'toc':
            for other_index, other in enumerate(content['pages']):
                if other.get('type') != 'toc':
                    label = other['section'] + ' · ' + other['title']
                    md += [f"- {md_text(label)} — PDF第{starts[other_index]}页"]
                    body += [f'<p><a href="#page-{other_index}">' + inline(label, 'html') + f'</a><span class="toc-page">PDF {starts[other_index]}</span></p>']
            md += ['']
        for block in page['blocks']:
            kind = block['type']
            if kind in ('p', 'sub', 'note'):
                text = block['text']
                md += [('### ' if kind == 'sub' else '') + md_text(text), '']
                tag = 'h3' if kind == 'sub' else 'p'
                body += [f'<{tag} class="{kind}">' + inline(text, 'html') + f'</{tag}>']
            elif kind == 'table':
                def md_cell(value):
                    return md_text(value).replace('|', '\\|').replace('\n', '<br>')
                md += ['| ' + ' | '.join(md_cell(c) for c in block['headers']) + ' |',
                       '| ' + ' | '.join('---' for _ in block['headers']) + ' |']
                md += ['| ' + ' | '.join(md_cell(c) for c in row) + ' |' for row in block['rows']] + ['']
                body += ['<table><thead><tr>' + ''.join('<th>' + inline(c, 'html') + '</th>' for c in block['headers']) + '</tr></thead><tbody>']
                for row in block['rows']:
                    body += ['<tr>' + ''.join('<td>' + inline(c, 'html') + '</td>' for c in row) + '</tr>']
                body += ['</tbody></table>']
            elif kind == 'chart':
                path = within(run, block['path'], 'chart.path')
                mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
                data = base64.b64encode(path.read_bytes()).decode('ascii')
                md += [f"### {md_text(block['title'])}", '', f"![{md_text(block['title'])}](<../{block['path']}>)", '', md_text(block['source']), '']
                body += ['<figure><h3>' + inline(block['title'], 'html') + '</h3>',
                         f'<img src="data:{mime};base64,{data}" alt="' + html.escape(block['title'], quote=True) + '">',
                         '<figcaption>' + inline(block['source'], 'html') + '</figcaption></figure>']
            elif kind == 'source':
                md += [md_text(source_text(block)), '']
                body += ['<p class="source">' + inline(source_text(block), 'html') + '</p>']
        body += ['</article>']
    css = '''@page{size:A4;margin:20mm}*{box-sizing:border-box}body{max-width:900px;margin:0 auto;padding:42px 32px;color:#000;background:#fff;font-family:SimSun,"宋体",serif;font-size:15px;line-height:1.65}article{padding:32px 0;border-bottom:1px solid #bfc3c7;page-break-before:always}article:first-child{page-break-before:auto}h1,h2,h3,.section{font-family:"Microsoft YaHei",sans-serif;color:#000}h1{font-size:36px}h2{font-size:27px}h3{font-size:18px}p{overflow-wrap:anywhere}a{color:#000;text-decoration:underline;overflow-wrap:anywhere}.subtitle{font-size:21px}.note,figcaption,.source{font-size:12px}.metrics{display:flex;gap:32px;margin-top:35px;border-top:1px solid #bfc3c7;padding-top:20px}.metrics>div{flex:1}.metrics strong{font-size:27px}table{border-collapse:collapse;width:100%;font-size:13px;margin:18px 0;table-layout:fixed}th,td{border-bottom:1px solid #bfc3c7;text-align:left;vertical-align:top;padding:10px;overflow-wrap:anywhere}th{border-top:1px solid #bfc3c7}figure{margin:20px 0;break-inside:avoid}img{display:block;width:100%;height:auto}.toc-page{float:right;font-size:12px}'''
    doc = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + html.escape(content['title']) + '</title><style>' + css + '</style></head><body>' + '\n'.join(body) + '</body></html>'
    return '\n'.join(md), doc


def audit_pdf(pdf_path, doc, content, image_inputs):
    pdf = fitz.open(pdf_path)
    planned = len(content['pages']) + 1
    actual = len(pdf)
    starts = doc.starts
    pages = []
    for index, page in enumerate(content['pages']):
        end = starts.get(index + 1, actual + 1) - 1
        pages.append({'input_page_index': index, 'section': page['section'], 'title': page['title'],
                      'planned_start': index + 2, 'actual_start': starts[index], 'actual_end': end,
                      'actual_page_count': end - starts[index] + 1})
    errors, warnings, bounds_errors, blank_pages = [], [], [], []
    page_checks, all_text, image_occurrences = [], [], []
    for number, page in enumerate(pdf, 1):
        raw = page.get_text('dict')
        body_spans, chinese, body_chars = [], 0, 0
        for block in raw['blocks']:
            if block['type'] != 0:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text']
                    bounds = list(span['bbox'])
                    # Decorations have their own reserved zones and must not be counted as body.
                    header = f"{content['ticker']}  |  {content['as_of']}"
                    footer = ('公开信息研究 · ' if CJK.search(visible_text(content)) else 'Public information research | ') + content['ticker']
                    decoration = ((text == header and bounds[3] < 44) or
                                  (text in (footer, str(number)) and bounds[1] > PAGE_H - 35))
                    if decoration:
                        continue
                    body_chars += len(text.strip())
                    chinese += len(CJK.findall(text))
                    all_text.append(text)
                    body_spans.append(bounds)
                    if (bounds[0] < LEFT - 1.5 or bounds[2] > PAGE_W - RIGHT + 1.5 or
                            bounds[1] < TOP - 4 or bounds[3] > PAGE_H - BOTTOM + 4):
                        bounds_errors.append({'page': number, 'bounds': bounds, 'text': text[:120]})
        images = page.get_image_info()
        for image in images:
            bounds = list(image['bbox'])
            image_occurrences.append({'page': number, 'bounds': bounds, 'pixels': [image['width'], image['height']]})
            if (bounds[0] < LEFT - 1 or bounds[2] > PAGE_W - RIGHT + 1 or
                    bounds[1] < TOP - 1 or bounds[3] > PAGE_H - BOTTOM + 1):
                bounds_errors.append({'page': number, 'bounds': bounds, 'kind': 'image'})
        if not body_chars and not images:
            blank_pages.append(number)
        page_checks.append({'page': number, 'body_text_characters': body_chars, 'chinese_characters': chinese,
                            'images': len(images), 'body_text_bounds': body_spans})
    if bounds_errors:
        errors.append(f'{len(bounds_errors)} text/image bounds violations')
    if blank_pages:
        errors.append(f'blank pages: {blank_pages}')
    if len(image_occurrences) != len(image_inputs):
        errors.append('rendered image occurrence count differs from chart input count')
    expected_chinese = bool(CJK.search(visible_text(content)))
    chinese_count = sum(p['chinese_characters'] for p in page_checks)
    expected_glyphs = set(CJK.findall(json.dumps(content, ensure_ascii=False)))
    extracted_glyphs = set(CJK.findall(''.join(all_text)))
    # Keys and chart paths are not rendered content; check only visible strings.
    visible = [content[k] for k in ('title', 'subtitle', 'ticker', 'as_of', 'quote_note', 'judgment')]
    for metric in content.get('cover_metrics', []):
        visible.extend(str(metric[k]) for k in ('value', 'label'))
    for item in content['pages']:
        visible.extend([item['title'], item['section']])
        for block in item['blocks']:
            if block['type'] in ('p', 'sub', 'note'):
                visible.append(block['text'])
            elif block['type'] == 'table':
                visible.extend(str(v) for v in block['headers'])
                visible.extend(str(v) for row in block['rows'] for v in row)
            elif block['type'] == 'chart':
                visible.extend([block['title'], block['source']])
            elif block['type'] == 'source':
                visible.append(source_text(block))
    expected_glyphs = set(CJK.findall(''.join(visible)))
    missing_glyphs = sorted(expected_glyphs - extracted_glyphs)
    if expected_chinese and chinese_count == 0:
        errors.append('Chinese text extraction failed')
    if missing_glyphs:
        errors.append(f'{len(missing_glyphs)} expected Chinese glyphs missing from extracted PDF text')
    if actual != planned:
        warnings.append(f'planned {planned} pages, actual {actual}; actual mapping is authoritative')
    for mapping in pages:
        if mapping['actual_page_count'] > 1:
            warnings.append(f'input page {mapping["input_page_index"]} overflowed to {mapping["actual_page_count"]} actual pages')
    if starts.get(0) != 2:
        errors.append('cover overflowed beyond one page; shorten cover content')
    outlines = pdf.get_toc()
    expected_outline = [(content['title'], 1)]
    seen = set()
    for index, page in enumerate(content['pages']):
        if page['section'] not in seen:
            expected_outline.append((page['section'], starts[index]))
            seen.add(page['section'])
        expected_outline.append((page['title'], starts[index]))
    if [(item[1], item[2]) for item in outlines] != expected_outline:
        errors.append('outline destinations do not match actual section/page starts')
    pdf_links = sum(len(page.get_links()) for page in pdf)
    audit = {
        'status': 'fail' if errors else ('warning' if warnings else 'pass'),
        'planned_pages': planned, 'actual_pages': actual, 'page_mapping': pages,
        'section_actual_start_pages': doc.sections, 'errors': errors, 'warnings': warnings,
        'blank_pages': blank_pages, 'blank_page_count': len(blank_pages),
        'text_bounds_violations': bounds_errors, 'body_frame': [LEFT, TOP, PAGE_W - RIGHT, PAGE_H - BOTTOM],
        'input_chart_count': len(image_inputs), 'actual_image_count': len(image_occurrences),
        'image_occurrences': image_occurrences, 'chinese_extraction': {
            'required': expected_chinese, 'extracted_characters': chinese_count,
            'expected_unique_glyphs': len(expected_glyphs), 'missing_glyphs': missing_glyphs,
            'passed': not missing_glyphs and (not expected_chinese or chinese_count > 0)},
        'outline': outlines, 'outline_actual_pages_verified': not any('outline' in e for e in errors),
        'clickable_link_count': pdf_links, 'pages': page_checks,
        'flowable_regions': doc.regions,
    }
    pdf.close()
    return audit


def publish(run, content_path, font_body=None, font_head=None):
    run = Path(run)
    if not run.is_absolute() or not run.is_dir():
        raise ValueError('--run must be an existing absolute run directory')
    run = run.resolve()
    source = within(run, content_path, '--content')
    content_bytes = source.read_bytes()
    content = json.loads(content_bytes.decode('utf-8-sig'))
    image_inputs = validate(run, content)
    # Chinese decoration is used only for Chinese reports; English runs can use DejaVu.
    required_text = visible_text(content)
    if CJK.search(required_text):
        required_text += '公开信息研究章节内容实际起页发布机构发布日期适用期间'
    fonts = register_fonts(font_body, font_head, required_text)
    sty = styles()
    deliverables = within(run, '04_deliverables', 'deliverables')
    internal = within(run, '99_internal', 'internal')
    deliverables.mkdir(exist_ok=True)
    internal.mkdir(exist_ok=True)
    filename = content['filename']
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    pdf_path = deliverables / filename
    # Reflow TOC until actual starts converge; every pass rebuilds fresh flowables.
    previous = {}
    doc = None
    iterations = 0
    for iterations in range(1, 7):
        doc = ReportDoc(pdf_path, content, title=content['title'], author='Research Publisher',
                        subject=content['subtitle'])
        doc.build(build_story(run, content, sty, previous))
        current = {i: doc.starts[i] for i in range(len(content['pages']))}
        if not any(p.get('type') == 'toc' for p in content['pages']) or current == previous:
            break
        previous = current
    else:
        raise ValueError('TOC pagination failed to converge after 6 passes')
    audit = audit_pdf(pdf_path, doc, content, image_inputs)
    audit['toc_build_passes'] = iterations
    markdown, html_doc = text_versions(run, content, current)
    (deliverables / 'report.md').write_text(markdown, encoding='utf-8')
    (deliverables / 'report.html').write_text(html_doc, encoding='utf-8')
    audit_path = internal / 'pdf-layout-audit.json'
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    paths = [pdf_path, deliverables / 'report.md', deliverables / 'report.html', audit_path]
    manifest = {
        'schema_version': 1, 'publisher': 'publisher.py',
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'content': str(source.relative_to(run)), 'content_sha256': hashlib.sha256(content_bytes).hexdigest(),
        'title': content['title'], 'ticker': content['ticker'], 'as_of': content['as_of'],
        'status': audit['status'], 'planned_pages': audit['planned_pages'], 'actual_pages': audit['actual_pages'],
        'page_mapping': audit['page_mapping'], 'section_actual_start_pages': doc.sections,
        'fonts': fonts, 'body_font_size_pt': 10, 'body_leading_pt': 16,
        'chart_width_pt': 480, 'chart_inputs': image_inputs,
        'outputs': [{'path': str(p.relative_to(run)), 'sha256': sha256(p), 'bytes': p.stat().st_size} for p in paths],
        'errors': audit['errors'], 'warnings': audit['warnings'],
    }
    (internal / 'report_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, help='absolute report run directory')
    parser.add_argument('--content', required=True, help='content JSON path relative to run')
    parser.add_argument('--font-body', help='licensed body TTF/TTC; overrides AIR_FONT_BODY')
    parser.add_argument('--font-head', help='licensed heading TTF/TTC; overrides AIR_FONT_HEAD')
    args = parser.parse_args()
    try:
        result = publish(args.run, args.content, args.font_body, args.font_head)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result['status'] == 'fail' else 0
    except Exception as exc:
        print(f'publisher error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
