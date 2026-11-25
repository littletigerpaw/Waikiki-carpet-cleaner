# Waikiki Carpet Cleaners — Task Manager

[![CI](https://github.com/littletigerpaw/Waikiki-carpet-cleaner/actions/workflows/ci.yml/badge.svg)](https://github.com/littletigerpaw/Waikiki-carpet-cleaner/actions/workflows/ci.yml)

Task management app for an Airbnb / vacation-rental cleaning company. Managers schedule
cleanings and manage the team; employees see their assignments, update status, and upload
photos of finished units straight from their phone camera.

| Layer    | Tech |
|----------|------|
| Frontend | React, Vite, TypeScript, React Router, Vitest + Testing Library |
| Backend  | Python, Flask, SQLAlchemy, Flask-Migrate (Alembic), JWT auth, pytest |
| Database | SQLite (local) · PostgreSQL (production) |
| Photos   | Local `uploads/` folder (local) · Cloudinary (production) |
| Hosting  | Render (API + Postgres) · Netlify (frontend) · GitHub Actions (CI) |

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
cd backend && pytest          # 54 API tests (auth, permissions, tasks, photos, config)
cd frontend && npm test       # login page, route guards, API client
```
GitHub Actions runs both suites, lint, a type-checked build, and a migration check on every push.

## Database changes (migrations)
After editing `backend/models.py`:
```bash
cd backend
flask db migrate -m "describe the change"   # generates a file in migrations/versions/
flask db upgrade                            # applies it
```
Commit the new migration file. Production applies it automatically on the next deploy.

## Deploy

### 1. Cloudinary (photo storage, free)
Sign up at cloudinary.com and copy the **API environment variable**
(`cloudinary://<key>:<secret>@<cloud-name>`) from the dashboard.

### 2. Backend + database on Render
1. Render dashboard → **New → Blueprint** → choose this repo (it reads `render.yaml`).
2. Fill in the prompted values:
   - `CLOUDINARY_URL` — from step 1
   - `INITIAL_MANAGER_EMAIL` / `INITIAL_MANAGER_PASSWORD` — your first manager login
   - `FRONTEND_ORIGIN` — put a placeholder for now; update it after step 3
3. When it's live, note the API URL (e.g. `https://waikiki-api.onrender.com`) and check
   `https://…onrender.com/api/health` returns `{"status": "ok"}`.

### 3. Frontend on Netlify
1. Netlify → **Add new site → Import from Git** → choose this repo (it reads `netlify.toml`).
2. Site configuration → Environment variables → add `VITE_API_URL` = your Render API URL.
3. Deploy, then copy the site URL (e.g. `https://waikiki-cleaners.netlify.app`).

### 4. Connect them
In Render, set `FRONTEND_ORIGIN` to the Netlify URL (no trailing slash) and save
(Render redeploys). Log in as the manager, change the password on **My Account**, then
delete `INITIAL_MANAGER_PASSWORD` from Render.

> Free-tier notes: Render's free web service sleeps after ~15 min idle (first request takes
> ~30–60 s), and Render's free Postgres database expires after 30 days. Upgrade either when
> the company starts relying on it.

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
| GET    | /api/uploads/:filename                  | local dev photo storage |
| GET    | /api/health                             | health check |

## Useful commands
```bash
flask create-manager      # add another manager interactively
flask ensure-manager      # create first manager from INITIAL_MANAGER_* env vars
```
