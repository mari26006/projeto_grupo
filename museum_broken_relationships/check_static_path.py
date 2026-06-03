import app, os
print('appfile', app.__file__)
print('static_folder', app.app.static_folder)
print('exists', os.path.exists(app.app.static_folder))
print('files', os.listdir(app.app.static_folder))
path = os.path.join(app.app.static_folder, 'css', 'style.css')
print('css path', path, os.path.exists(path))
with open(path, 'r', encoding='utf-8') as f:
    for _ in range(12):
        print(f.readline().rstrip())
