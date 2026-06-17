import urllib.request
import json
import os
import time
from urllib.error import HTTPError, URLError

def get_wheel_url():
    print("Fetching metadata from PyPI...")
    req = urllib.request.Request('https://pypi.org/pypi/tensorflow/2.21.0/json')
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for file in data['urls']:
            if 'cp311-cp311-win_amd64.whl' in file['filename']:
                return file['url'], file['filename']
    return None, None

url, filename = get_wheel_url()
if not url:
    print("Could not find the wheel!")
    exit(1)

print(f"Found URL: {url}")
while True:
    if os.path.exists(filename):
        downloaded_size = os.path.getsize(filename)
    else:
        downloaded_size = 0

    print(f"Downloading {filename} starting at {downloaded_size} bytes...")
    req = urllib.request.Request(url)
    if downloaded_size > 0:
        req.add_header('Range', f'bytes={downloaded_size}-')
        
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            with open(filename, 'ab') as f:
                while True:
                    chunk = response.read(1024 * 1024) # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded_size += len(chunk)
        print("Download complete!")
        break
    except HTTPError as e:
        if e.code == 416: # Range Not Satisfiable
            print("Already downloaded completely!")
            break
        print(f"HTTP Error {e.code}: {e.reason}. Retrying...")
        time.sleep(2)
    except Exception as e:
        print(f"Connection dropped at {downloaded_size} bytes: {e}. Reconnecting in 2 seconds...")
        time.sleep(2)
