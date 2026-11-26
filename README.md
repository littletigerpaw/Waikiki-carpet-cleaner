# Waikiki Carpet Cleaners — Task Manager

[![CI](https://github.com/littletigerpaw/Waikiki-carpet-cleaner/actions/workflows/ci.yml/badge.svg)](https://github.com/littletigerpaw/Waikiki-carpet-cleaner/actions/workflows/ci.yml)

Task management app for an Airbnb / vacation-rental cleaning company. Managers schedule
cleanings and manage the team; employees see their assignments, update status, and upload
photos of finished units straight from their phone camera.

| Layer    | Tech |
|----------|------|
| Frontend | React, Vite, TypeScript, React Router, Vitest + Testing Library |
| Backend  | Python, Flask, SQLAlchemy, Flask-Migrate (Alembic), JWT auth, pytest |
| Database | SQLite (local) · PostgreSQL on Neon (production) |
| Photos   | Local `uploads/` folder (local) · Firebase Storage (production) |
| Hosting  | Vercel services (React + Flask in one project, one domain) · GitHub Actions (CI + migrations) |

## Features
- Separate **manager** and **employee** login portals, hashed passwords, role-protected routes
- **Managers:** dashboard stats, schedule / edit / reassign / delete cleanings, filter tasks
  (search, status, employee, date range), add employees, deactivate / reactivate employees
- **Employees:** today's and upcoming cleanings, update status, take or upload photos
- **Everyone:** My Account page with password change

## Run locally (two terminals)

**Terminal 1 — backend (http://localhost:5001)**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # first time only
pip install -r requirements-dev.txt                 # first time only
cp .env.example .env                                # first time only
flask db upgrade                                    # create / update tables
python seed.py                                      # optional: reset to demo data
python app.py
```

**Terminal 2 — frontend (http://localhost:5173)**
```bash
cd frontend
npm install        # first time only
npm run dev
```
Vite proxies `/api/*` to Flask, so no CORS setup is needed in development.

### Demo logins (after `python seed.py`)
| Portal   | Email                 | Password    |
|----------|-----------------------|-------------|
| Manager  | manager@waikiki.com   | manager123  |
| Employee | leilani@waikiki.com   | employee123 |
| Employee | noah@waikiki.com      | employee123 |

### Testing on a phone
Put the phone on the same Wi-Fi as your computer and open the **Network** URL that
`npm run dev` prints (e.g. `http://192.168.1.20:5173`).

## Tests
```bash
cd backend && pytest          # API tests: auth, permissions, tasks, photos, Firebase storage, config
cd frontend && npm test       # login page, route guards, API client, photo compression
```
GitHub Actions runs both suites, lint, a type-checked build, and a migration check on every push.
On pushes to `main` it then applies migrations to the production database.

## Database changes (migrations)
After editing `backend/models.py`:
```bash
cd backend
flask db migrate -m "describe the change"   # generates a file in migrations/versions/
flask db upgrade                            # applies it
```
Commit the new migration file. When you push to `main`, GitHub Actions applies it to the
production database (once the `DATABASE_URL` secret is set, see below).

## Deploy (Vercel + Neon + Firebase Storage)

```
Browser ──► Vercel project (one domain, two services from vercel.json)
              ├── /api/*  → "backend" service  (Flask, backend/app.py)
              │                ├─► Neon PostgreSQL   (users, tasks)
              │                └─► Firebase Storage  (photos)
              └── /*      → "frontend" service (Vite build of frontend/,
                                                unknown paths → index.html)
```
Flask receives the full path (e.g. `/api/auth/login`), which is why every route starts with `/api`.
The browser calls `/api/...` on the same domain, so there's no CORS and no API URL to configure.

### 1. Firebase Storage (photos)
1. [console.firebase.google.com](https://console.firebase.google.com) → **Add project**.
2. **Build → Storage → Get started** (production mode is fine; the server uses an admin key).
   Copy the bucket name shown at the top, e.g. `your-project.firebasestorage.app`.
   *Newer Firebase projects need the pay-as-you-go **Blaze** plan to use Storage. It has a
   free allowance (about 5 GB), so a small company normally pays $0; set a budget alert anyway.*
3. **Project settings (⚙) → Service accounts → Generate new private key**. A JSON file downloads.
   Treat it like a password: never commit it or share it.

### 2. Vercel project (site + API)
1. [vercel.com](https://vercel.com) → **Add New → Project** → import this GitHub repo.
   Leave **Root Directory** as the repo root: `vercel.json` defines the two services.
2. **Storage → Create Database → Neon (Postgres)** and connect it to the project.
   This adds `DATABASE_URL` automatically.
3. **Settings → Environment Variables** (Production), add:
   | Name | Value |
   |------|-------|
   | `SECRET_KEY` | output of `python3 -c "import secrets; print(secrets.token_hex(32))"` |
   | `FIREBASE_STORAGE_BUCKET` | bucket name from step 1.2 |
   | `FIREBASE_SERVICE_ACCOUNT` | paste the **entire contents** of the JSON file from step 1.3 |
4. **Deployments → Redeploy** so the new variables take effect.

### 3. Create the tables and your manager login (one time, from your computer)
Copy the Neon connection string (Vercel → Storage → your database → `DATABASE_URL`), then:
```bash
cd backend && source venv/bin/activate
export DATABASE_URL="postgresql://...your Neon URL..."
flask db upgrade          # creates the tables in Neon
flask create-manager      # prompts for name, email, password
unset DATABASE_URL        # back to your local SQLite database
```

### 4. Automatic migrations (optional, recommended)
GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:
`DATABASE_URL` = the same Neon connection string. From then on, every push to `main` that
passes the tests also runs `flask db upgrade` on production.

### 5. Check it
- `https://<your-app>.vercel.app/api/health` → `{"status": "ok"}`
- Log in as your manager, add an employee, log in as them on a phone, take a photo.

> **Notes**
> - Photos are shrunk in the browser (max 2000px JPEG) before upload, because Vercel limits
>   each request to 4.5 MB. Multiple photos upload one at a time.
> - Photo links contain a random token: anyone with the exact link can view the photo,
>   but links can't be guessed.
> - Vercel and Neon free tiers suit a small team. Neon's free database pauses when idle,
>   so the first request after a quiet period can take a second or two.

## API
| Method | Route                                   | Who |
|--------|-----------------------------------------|-----|
| POST   | /api/auth/login                         | anyone |
| GET    | /api/auth/me                            | logged in |
| POST   | /api/auth/change-password               | logged in |
| GET    | /api/manager/dashboard                  | manager |
| POST   | /api/manager/employees                  | manager |
| PATCH  | /api/manager/employees/:id              | manager (`{"is_active": false}` deactivates) |
| POST   | /api/manager/tasks                      | manager |
| PATCH  | /api/manager/tasks/:id                  | manager (edit / reassign) |
| DELETE | /api/manager/tasks/:id                  | manager |
| GET    | /api/employee/tasks                     | employee |
| PATCH  | /api/employee/tasks/:id                 | employee (status) |
| POST   | /api/employee/tasks/:id/photos          | employee (multipart, field `photos`) |
| DELETE | /api/employee/tasks/:id/photos/:photoId | employee |
| GET    | /api/uploads/:filename                  | local dev photo storage only |
| GET    | /api/health                             | health check |

## Useful commands
```bash
flask create-manager      # add a manager (set DATABASE_URL to target production)
flask db upgrade          # apply migrations (same)
```
