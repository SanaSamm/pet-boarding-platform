import sys
sys.path.insert(0, r'c:\Users\samma\pet-boarding-platform')
from app import create_app

app = create_app()
with app.test_client() as c:
    resp = c.get('/providers/1')
    print('status', resp.status_code)
    print('data', resp.get_data(as_text=True))
