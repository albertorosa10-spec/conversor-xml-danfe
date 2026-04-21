import urllib.request
import urllib.parse
import json
import time
import zipfile
import io

def multipart_post(url, filepaths):
    import uuid
    boundary = uuid.uuid4().hex
    data = []
    for fp in filepaths:
        data.append(f'--{boundary}'.encode())
        data.append(f'Content-Disposition: form-data; name="files"; filename="{fp.split("/")[-1]}"'.encode())
        data.append(b'Content-Type: application/xml')
        data.append(b'')
        with open(fp, 'rb') as f: data.append(f.read())
    data.append(f'--{boundary}--'.encode())
    data.append(b'')
    body = b'\r\n'.join(data)
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    try:
        res = urllib.request.urlopen(req)
        return res.status, res.headers, res.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()

print('--- 4.9 ---')
status, headers, body = multipart_post('http://localhost:8000/converter', ['backend/tests/fixtures/nfe_completa_com_protocolo.xml', 'backend/tests/fixtures/xml_malformado.xml', 'backend/tests/fixtures/cte_completo_com_protocolo.xml'])
print(f"X-Total-Processed: {headers.get('X-Total-Processed', '')}")
print(f"X-Total-Errors: {headers.get('X-Total-Errors', '')}")
if status == 200:
    with zipfile.ZipFile(io.BytesIO(body)) as z:
        print('ZIP contents:', z.namelist())
        print('--- 4.10 ---')
        print(z.read('_RELATORIO.txt').decode('utf-8'))
else:
    print('HTTP', status)

print('--- 4.11 ---')
for i in range(1, 7):
    s, h, b = multipart_post('http://localhost:8000/converter', ['backend/tests/fixtures/nfe_completa_com_protocolo.xml'])
    print(f'Req {i}: HTTP {s}')
