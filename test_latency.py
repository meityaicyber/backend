import requests
import time
import uuid

url = 'http://localhost:3000/api/reports/upload'

def upload_file(filepath):
    start = time.time()
    try:
        with open(filepath, 'rb') as f:
            res = requests.post(
                url,
                files={'file': (filepath.split('/')[-1], f, 'application/pdf')}
            )
        end = time.time()
        print(f"Status: {res.status_code}")
        print(f"Latency: {end - start:.2f}s")
        if res.status_code == 200:
            print("Response:", res.json())
        else:
            print("Error:", res.text)
    except Exception as e:
        print(f"Exception: {e}")

print("Measuring latency for a file...")
upload_file('test_reports/unencrypted_report.pdf')
