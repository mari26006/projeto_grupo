from pathlib import Path
p = Path('static/css/style.css').resolve()
print(p)
text = p.read_text(encoding='utf-8')
print(text[:360])
