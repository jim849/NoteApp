# NotesApp

A small grades application used throughout the Computer Security course. Teachers
record grades and comments for their classes, students read their own grades, and an
admin manages users and classes.

## Run it

You need Docker with the Compose plugin. Clone your own fork and enter its directory:

```
cd notesapp
```

Copy `.env.example` to `.env` if you do not already have a local `.env`. Generate a
secret with `openssl rand -hex 32` and set `EXPORT_HMAC_KEY` in `.env` to that value.
Keep this key stable so previously exported files remain verifiable. `.env` is
excluded from Git.

Then start the app:

```
docker compose up --build -d
```

The first start builds the image, launches PostgreSQL, and loads the seed data
automatically. When it is ready, open:

```
http://localhost:8080
```

## Test accounts

| Role    | Username      | Password   |
|---------|---------------|------------|
| Student | `alice`       | `alicepw`  |
| Teacher | `prof.turing` | `teach123` |
| Admin   | `admin`       | `admin123` |

(There are ~30 students in total; each student's password is their username + `pw`,
e.g. `bob` / `bobpw`.)

## Stack

- Python 3.11 + Flask (server-rendered Jinja2 pages and a small JSON API)
- PostgreSQL 15
- Docker Compose (`web` and `db` services)

## Classes 4 and 5: signed grade exports

Teacher CSV exports end with `# HMAC: <hex digest>`. The server computes
HMAC-SHA256 over the exact UTF-8 CSV bytes, excluding that final line, using the
separate `EXPORT_HMAC_KEY` secret.

Sign in as a teacher, click **export CSV**, and save the downloaded file as
`hmac_demo/grades_original.csv` in this project. Create the `hmac_demo` directory
first if needed. Verify it inside the server container:

```
docker compose exec -T web python /host/verify_export.py /host/hmac_demo/grades_original.csv
```

Copy the file to `hmac_demo/grades_tampered.csv`, edit one grade using a text editor,
and preserve the HMAC line. Verify the copy:

```
docker compose exec -T web python /host/verify_export.py /host/hmac_demo/grades_tampered.csv
```

The original prints `CHECK PASSED` and exits with code 0. The edited copy prints
`CHECK FAILED` and exits with code 1. Configuration or file errors exit with code 2.
Verification is a server-side command; there is no browser upload/verification form.
HMAC detects changes but does not encrypt the grades.

## HTTPS lab

Generate a local self-signed certificate and private key (requires OpenSSL):

```
mkdir -p nginx/certs
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -config nginx/localhost-cert.cnf -keyout nginx/certs/notesapp.key -out nginx/certs/notesapp.crt
```

If you already have a matching local certificate and key, keep them instead of
regenerating them. Both generated files are excluded from Git.

Start the HTTPS configuration:

```
docker compose -f docker-compose.yml -f docker-compose.https.yml up --build -d
```

Open `https://localhost`. Nginx terminates TLS and redirects port 80 to HTTPS.
The self-signed certificate is not trusted by default, so the browser's certificate
warning is an expected part of the lab. The HTTP-only configuration remains available
with `docker compose up --build -d` on port 8080.

## Password storage and dictionary attack lab

New accounts created by the admin store Argon2 hashes. Existing plaintext accounts
are migrated after a successful login; accounts that have not logged in still retain
their seed passwords. Login looks up the username with a parameterized SQL query and
checks Argon2 hashes with `argon2-cffi`.

The `crack` directory contains a separate dictionary attack exercise using synthetic
accounts and deliberately weak MD5 hashes. It does not read the NotesApp database.
From the project root, run:

```
python3 crack/make_dump.py
python3 crack/crack.py
```

The exercise illustrates why fast, unsalted MD5 hashes are unsuitable for password
storage. It is independent of the app's Argon2 implementation.

## Reset

```
docker compose down -v   # wipes the database volume
docker compose up        # reloads the seed data
```

## Updating your fork

The course repository is sometimes updated. Your fork does **not** update by itself.
To pull the latest changes into your fork:

**Easiest (GitHub website):** open your fork, and if it says *"This branch is behind
KristenPire/NoteApp"*, click **Sync fork → Update branch**. Then, in your local clone:

```
git pull
```

**Command line (keeps your own commits):**

```
git remote add upstream https://github.com/KristenPire/NoteApp.git   # once
git fetch upstream
git merge upstream/main
git push
```

Then **rebuild**, because the app code is baked into the Docker image:

```
docker compose up --build
```

A plain `docker compose up` would keep running the old image.
