import hashlib
import hmac
import requests
import time

# FROM: https://pusher.com/docs/rest_api#authentication

# Configuration
JSON_HEADER = {'Content-type': 'application/json'}
API = '/apps/110855/events'
URL = 'http://api.pusherapp.com'+API
SECRET='8440acd6ba1e0bfec3d4'

def get_md5_hash(s):
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()

def get_sha256(s):
    m = hmac.new(SECRET, s, hashlib.sha256)
    return m.hexdigest()

payload = r'{"name": "client-button-pushed", "data": "{\"user_id\": \"test_rest_API\", \"value\": \"4\"}", "channel": "presence-moodies"}'
params= [
    'auth_key=2c987384b72778026687',
    'auth_timestamp={}'.format(int(time.time())),
    'auth_version=1.0',
    'body_md5={}'.format(get_md5_hash(payload)).encode('utf-8')
]

sig = get_sha256('POST\n{}\n{}'.format(API,'&'.join(params)))
params.append('auth_signature={}'.format(sig))

url = URL+'?'+'&'.join(params)

r = requests.post(url, data=payload, headers=JSON_HEADER)
print r
print r.text
