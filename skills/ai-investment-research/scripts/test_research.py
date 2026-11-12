"""Meaningful isolated fixtures; no real company facts or network access.

Parent runner may set RESEARCH_TEST_TMPDIR (or TEMP/TMP) to a project folder.
Run: python -B -m unittest discover -s <scripts-directory> -p test_research.py -v
"""
import argparse
import base64
import binascii
import struct
import zlib
from datetime import date, timedelta
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import xml.etree.ElementTree as ET
import zipfile

spec = importlib.util.spec_from_file_location('research_under_test', Path(__file__).with_name('research.py'))
research = importlib.util.module_from_spec(spec)
spec.loader.exec_module(research)


class ResearchTests(unittest.TestCase):
    def setUp(self):
        # The parent may keep fixtures in a project directory; otherwise use OS temp.
        configured = os.environ.get('RESEARCH_TEST_TMPDIR')
        root = Path(configured).resolve() if configured else None
        if root is not None:
            root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='research-fixture-', dir=root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'run'
        self.args = argparse.Namespace(output=str(self.run), topic='测试公司：明确虚构 fixture',
                                       market='CN', as_of='2025-01-02', mode='company',
                                       horizon=research.DEFAULT_HORIZON, company=['测试公司'],
                                       format='md,html,docx')
        research.init_run(self.args)

    def save(self, name, data):
        research.dump(self.run / name, data)

    def meta(self, **updates):
        path = self.run / 'research.json'
        value = json.loads(path.read_text(encoding='utf-8'))
        value.update(updates); self.save('research.json', value)
        return value

    def report(self, text='# 测试公司\n\n这是明确的测试夹具，不是真实研究。\n'):
        (self.run / '04_deliverables/report.md').write_text(text, encoding='utf-8')

    def source(self, **updates):
        value = dict(id='S1', title='测试夹具资料', publisher='测试机构', url='https://example.invalid/fixture',
                     published_at='2025-01-01', retrieved_at='2025-01-02', source_type='fixture', period='2024测试期间')
        value.update(updates)
        return value

    def forecast(self, **updates):
        value = dict(id='F1', subject='测试公司', forecast_type='fundamental', as_of='2025-01-02',
                     horizon='一个月', baseline=100, target=110, unit='测试单位',
                     scenarios=[dict(name='测试情景A', probability=0.6, trigger='测试指标达标', invalidation='测试指标低于门槛'),
                                dict(name='测试情景B', probability=0.4, trigger='测试指标未达标', invalidation='测试指标超过门槛')],
                     leading_indicators=['测试指标'], validation_date='2025-02-02', status='open', source_ids=['S1'])
        value.update(updates)
        return value

    def codes(self, strict=False):
        return {x['code'] for x in research.check_run(self.run, strict)['issues']}

    def directory_link(self, link, target):
        try:
            link.symlink_to(target, target_is_directory=True)
            self.addCleanup(link.unlink)
        except OSError:
            if os.name != 'nt':
                raise
            result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(target)],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            self.assertEqual(result.returncode, 0, '创建项目内 fixture junction 失败')
            self.addCleanup(link.rmdir)

    def test_init_resume_preserves_every_existing_byte_and_refuses_plain_directory(self):
        self.report()
        before = {str(p.relative_to(self.run)): p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        self.args.topic = '不能覆盖主题'
        self.assertEqual(research.init_run(self.args)['action'], 'resume')
        after = {str(p.relative_to(self.run)): p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.args.output = str(self.root)
        with self.assertRaises(ValueError):
            research.init_run(self.args)
        self.assertEqual(set(json.loads((self.run / 'research.json').read_text(encoding='utf-8'))['modules']), set(research.MODULES))

    def test_init_requires_absolute_output_and_does_not_fabricate_sources(self):
        self.args.output = 'relative-test-output'
        with self.assertRaises(ValueError):
            research.init_run(self.args)
        for name in ('sources', 'claims', 'forecasts'):
            self.assertEqual(json.loads((self.run / f'{name}.json').read_text()), [])
        self.assertFalse((self.run / '04_deliverables/report.md').exists())

    def test_paths_block_traversal_absolute_windows_and_symlink_escape(self):
        for path in ('../outside.md', '01_sources/../../outside.md', '/outside.md', 'C:\\outside.md', '\\\\server\\file.md'):
            with self.subTest(path=path):
                self.meta(report_path=path)
                self.assertIn('path', self.codes())
        outside = self.root / 'outside'; outside.mkdir()
        link = self.run / 'escape'
        self.directory_link(link, outside)
        self.meta(report_path='escape/secret.md')
        self.assertIn('path', self.codes())
        self.save('sources.json', [self.source(local_path='escape/raw.txt')])
        self.assertTrue(any(i['location'].endswith('local_path') for i in research.check_run(self.run)['errors']))

    def test_check_is_readonly_and_normal_warning_becomes_strict_evidence_error(self):
        self.report()
        self.save('claims.json', [dict(id='C1', text='虚构测试事实', kind='fact', source_ids=[], as_of='2025-01-02', confidence='low')])
        before = {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        normal, strict = research.check_run(self.run), research.check_run(self.run, True)
        self.assertTrue(normal['valid']); self.assertFalse(strict['valid'])
        self.assertTrue(any(x['code'] == 'evidence' for x in strict['errors']))
        self.assertEqual(before, {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()})

    def test_duplicate_unknown_source_bad_date_and_future_retrieval(self):
        future = (date.today() + timedelta(days=2)).isoformat()
        self.save('sources.json', [self.source(published_at='2025-02-30'), self.source(retrieved_at=future)])
        self.save('claims.json', [dict(id='C1', text='测试', kind='assumption', source_ids=['missing'], as_of='2025-01-02', confidence='medium')])
        self.assertTrue({'duplicate_id', 'date', 'future_retrieval', 'source_reference'} <= self.codes())

    def test_probabilities_require_range_total_and_complete_series(self):
        self.save('sources.json', [self.source()])
        for kind in ('sum', 'missing', 'range', 'bool', 'nan'):
            with self.subTest(kind=kind):
                forecast = self.forecast()
                first, second = forecast['scenarios']
                if kind == 'sum':
                    second['probability'] = .3
                elif kind == 'missing':
                    second.pop('probability')
                else:
                    first['probability'] = {'range': 1.2, 'bool': True, 'nan': float('nan')}[kind]
                self.save('forecasts.json', [forecast])
                self.assertIn('probability_sum', self.codes())
                if kind in ('range', 'bool', 'nan'):
                    self.assertIn('probability', self.codes())
        self.save('forecasts.json', [self.forecast()]); self.report()
        self.assertTrue(research.check_run(self.run, True)['valid'])

    def test_missing_forecast_baseline_dates_and_invalidation_fail_strict(self):
        forecast = self.forecast(source_ids=[])
        for key in ('baseline', 'as_of', 'validation_date'):
            forecast.pop(key)
        forecast['scenarios'] = []
        self.save('forecasts.json', [forecast]); self.report()
        self.assertTrue(research.check_run(self.run)['valid'])
        self.assertFalse(research.check_run(self.run, True)['valid'])
        self.assertIn('invalidation', self.codes(True))

    def test_assumptions_need_no_source_and_technical_target_is_not_valuation(self):
        self.report()
        self.save('claims.json', [dict(id='A', text='测试假设', kind='assumption', source_ids=[], as_of='2025-01-02', confidence='low')])
        self.assertTrue(research.check_run(self.run, True)['valid'])
        self.save('forecasts.json', [self.forecast(forecast_type='technical', source_ids=[])])
        self.assertIn('technical_target', self.codes())
        self.assertTrue(research.check_run(self.run, True)['valid'])

    def test_missing_report_and_explicit_placeholders_only(self):
        self.assertFalse(research.check_run(self.run, True)['valid'])
        self.report('# 正文\n\n待核实的局限性和示例区间不是自动假数据。\n')
        self.assertTrue(research.check_run(self.run, True)['valid'])
        self.report('# 正文\n\n{{明确占位符}} TODO\n')
        self.assertIn('placeholder', self.codes(True))

    def test_full_incomplete_modules_need_actual_limitations_and_cannot_complete(self):
        self.meta(mode='full', status='complete')
        self.report('# 资料缺口\n\n行业 公司 事件 周线 宏观\n')
        self.assertIn('module_disclosure', self.codes(True))
        self.assertIn('false_completion', self.codes())
        self.meta(status='draft')
        self.report('# 研究\n\n## 资料缺口\n\n' + '\n'.join(f'{label}资料未获取，模块待完成。' for label in research.LABELS.values()))
        self.assertTrue(research.check_run(self.run, True)['valid'])

    def test_full_disclosure_accepts_technical_table_alias_and_completed_scope_skips(self):
        modules = {name: {'status': 'skipped', 'reason': '本题范围不适用', 'artifact': ''} for name in research.MODULES}
        self.meta(mode='full', status='limited', modules=modules)
        rows = [('行业', 'skipped'), ('公司', 'skipped'), ('事件', 'skipped'), ('技术', 'limited'), ('宏观', 'skipped')]
        modules['technical'] = {'status': 'limited', 'reason': '没有K线图', 'artifact': ''}
        self.meta(modules=modules)
        self.report('# 报告\n\n## 研究范围与资料缺口\n\n| 模块 | 状态 | 原因 |\n| --- | --- | --- |\n' + ''.join(f'| {label} | {status} | 资料缺少或不适用 |\n' for label, status in rows))
        self.assertTrue(research.check_run(self.run, True)['valid'])
        self.meta(status='complete')
        self.assertIn('false_completion', self.codes(True))
        modules['technical'] = {'status': 'skipped', 'reason': '用户明确不研究价格路径', 'artifact': ''}
        self.meta(modules=modules)
        self.assertTrue(research.check_run(self.run, True)['valid'])
        modules['industry'] = {'status': 'complete', 'reason': '', 'artifact': ''}
        self.meta(modules=modules)
        self.assertIn('artifact_required', self.codes(True))

    def test_render_valid_zip_xml_chinese_table_links_source_preserved_and_script_escaped(self):
        text = ('# 测试公司报告\n\n**中文重点** 与 [测试来源](https://example.invalid/evidence)。\n\n'
                '| 指标 | 数值 |\n| --- | --- |\n| 中文表格 | 夹具100 |\n\n'
                '- 测试列表\n\n1. 第一项\n\n```python\nprint("测试")\n```\n\n'
                '<script src="https://evil.invalid/x.js">alert("fixture")</script>\n')
        self.report(text)
        self.save('sources.json', [self.source()])
        original = (self.run / '04_deliverables/report.md').read_bytes()
        manifest = research.render_run(self.run)
        self.assertTrue(manifest['valid'])
        self.assertEqual(original, (self.run / '04_deliverables/report.md').read_bytes())
        page = (self.run / '04_deliverables/report.html').read_text(encoding='utf-8')
        self.assertIn('&lt;script', page); self.assertNotIn('<script', page)
        for marker in ('<table>', '<strong>中文重点</strong>', '<nav', '数据截止: 2025-01-02', '研究状态: draft', 'https://example.invalid/evidence', '证据来源登记'):
            self.assertIn(marker, page)
        with zipfile.ZipFile(self.run / '04_deliverables/report.docx') as archive:
            self.assertIsNone(archive.testzip())
            for filename in archive.namelist():
                if filename.endswith(('.xml', '.rels')):
                    ET.fromstring(archive.read(filename))
            doc = ET.fromstring(archive.read('word/document.xml'))
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            texts = ''.join(doc.itertext())
            self.assertIn('中文表格', texts); self.assertIn('中文重点', texts)
            self.assertEqual(len(doc.findall('.//w:tbl', ns)), 1)
            self.assertGreater(len(doc.findall('.//w:hyperlink', ns)), 0)
            self.assertIn('https://example.invalid/evidence', archive.read('word/_rels/document.xml.rels').decode())
            self.assertIn('Microsoft YaHei', archive.read('word/styles.xml').decode())
        self.assertEqual(json.loads((self.run / 'research.json').read_text(encoding='utf-8'))['status'], 'draft')
        self.assertTrue((self.run / '99_internal/delivery_manifest.json').is_file())

    def test_javascript_links_never_become_active_links(self):
        self.report('# 测试\n\n[危险](javascript:alert) 与 <img src="https://evil.invalid/a">\n')
        research.render_run(self.run, 'html,docx')
        page = (self.run / '04_deliverables/report.html').read_text(encoding='utf-8')
        self.assertNotIn('href="javascript:', page); self.assertNotIn('<img', page)
        with zipfile.ZipFile(self.run / '04_deliverables/report.docx') as archive:
            rels = archive.read('word/_rels/document.xml.rels').decode()
            self.assertNotIn('javascript:', rels)

    def test_pdf_unavailable_and_failed_are_real_failures_with_html_retained(self):
        self.report()
        with mock.patch.object(research, 'browsers', return_value=[]):
            result = research.render_run(self.run, 'pdf')
        self.assertFalse(result['valid'])
        pdf = result['exports'][-1]
        self.assertEqual(pdf['status'], 'unavailable'); self.assertFalse(pdf['magic_valid'])
        self.assertTrue((self.run / '04_deliverables/report.html').is_file())
        with mock.patch.object(research, 'browsers', return_value=['fixture-browser']), mock.patch.object(research.subprocess, 'run', return_value=argparse.Namespace(returncode=0)):
            result = research.render_run(self.run, 'pdf')
        self.assertFalse(result['valid']); self.assertEqual(result['exports'][-1]['size'], 0)
        self.assertIn('PDF 无效', result['exports'][-1]['reason'])

    def test_render_rejects_escaping_output_symlink_before_any_write(self):
        self.report()
        destination = self.run / '99_internal'
        self.assertEqual(destination.resolve(), self.run.resolve() / '99_internal')
        self.assertFalse(any(destination.iterdir()))
        destination.rmdir()  # Known empty fixture directory, replaced by an escaping junction.
        outside = self.root / 'protected'; outside.mkdir()
        sentinel = outside / 'delivery_manifest.json'; sentinel.write_bytes(b'protected fixture')
        self.directory_link(destination, outside)
        with self.assertRaises(ValueError):
            research.render_run(self.run, 'html,docx')
        self.assertEqual(sentinel.read_bytes(), b'protected fixture')
        self.assertFalse((self.run / '04_deliverables/report.html').exists())

    def test_unknown_publication_local_source_and_lookahead_are_explicit(self):
        self.report()
        raw = self.run / '01_sources/raw/fixture.txt'; raw.write_text('明确测试资料', encoding='utf-8')
        self.save('sources.json', [self.source(published_at='unknown', url='local:fixture.txt', local_path='01_sources/raw/fixture.txt')])
        result = research.check_run(self.run, True)
        self.assertTrue(result['valid'])
        self.assertTrue({'unknown_publication', 'local_source'} <= {i['code'] for i in result['warnings']})
        self.save('sources.json', [self.source(published_at='2025-01-03', retrieved_at='2025-01-04')])
        self.save('forecasts.json', [self.forecast()])
        self.assertTrue(research.check_run(self.run)['valid'])
        self.assertIn('lookahead', self.codes(True))
        self.assertFalse(research.check_run(self.run, True)['valid'])

    def test_empty_indicators_and_missing_images_are_disclosed(self):
        self.report('# 夹具\n\n![测试图](01_sources/raw/chart.png)\n')
        self.save('forecasts.json', [self.forecast(source_ids=[], leading_indicators=[])])
        self.assertIn('leading_indicators', self.codes(True))
        result = research.render_run(self.run, 'html')
        self.assertIn('image_rejected', {i['code'] for i in result['check']['warnings']})

    def png(self, width=800, height=400):
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', binascii.crc32(kind + data) & 0xffffffff)
        return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress((b'\x00' + b'\xff\x00\x00' * width) * height)) + chunk(b'IEND', b''))

    def test_png_and_jpeg_embed_in_html_and_docx_with_relationships_and_proportion(self):
        png = self.png()
        # Complete tiny JPEG fixture (offline); dimensions are 1 x 1.
        jpeg = base64.b64decode('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAABQb/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAB//2Q==')
        (self.run / '03_models/chart.png').write_bytes(png)
        (self.run / '04_deliverables/photo.jpg').write_bytes(jpeg)
        self.report('# 图表\n\n![PNG <测试>](../03_models/chart.png)\n![JPEG](photo.jpg)\n')
        result = research.render_run(self.run, 'html,docx')
        self.assertTrue(result['valid'])
        self.assertFalse(any(i['code'].startswith('image_') for i in result['check']['warnings']))
        page = (self.run / '04_deliverables/report.html').read_text(encoding='utf-8')
        self.assertIn('img-src data:', page)
        for mime, payload in (('image/png', png), ('image/jpeg', jpeg)):
            self.assertIn('data:' + mime + ';base64,' + base64.b64encode(payload).decode(), page)
        self.assertIn('alt="PNG &lt;测试&gt;"', page)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
              'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
              'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
              'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
        with zipfile.ZipFile(self.run / '04_deliverables/report.docx') as archive:
            document = ET.fromstring(archive.read('word/document.xml'))
            drawings = document.findall('.//w:drawing/wp:inline', ns)
            self.assertEqual(len(drawings), 2)
            relations = {x.attrib['Id']: x.attrib for x in ET.fromstring(archive.read('word/_rels/document.xml.rels'))}
            for drawing, payload, ratio in zip(drawings, (png, jpeg), (2, 1)):
                embed = drawing.find('.//a:blip', ns).attrib['{' + ns['r'] + '}embed']
                relation = relations[embed]
                self.assertTrue(relation['Type'].endswith('/image'))
                self.assertNotIn('TargetMode', relation)
                self.assertEqual(archive.read('word/' + relation['Target']), payload)
                extent = drawing.find('wp:extent', ns).attrib
                self.assertLessEqual(int(extent['cx']), 9638 * 635)
                self.assertAlmostEqual(int(extent['cx']) / int(extent['cy']), ratio, places=5)
            types = archive.read('[Content_Types].xml').decode()
            self.assertIn('image/png', types); self.assertIn('image/jpeg', types)
        if importlib.util.find_spec('docx'):
            from docx import Document
            self.assertEqual(len(Document(self.run / '04_deliverables/report.docx').inline_shapes), 2)

    def test_image_escape_absolute_and_symlink_are_rejected_without_reading_outside(self):
        outside = self.root / 'outside'; outside.mkdir()
        secret = self.png(); (outside / 'secret.png').write_bytes(secret)
        self.directory_link(self.run / 'escape', outside)
        paths = ('../../outside/secret.png', str(outside / 'secret.png'), '../escape/secret.png')
        for reference in paths:
            with self.subTest(reference=reference):
                self.report(f'# 图\n\n![逃逸 alt]({reference})\n')
                result = research.render_run(self.run, 'html,docx')
                self.assertIn('image_rejected', {i['code'] for i in result['check']['warnings']})
                page = (self.run / '04_deliverables/report.html').read_text(encoding='utf-8')
                self.assertIn('逃逸 alt', page); self.assertNotIn('<img', page)
                with zipfile.ZipFile(self.run / '04_deliverables/report.docx') as archive:
                    self.assertFalse(any(x.startswith('word/media/') for x in archive.namelist()))

    def test_external_svg_inline_example_and_oversized_images_warn_and_keep_alt(self):
        (self.run / '04_deliverables/chart.svg').write_text('<svg><script/></svg>')
        examples = self.run / '_example'; examples.mkdir()
        (examples / 'chart.png').write_bytes(self.png())
        (self.run / '04_deliverables/large.png').write_bytes(b'x' * (research.IMAGE_LIMIT + 1))
        self.report('# 图\n\n![外图](https://example.invalid/image.png)\n\n![矢量](chart.svg)\n\n'
                    '前文 ![行内](chart.png) 后文\n\n![示例](../_example/chart.png)\n\n![过大](large.png)\n')
        result = research.render_run(self.run, 'html,docx')
        warnings = result['check']['warnings']
        self.assertEqual(sum(i['code'] == 'image_rejected' for i in warnings), 4)
        self.assertIn('image_inline_unsupported', {i['code'] for i in warnings})
        self.assertIn('不下载', str(warnings)); self.assertIn('10 MiB', str(warnings))
        page = (self.run / '04_deliverables/report.html').read_text(encoding='utf-8')
        self.assertNotIn('<img', page)
        for alt in ('外图', '矢量', '行内', '示例', '过大'):
            self.assertIn(alt, page)

    def test_resume_rejects_partial_or_bad_types_and_accepts_bare_valid_draft_readonly(self):
        original = json.loads((self.run / 'research.json').read_text(encoding='utf-8'))
        for data in ({'schema_version': '1.0', 'run_id': 'junk'}, dict(original, formats='html'),
                     dict(original, companies={}), dict(original, modules={}), dict(original, as_of='bad')):
            self.save('research.json', data)
            before = {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):
                research.init_run(self.args)
            self.assertEqual(before, {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()})
        self.save('research.json', original)
        for name in ('sources.json', 'claims.json', 'forecasts.json'):
            (self.run / name).unlink()  # Only known fixture files; draft resume needs metadata alone.
        before = {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()}
        self.assertEqual(research.init_run(self.args)['action'], 'resume')
        self.assertEqual(before, {p: p.read_bytes() for p in self.run.rglob('*') if p.is_file()})

    def test_malformed_json_and_arrays_report_issues_without_crashing(self):
        self.meta(market=[], companies={}, formats=[{}], modules=[])
        self.save('claims.json', [None, {'id': []}])
        (self.run / 'sources.json').write_text('{broken', encoding='utf-8')
        result = research.check_run(self.run)
        self.assertFalse(result['valid'])
        self.assertTrue({'json', 'type', 'modules', 'enum'} <= {x['code'] for x in result['issues']})


if __name__ == '__main__':
    unittest.main()
