import os
import app
print('cwd', os.getcwd())
print('appfile', app.__file__)
print('static_folder', app.app.static_folder)
print('static_exists', os.path.exists(app.app.static_folder))
print('static_files', os.listdir(app.app.static_folder))
css_path = os.path.join(app.app.static_folder, 'css', 'style.css')
print('css_path', css_path, os.path.exists(css_path))
with open(css_path, 'r', encoding='utf-8') as f:
    print('first line', f.readline().strip())
    for _ in range(10):
        print(f.readline().strip())
