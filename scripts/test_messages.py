"""Simple manual test script for messaging endpoints.

Run the server and then run this script to exercise the basic message flow.
"""
import requests

BASE = 'http://127.0.0.1:5000'

# Please ensure there is at least one owner and one provider registered.
# This script expects owners with emails owner@example.com and provider@example.com with password 'password'.

def login_as_owner():
    r = requests.post(BASE + '/owner/login', json={'email':'owner@example.com','password':'password'})
    return r.json().get('access_token')


def login_as_provider():
    r = requests.post(BASE + '/provider/login', json={'email':'provider@example.com','password':'password'})
    return r.json().get('access_token')


def main():
    owner_token = login_as_owner()
    provider_token = login_as_provider()
    print('owner_token', owner_token)
    print('provider_token', provider_token)

    # Create conversation
    headers = {'Authorization':'Bearer '+owner_token}
    resp = requests.post(BASE + '/conversations', json={'owner_id':1,'provider_id':1}, headers=headers)
    print('create convo', resp.status_code, resp.text)
    convo = resp.json()

    # Send message from owner
    resp = requests.post(BASE + f"/conversations/{convo['id']}/messages", json={'content':'Hello provider'}, headers=headers)
    print('send owner msg', resp.status_code, resp.text)

    # Send provider reply
    ph = {'Authorization':'Bearer '+provider_token}
    resp = requests.post(BASE + f"/conversations/{convo['id']}/messages", json={'content':'Hello owner, thanks!'}, headers=ph)
    print('provider reply', resp.status_code, resp.text)

    # Fetch messages
    resp = requests.get(BASE + f"/conversations/{convo['id']}/messages", headers=headers)
    print('messages', resp.status_code, resp.json())

if __name__ == '__main__':
    main()
