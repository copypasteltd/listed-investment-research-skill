"""System font candidates only. No fonts or font licences are bundled."""
from pathlib import Path
import os


def candidates(role='body'):
    windows = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    if role == 'body':
        names = [windows / 'simsun.ttc', windows / 'msyh.ttc']
        linux = ['NotoSerifCJK-Regular.ttc', 'NotoSansCJK-Regular.ttc']
    else:
        names = [windows / 'msyhbd.ttc', windows / 'msyh.ttc', windows / 'simsun.ttc']
        linux = ['NotoSansCJK-Bold.ttc', 'NotoSerifCJK-Bold.ttc',
                 'NotoSerifCJK-Regular.ttc', 'NotoSansCJK-Regular.ttc']
    for root in ('/usr/share/fonts/opentype/noto', '/usr/share/fonts/truetype/noto',
                 '/usr/local/share/fonts', str(Path.home() / '.local/share/fonts')):
        names.extend(Path(root) / name for name in linux)
    names.extend([Path('/System/Library/Fonts/PingFang.ttc'),
                  Path('/System/Library/Fonts/STHeiti Light.ttc')])
    if role == 'body':
        names += [Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'), windows / 'arial.ttf']
    else:
        names += [Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'), windows / 'arialbd.ttf']
    return names


def missing_message(role, detail=''):
    option = '--font-body / --font-head' if role in ('body', 'head') else 'Charts(run, font=PATH)'
    environment = 'AIR_FONT_BODY / AIR_FONT_HEAD' if role in ('body', 'head') else 'AIR_CHART_FONT'
    return (f'No usable font for {role}. {detail} Supply a licensed TTF/TTC using {option} '
            f'or {environment}. For Chinese, install Noto CJK (for example fonts-noto-cjk) '
            'or point to a CJK TrueType font. Some Noto CJK TTC files use CFF outlines '
            'unsupported by ReportLab; use a compatible TrueType CJK font in that case. '
            'DejaVu is an English fallback only; it cannot render Chinese correctly.')
