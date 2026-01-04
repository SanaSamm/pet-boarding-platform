from app import create_app
from db import db
from models.provider import ProviderModel
from models.service import BoardingServiceModel

app = create_app()
with app.app_context():
    print('Providers:')
    for p in ProviderModel.query.all():
        print(f'  id={p.id} name={p.name!r} bio={bool(p.bio)} photo_url={bool(p.photo_url)} services_offered={p.services_offered}')

    print('\nServices:')
    for s in BoardingServiceModel.query.all():
        print(f'  id={s.id} name={s.name!r} provider_id={s.provider_id} services_provided={s.services_provided} capacity={s.capacity}')

    # check referential integrity
    print('\nServices without provider:')
    for s in BoardingServiceModel.query.all():
        if s.provider is None:
            print(f'  id={s.id} name={s.name!r} provider_id={s.provider_id}')

    print('\nDone')