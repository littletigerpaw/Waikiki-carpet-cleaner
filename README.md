# Waikiki Carpet Cleaners — Task Manager

Task management app for an Airbnb / vacation-rental cleaning company.

- **Frontend:** React + Vite + TypeScript + React Router (`frontend/`)
- **Backend:** Python Flask + SQLAlchemy + SQLite + JWT auth (`backend/`)

## Run it (two terminals)

**Terminal 1 — backend (http://localhost:5001)**
```bash
cd backend
source venv/bin/activate          # first time: python3 -m venv venv && pip install -r requirements.txt
python seed.py                    # resets DB with demo users/tasks
python app.py
```

**Terminal 2 — frontend (http://localhost:5173)**
```bash
cd frontend
npm install                       # first time only
npm run dev
```
Vite proxies `/api/*` to Flask, so no CORS setup is needed in dev.

## Testing on a phone
The dev server listens on your network. Put the phone on the same Wi-Fi as your computer and open
`http://<your-computer-ip>:5173` (Vite prints this as the "Network" URL when you run `npm run dev`).

## Demo logins
| Portal   | Email                 | Password    |
|----------|-----------------------|-------------|
| Manager  | manager@waikiki.com   | manager123  |
| Employee | leilani@waikiki.com   | employee123 |
| Employee | noah@waikiki.com      | employee123 |

## API
| Method | Route                          | Who       |
|--------|--------------------------------|-----------|
| POST   | /api/auth/login                | anyone    |
| GET    | /api/auth/me                   | logged in |
| POST   | /api/auth/change-password      | logged in |
| GET    | /api/manager/dashboard         | manager   |
| POST   | /api/manager/employees         | manager   |
| PATCH  | /api/manager/employees/:id     | manager (`{"is_active": false}` deactivates) |
| POST   | /api/manager/tasks             | manager   |
| PATCH  | /api/manager/tasks/:id         | manager (edit / reassign) |
| DELETE | /api/manager/tasks/:id         | manager   |
| GET    | /api/employee/tasks            | employee  |
| PATCH  | /api/employee/tasks/:id        | employee  |
| POST   | /api/employee/tasks/:id/photos | employee (multipart, field `photos`) |
| DELETE | /api/employee/tasks/:id/photos/:photoId | employee |
| GET    | /api/uploads/:filename         | public (random filenames) |

Uploaded photos are saved in `backend/uploads/` (10 MB per upload; png/jpg/gif/webp/heic).
