"""Offline synthetic boundary tests; all runtime fixtures live in cleaned temp dirs."""
import copy
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chartkit
import publisher
import reportlab
from PIL import Image
from matplotlib import pyplot as plt

VERA = Path(reportlab.__file__).resolve().parent / 'fonts' / 'Vera.ttf'


def fixture():
    return dict(title='SYNTHETIC TEST ONLY', subtitle='No investment conclusions', ticker='TEST',
                as_of='2025-01-02', quote_note='Synthetic input', judgment='Not research', filename='synthetic',
                pages=[dict(section='Test', title='Evidence', blocks=[dict(type='p', text='Synthetic report text.')])])


class PublisherTests(unittest.TestCase):
    def setUp(self):
        configured = os.environ.get('RESEARCH_TEST_TMPDIR')
        root = Path(configured).resolve() if configured else None
        if root:
            root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='publisher-synthetic-', dir=root)
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name).resolve()
        (self.run / '99_internal').mkdir()

    def write(self, content):
        (self.run / '99_internal/content.json').write_text(json.dumps(content, ensure_ascii=False), encoding='utf-8')

    def test_markup_is_escaped_and_only_http_links_are_active(self):
        text = '<script>alert(1)</script> **bold** https://example.com/a?x=1&y=2 javascript:alert(1)'
        result = publisher.inline(text, 'html')
        self.assertNotIn('<script>', result)
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('<strong>bold</strong>', result)
        self.assertIn('href="https://example.com/a?x=1&amp;y=2"', result)
        self.assertNotIn('href="javascript:', result)
        self.assertIsNone(publisher.safe_url('file:///etc/passwd'))

    def test_cross_platform_path_traversal_is_rejected(self):
        for value in ('../x.png', '/tmp/x.png', 'C:/x.png', 'C:\\x.png', '\\\\host\\x.png', 'a/../../x.png'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                publisher.within(self.run, value, 'test')

    def test_local_png_hash_and_encoding_are_verified(self):
        image = self.run / 'image.png'; Image.new('RGB', (90, 30), 'white').save(image)
        content = fixture()
        content['pages'][0]['blocks'] = [dict(type='chart', path='image.png', title='Chart', source='Synthetic')]
        result = publisher.validate(self.run, content)
        self.assertEqual(result[0]['pixels'], [90, 30])
        self.assertEqual(result[0]['sha256'], publisher.sha256(image))
        image.write_bytes(b'<svg></svg>')
        with self.assertRaises(Exception):
            publisher.validate(self.run, content)

    def test_filename_and_table_widths_are_rejected(self):
        content = fixture(); content['filename'] = '../bad'
        with self.assertRaises(ValueError): publisher.validate(self.run, content)
        content = fixture()
        content['pages'][0]['blocks'] = [dict(type='table', headers=['a', 'b'], rows=[[1, 2]], widths=[.8, .8])]
        with self.assertRaises(ValueError): publisher.validate(self.run, content)

    def test_font_precedence_and_english_fallback(self):
        with mock.patch.dict(os.environ, {'AIR_FONT_BODY': 'missing-body.ttf', 'AIR_FONT_HEAD': 'missing-head.ttf'}):
            selected = publisher.register_fonts(str(VERA), str(VERA), 'English only')
        self.assertEqual(Path(selected['BodyCN']), VERA)
        with mock.patch('font_support.candidates', return_value=[VERA]), mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Path(publisher.register_fonts(text='English')['HeadCN']), VERA)

    def test_english_font_cannot_silently_render_chinese(self):
        with self.assertRaisesRegex(ValueError, 'AIR_FONT_BODY.*Chinese'):
            publisher.register_fonts(str(VERA), str(VERA), '中文')

    def test_chinese_publish_checks_real_glyphs(self):
        try:
            fonts = publisher.register_fonts(text='中文测试合成报告')
        except ValueError as exc:
            self.skipTest(f'No compatible system CJK font: {exc}')
        content = fixture(); content.update(title='合成测试报告', subtitle='中文测试', judgment='测试')
        content['pages'][0].update(section='测试', title='中文')
        content['pages'][0]['blocks'] = [dict(type='p', text='中文测试，不是真实研究。')]
        self.write(content)
        result = publisher.publish(self.run, '99_internal/content.json', fonts['BodyCN'], fonts['HeadCN'])
        audit = json.loads((self.run / '99_internal/pdf-layout-audit.json').read_text(encoding='utf-8'))
        self.assertEqual(result['status'], 'pass', result['errors'])
        self.assertTrue(audit['chinese_extraction']['passed'])
        self.assertGreater(audit['chinese_extraction']['extracted_characters'], 0)

    def test_real_toc_overflow_warning_bounds_images_and_escaping(self):
        Image.new('RGB', (900, 300), 'white').save(self.run / 'chart.png')
        content = fixture()
        content['pages'] = [dict(type='toc', section='Navigation', title='Contents', blocks=[]),
                            dict(section='Evidence', title='Long content', blocks=[
                                dict(type='p', text='<script>literal</script> **bold** https://example.com/test'),
                                dict(type='chart', path='chart.png', title='Synthetic chart', source='Synthetic input')]
                                 + [dict(type='p', text=('Long synthetic paragraph for pagination. ' * 7)) for _ in range(32)]),
                            dict(section='End', title='Last page', blocks=[dict(type='p', text='End of synthetic test.')])]
        self.write(content)
        result = publisher.publish(self.run, '99_internal/content.json', str(VERA), str(VERA))
        audit = json.loads((self.run / '99_internal/pdf-layout-audit.json').read_text(encoding='utf-8'))
        self.assertEqual(result['status'], 'warning', result['errors'])
        self.assertGreater(result['actual_pages'], result['planned_pages'])
        self.assertTrue(result['warnings'])
        self.assertEqual(audit['blank_page_count'], 0)
        self.assertEqual(audit['text_bounds_violations'], [])
        self.assertEqual(audit['actual_image_count'], 1)
        self.assertTrue(audit['outline_actual_pages_verified'])
        final_start = result['page_mapping'][-1]['actual_start']
        html = (self.run / '04_deliverables/report.html').read_text(encoding='utf-8')
        self.assertIn(f'PDF {final_start}', html)
        self.assertIn('data:image/png;base64,', html)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertGreaterEqual(audit['toc_build_passes'], 2)

    def test_public_cli_font_arguments_override_invalid_environment(self):
        self.write(fixture())
        environment = dict(os.environ, AIR_FONT_BODY='missing.ttf', AIR_FONT_HEAD='missing.ttf', PYTHONUTF8='1')
        result = subprocess.run([sys.executable, '-B', str(Path(publisher.__file__)), '--run', str(self.run),
                                 '--content', '99_internal/content.json', '--font-body', str(VERA), '--font-head', str(VERA)],
                                env=environment, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'pass')
        self.assertTrue((self.run / '04_deliverables/synthetic.pdf').is_file())

    def test_escaping_symlink_and_output_directory_are_rejected(self):
        outside = self.run / 'outside'; outside.mkdir()
        root = self.run / 'nested-run'; root.mkdir()
        link = root / 'escape'
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != 'nt': raise
            completed = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(outside)], capture_output=True)
            self.assertEqual(completed.returncode, 0)
        self.addCleanup(lambda: link.unlink() if link.is_symlink() else link.rmdir())
        with self.assertRaisesRegex(ValueError, 'escapes run'):
            publisher.within(root, 'escape/image.png', 'chart.path')
        (root / '99_internal').mkdir()
        (root / '99_internal/content.json').write_text(json.dumps(fixture()), encoding='utf-8')
        output = root / '04_deliverables'
        try:
            output.symlink_to(outside, target_is_directory=True)
        except OSError:
            completed = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(output), str(outside)], capture_output=True)
            self.assertEqual(completed.returncode, 0)
        self.addCleanup(lambda: output.unlink() if output.is_symlink() else output.rmdir())
        with self.assertRaisesRegex(ValueError, 'escapes run'):
            publisher.publish(root, '99_internal/content.json', str(VERA), str(VERA))
        self.assertEqual(list(outside.iterdir()), [])

    def test_waterfall_negative_total_stays_below_zero(self):
        charts = chartkit.Charts(self.run, font=str(VERA))
        def inspect(id, fig, source):
            total = fig.axes[0].patches[-1]
            self.assertEqual(total.get_y(), -1)
            self.assertEqual(total.get_height(), 1)
            plt.close(fig)
            return id
        with mock.patch.object(charts, 'save', side_effect=inspect):
            charts.waterfall('negative', ['a', 'b', 'total'], [2, -3, -1], 'unit', 'synthetic')

    def test_waterfall_rejects_point_one_mismatch_unless_explicit_tolerance(self):
        charts = chartkit.Charts(self.run, font=str(VERA))
        with self.assertRaisesRegex(ValueError, 'waterfall mismatch'):
            charts.waterfall('mismatch', ['a', 'b', 'total'], [1, 2, 3.1], 'unit', 'synthetic')
        with mock.patch.object(charts, 'save', side_effect=lambda id, fig, source: plt.close(fig)):
            charts.waterfall('rounded', ['a', 'b', 'total'], [1, 2, 3.1], 'unit', 'synthetic', tolerance=.11)
        with self.assertRaises(ValueError):
            charts.waterfall('nan', ['a', 'total'], [float('nan'), 1], 'unit', 'synthetic')

    def test_chart_cutoff_is_required_and_applied(self):
        charts = chartkit.Charts(self.run, font=str(VERA))
        csv = self.run / 'synthetic.csv'; csv.write_text('date,close\n2020-01-01,1\n2030-01-01,2\n', encoding='utf-8')
        with self.assertRaises(TypeError): charts.price('price', csv, 'synthetic')
        def inspect(id, fig, source):
            self.assertEqual(len(fig.axes[0].lines[0].get_xdata()), 1)
            plt.close(fig)
        with mock.patch.object(charts, 'save', side_effect=inspect):
            charts.price('price', csv, 'synthetic', last='2025-01-01')

    def test_chart_font_environment_and_missing_glyph_failure(self):
        with mock.patch.dict(os.environ, {'AIR_CHART_FONT': str(VERA)}):
            charts = chartkit.Charts(self.run)
        self.assertEqual(Path(charts.font), VERA)
        with self.assertRaisesRegex(ValueError, 'AIR_CHART_FONT'):
            charts.bars('missing-cjk', ['中文'], [1], 'unit', 'synthetic')


if __name__ == '__main__':
    unittest.main()
