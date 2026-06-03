import urllib.request
for p in ['http://127.0.0.1:5000/static/css/style.css']:
    req = urllib.request.Request(p)
    with urllib.request.urlopen(req) as r:
        print('STATUS', r.status)
        print('HEADERS')
        for k, v in r.getheaders():
            if k.lower() in ('last-modified', 'etag', 'cache-control', 'content-type'):
                print(k+':', v)
        data = r.read().decode('utf-8', errors='replace')
        idx = data.find(':root')
        print('ROOT idx', idx)
        print(data[idx:idx+240].replace('\n',' '))
        print('---')
