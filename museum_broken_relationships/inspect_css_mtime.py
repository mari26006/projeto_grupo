from pathlib import Path
p = Path('static/css/style.css').resolve()
print('path', p)
print('mtime', p.stat().st_mtime)
print('text start', p.read_text(encoding='utf-8')[:240])
