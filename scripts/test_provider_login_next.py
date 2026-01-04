"""Simple tests for provider login response `next` behavior.

These are lightweight smoke tests that can be run locally to validate
that provider login returns a `next` field pointing to the right place
for new providers (no services) and providers with services.

Run with: python scripts/test_provider_login_next.py
"""

import requests
from pprint import pprint

BASE = "http://localhost:5000"

# Credentials used by tests (ensure these exist in your dev DB)
NEW_PROVIDER = {"email": "new_provider@example.com", "password": "password"}
EXISTING_PROVIDER = {"email": "provider@example.com", "password": "password"}


def login_and_print(creds):
    r = requests.post(BASE + '/provider/login', json=creds)
    print('Status:', r.status_code)
    try:
        j = r.json()
    except Exception:
        print('No JSON response')
        print(r.text)
        return
    pprint(j)


if __name__ == '__main__':
    print('\n== New provider (expected next: /offer-care) ==')
    login_and_print(NEW_PROVIDER)

    print('\n== Existing provider (expected next: /provider?id=...) ==')
    login_and_print(EXISTING_PROVIDER)
