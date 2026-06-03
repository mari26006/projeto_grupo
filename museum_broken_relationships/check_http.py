import urllib.request
paths = ['http://127.0.0.1:5000/', 'http://127.0.0.1:5000/static/css/style.css']
for p in paths:
    try:
        with urllib.request.urlopen(p) as r:
            data = r.read().decode('utf-8', errors='replace')
            print('PATH', p)
            print(data[:240].replace('\n', ' '))
            print('-----')
    except Exception as e:
        print('ERROR', p, e)
