# Django War Simulator (Hard)

Proiect pentru CodeRun 2026, construit pe starter-ul `imimali/coderun2026-starter`.
Conține toate cerințele variantei Easy plus partea Hard (înregistrarea și draftul în background, cu Celery).

## Pornire

```bash
pip install -r requirements.txt
python manage.py migrate
```

Apoi, în **două terminale separate**:

```bash
# Terminal 1: aplicația web
python manage.py runserver

# Terminal 2: worker-ul Celery (rulează task-urile de background)
celery -A coderun2026_starter worker -l info
```

Dacă modifici `simulator/tasks.py`, repornește worker-ul (Ctrl+C și pornești din nou), pentru că Celery nu reîncarcă singur codul.

## Pagini

| URL | Ce face |
|---|---|
| `/unit` | formularul de adăugare a unei unități (Easy 1) |
| `/unit/all` | lista unităților, Heal, Simulate și statisticile pe echipe (Easy 2, 3, 4b) |
| `/unit/<id>` | detaliile unei unități și istoricul fiecărei lupte (Easy 2, 4a) |
| `/people` | Draft Office: înregistrarea persoanelor și draftul (Hard) |
| `/admin` | admin-ul Django (`python manage.py createsuperuser`) |

## Varianta Hard: cum funcționează

1. **Register people** pornește task-ul `register_people`, care descarcă `/people` și salvează cele 100 de persoane.
   Persoana *Hellstorm Fireburn* are `key = "draft-info"`. Task-ul `fetch_instructions` descarcă de acolo instrucțiunile pentru draft, iar ele apar pe pagină.
2. **Start draft** pornește `download_batch(0)`:
   - descarcă `/draft/0`;
   - **pornește imediat** `process_batch` pentru lotul descărcat, ca task separat, care setează `rank` pentru fiecare persoană;
   - continuă cu `/draft/x` (atributul `x` din răspuns) cât timp mai există loturi.

   Descărcarea e secvențială, pentru că abia din lotul curent afli lotul următor. Procesarea loturilor rulează însă **în paralel**, pe 16 thread-uri (`CELERY_WORKER_CONCURRENCY`).
3. **Retry**: task-urile de rețea se reîncearcă automat la timeout sau la erori HTTP, cu backoff exponențial (până la 10 încercări, maximum 60 s între ele). Task-urile care scriu în baza de date se reîncearcă dacă SQLite e ocupat.
4. **Migrare**: câmpul `rank` e adăugat printr-o migrare separată, `simulator/migrations/0002_person_rank.py`.
5. Când draftul ajunge la Hellstorm Fireburn, noua lui cheie e urmată automat, iar instrucțiunile etapei următoare apar pe `/people`.

## Structura

```
coderun2026_starter/   settings, urls, celery.py
simulator/
    models.py          Unit, Fight, FightStep (Easy) · Person, Instruction (Hard)
    forms.py           UnitForm
    views.py           paginile Easy + Draft Office
    tasks.py           task-urile Celery (register, draft, retry)
    migrations/        0001_initial, 0002_person_rank
templates/simulator/   base, unit_form, unit_list, unit_detail, people
```
