import requests
import json
token = None
basicAuthCredentials = requests.auth.HTTPBasicAuth('lakshman', 'harrypotter')
response = requests.get('http://localhost:9997/authenticate', auth=basicAuthCredentials)
if response.status_code == 200:
    token = json.loads(response.text)["token"]
response = requests.get('http://localhost:9997/getalltransactions', headers={"x-access-token":token} )
if response.status_code == 200:
    data = json.loads(response.text)
    print(data)