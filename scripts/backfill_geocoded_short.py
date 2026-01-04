"""Backfill script: populate geocoded_short for boarding services that have
latitude/longitude but no geocoded_short. Uses Nominatim directly.

Run:
    python scripts/backfill_geocoded_short.py
"""
import sqlite3
import requests

DB = 'instance/petboarding.db'

def short_from_address(addr, full_display=None):
    locality_keys = ["city", "town", "village", "municipality", "hamlet"]
    suburb_keys = ["suburb", "quarter", "neighbourhood", "locality"]

    locality = None
    for k in locality_keys:
        if addr.get(k):
            locality = addr.get(k)
            break

    suburb = None
    for k in suburb_keys:
        if addr.get(k):
            suburb = addr.get(k)
            break

    if suburb and locality:
        return f"{suburb}, {locality}"
    if locality:
        return locality
    if suburb:
        return suburb

    if addr.get('county') and addr.get('postcode'):
        return f"{addr.get('county')} ({addr.get('postcode')})"
    if addr.get('county'):
        return addr.get('county')
    if addr.get('state'):
        return addr.get('state')
    if addr.get('postcode'):
        return addr.get('postcode')
    return full_display


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT id, latitude, longitude, geocoded_name, geocoded_short FROM boarding_services WHERE (geocoded_short IS NULL OR geocoded_short='') AND latitude IS NOT NULL AND longitude IS NOT NULL")
    rows = cur.fetchall()

    if not rows:
        print('Nothing to update')
        return

    print(f'Found {len(rows)} services to backfill')

    headers = { 'User-Agent': 'SafePaws/1.0' }

    for sid, lat, lon, full, short in rows:
        try:
            r = requests.get('https://nominatim.openstreetmap.org/reverse', params={'format':'json','lat':lat,'lon':lon,'zoom':18,'addressdetails':1}, headers=headers, timeout=10)
            r.raise_for_status()
            nd = r.json()
            addr = nd.get('address') or {}
            computed = short_from_address(addr, nd.get('display_name'))
            if not computed:
                print(f'skipping {sid}, no computed value')
                continue
            cur.execute("UPDATE boarding_services SET geocoded_short=? WHERE id=?", (computed, sid))
            conn.commit()
            print(f'Updated {sid} -> {computed}')
        except Exception as e:
            print('Failed for', sid, e)

    conn.close()

if __name__ == '__main__':
    main()
