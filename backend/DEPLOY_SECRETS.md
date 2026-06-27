# Secrets & deployment configuration

`backend/.env` and `backend/.env.production` are **no longer tracked in git**
(only `.env.example` is). Configure secrets through your host's environment
(e.g. the Render dashboard → Environment), never by committing them.

## ⚠️ Rotate leaked credentials

These values were previously committed and **still exist in git history**, so
treat them as compromised and rotate them:

1. **Supabase database password** — reset it in Supabase (Project → Database →
   Reset password) and update `DATABASE_URL` in your host env.
2. **`SECRET_KEY` / `JWT_SECRET_KEY`** — generate fresh values
   (`python -c "import secrets; print(secrets.token_urlsafe(48))"`).
3. **`RESEND_API_KEY`** and any other provider keys.
4. **Admin password** — change it after first login (see below).

Untracking the files does not remove them from history; rotation is what makes
the old values useless. (A history rewrite is possible but destructive on a
shared branch, so rotation is the recommended fix.)

## Required environment variables

Set these in the host dashboard (see `.env.example` for the full list):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection (`postgresql+asyncpg://…`) |
| `SECRET_KEY`, `JWT_SECRET_KEY` | App + JWT signing secrets |
| `RESEND_API_KEY`, `EMAIL_FROM` | Transactional email |
| `CORS_ORIGINS`, `SITE_BASE_URL` | Frontend origin(s) |
| `BOOTSTRAP_ADMIN_EMAIL` | First admin to create/promote on startup |
| `BOOTSTRAP_ADMIN_PASSWORD` | Password for a new bootstrap admin |
| `BOOTSTRAP_ADMIN_USERNAME` | (optional) username for the bootstrap admin |

## Creating the first admin

Set the bootstrap vars in the host env and (re)deploy this branch — the app
creates/promotes `BOOTSTRAP_ADMIN_EMAIL` to `Overall_Admin` on startup
(idempotent). Then **clear `BOOTSTRAP_ADMIN_*`** and rotate the password.

Alternative (shell on the server):

```bash
python -m scripts.create_admin --email you@domain.com --password '<strong>' --username owner
```

After the first admin exists, manage all other roles in-app: Admin → Users.
