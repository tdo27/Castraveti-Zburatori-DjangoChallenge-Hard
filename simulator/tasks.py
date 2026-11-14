"""
Task-urile de background pentru varianta Hard.

Fluxul:
  register_people  ->  GET /people, salvează cele 100 de persoane
                   ->  cheia lui Hellstorm Fireburn ("draft-info") -> fetch_instructions
  download_batch(0) -> GET /draft/0
        |-> process_batch(lot)      (task separat, pornește imediat)
        |-> download_batch(x)       (lotul următor, cât timp există "x")
  process_batch    ->  setează rank-ul; noua cheie a lui Hellstorm -> fetch_instructions
"""
import logging

import requests
from celery import shared_task
from django.conf import settings
from django.db.utils import OperationalError

from .models import Instruction, Person

logger = logging.getLogger(__name__)

HELLSTORM = 'Hellstorm Fireburn'
BASE_FIELDS = ('id', 'name', 'age')

# Serverul e lent intenționat și poate da timeout -> reîncercăm cu backoff exponențial.
NETWORK_RETRY = dict(
    autoretry_for=(requests.RequestException, OperationalError),
    retry_backoff=True,        # 1s, 2s, 4s, 8s ...
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=10,
)
# SQLite permite un singur scriitor; dacă baza e ocupată, reîncercăm.
DB_RETRY = dict(
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=10,
)

# Atributul cu lotul următor ("x" în instrucțiuni); acceptăm și alte denumiri uzuale.
NEXT_KEYS = ('x', 'next', 'next_batch', 'nextBatch', 'next_id', 'cursor')


def fetch(path):
    """GET pe server; întoarce TOT răspunsul JSON (nu doar 'data')."""
    response = requests.get(f"{settings.WAR_API_HOST}/{path}", timeout=(5, 60))
    response.raise_for_status()
    return response.json()


def find_next(body):
    """Caută atributul cu lotul următor, lângă 'data' sau în interiorul lui."""
    places = [body]
    if isinstance(body.get('data'), dict):
        places.append(body['data'])
    for place in places:
        for key in NEXT_KEYS:
            if place.get(key) not in (None, ''):
                return place[key]
    return None


def extract_people(data):
    """Lista de persoane dintr-un lot, fie că 'data' e listă, fie dict cu o listă."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
    return []


def check_hellstorm(person):
    """Hellstorm Fireburn are o cheie care duce la instrucțiunile etapei următoare."""
    if person.get('name') == HELLSTORM and person.get('key'):
        fetch_instructions.delay(person['key'])


# --------------------------------------------------------------------------
# Etapa 1: înregistrarea persoanelor (peacetime)
# --------------------------------------------------------------------------

@shared_task(**NETWORK_RETRY)
def register_people():
    people = fetch('people')['data']
    Person.objects.bulk_create(
        [
            Person(
                external_id=p['id'],
                name=p['name'],
                age=p['age'],
                extra={k: v for k, v in p.items() if k not in BASE_FIELDS},
            )
            for p in people
        ],
        update_conflicts=True,
        unique_fields=['external_id'],
        update_fields=['name', 'age', 'extra'],
    )
    for p in people:
        check_hellstorm(p)
    logger.info('Registered %s people', len(people))
    return len(people)


@shared_task(**NETWORK_RETRY)
def fetch_instructions(key):
    body = fetch(key)
    Instruction.objects.update_or_create(key=key, defaults={'content': body.get('data', body)})
    logger.info('Saved instructions from /%s', key)
    return key


# --------------------------------------------------------------------------
# Etapa 2: draftul, câte un task pentru fiecare lot
# --------------------------------------------------------------------------

@shared_task(**NETWORK_RETRY)
def download_batch(batch_id=0):
    body = fetch(f'draft/{batch_id}')
    people = extract_people(body.get('data'))

    # 1) lotul descărcat e procesat imediat, într-un task separat (în paralel)
    process_batch.delay(people)

    # 2) descărcarea continuă cu lotul următor, cât timp serverul ne dă "x"
    next_id = find_next(body)
    if next_id is not None and str(next_id) != str(batch_id):
        download_batch.delay(next_id)

    logger.info('Batch %s: %s people, next=%s, keys=%s', batch_id, len(people), next_id, list(body))
    return {'batch': batch_id, 'people': len(people), 'next': next_id, 'keys': list(body)}


@shared_task(**DB_RETRY)
def process_batch(people):
    for p in people:
        Person.objects.update_or_create(
            external_id=p['id'],
            defaults={
                'name': p.get('name', ''),
                'age': p.get('age', 0),
                'rank': p.get('rank'),
                'extra': {k: v for k, v in p.items() if k not in BASE_FIELDS + ('rank',)},
            },
        )
        check_hellstorm(p)
    return len(people)
