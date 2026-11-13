---
name: deploy
description: Ship SeeWord to production — push master to GitHub, build amd64 images locally, transfer, run migrations, switch the running services, verify. Use when the user asks to push and deploy to production (部署到生产 / 上线), or runs /deploy.
---

# SeeWord Deploy — build here, ship there

The production host has no build capacity (2C/1.6 GB — an in-place `docker compose build` freezes the
machine), so images are built on this workstation and loaded on the server. Three phases: **build**
(local), **transfer** (upload + hash check), **switch** (load → migrate → recreate → nginx reload).

| | |
|---|---|
| Host | `47.122.109.52`, **root password auth**, code at `/opt/speaking` (a source copy, no `.git`) |
| Containers | `speaking-backend-1` `speaking-celery-1` `speaking-celery-beat-1` `speaking-frontend-1`; db/redis/nginx stay untouched |
| Images | `speaking-backend` `speaking-celery` `speaking-celery-beat` `speaking-frontend` |
| Site | https://seeword.top |

`scripts/sshx.py` runs one command over SSH; `scripts/upload.py` does resumable SFTP. Both read the
password from the `SW_PW` environment variable and take the host from `SW_HOST`.

**Resolve the host from DNS, never from an SSH alias.** `~/.ssh/config`'s `seeword` points at
`47.122.127.105`, a decommissioned machine whose containers are named `seeword-*`; reading its state
as production already produced a false "production data is empty" conclusion once.

## Steps

1. **Resolve the host and get the password.**
   ```bash
   dig +short seeword.top
   ```
   Done when the IP is resolved and you hold the root password — ask the user for it if it is not
   already in context. It is never written to the repo.

2. **Push master.** Check the tree and the remote before building:
   ```bash
   git status --short && git log --oneline -1 origin/master
   ```
   On `Connection reset`, retry through the local proxy:
   ```bash
   git -c http.sslBackend=openssl -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push origin master
   ```
   Done when `origin/master` is at the commit you are about to build. **A dirty tree stops the
   deploy** — the image is built from the working tree, so uncommitted source ships code that matches
   no commit and no rollback target.

3. **Build the four images, then package them.** `--platform linux/amd64` is mandatory: the host is
   x86_64 and a native Windows build produces the wrong platform.
   ```bash
   cd "$(git rev-parse --show-toplevel)"
   IMG="$(cygpath -m "$TEMP")/images.tgz"

   docker build --platform linux/amd64 -f backend/Dockerfile.cloud -t speaking-backend:latest backend/
   docker tag speaking-backend:latest speaking-celery:latest
   docker tag speaking-backend:latest speaking-celery-beat:latest
   docker build --platform linux/amd64 -f frontend/Dockerfile.prod -t speaking-frontend:latest frontend/

   docker save speaking-backend:latest speaking-celery:latest speaking-celery-beat:latest speaking-frontend:latest \
     | gzip -1 > "$IMG"
   sha256sum "$IMG"
   ```
   Done when the archive is ~403 MB and you have written its sha256 down. Record the four new image
   IDs too — step 8 compares them against the running containers.

4. **Transfer, then verify the archive.** Run it in the background: ~9–17 min at ~400 KB/s, and the
   connection does drop mid-flight (the script reconnects and resumes from the remote offset).
   `MSYS_NO_PATHCONV=1` is required or Git Bash rewrites `/root/images.tgz` into
   `C:/Program Files/Git/root/images.tgz`; the local argument must be a Windows-form path
   (`cygpath -m`) for the same reason.
   ```bash
   cd "$(git rev-parse --show-toplevel)/.claude/skills/deploy/scripts"
   MSYS_NO_PATHCONV=1 SW_HOST=<resolved-ip> SW_PW='<password>' python upload.py \
     "$(cygpath -m "$TEMP")/images.tgz" /root/images.tgz
   ```
   ```bash
   cd "$(git rev-parse --show-toplevel)/.claude/skills/deploy/scripts"
   MSYS_NO_PATHCONV=1 SW_HOST=<resolved-ip> SW_PW='<password>' python sshx.py "sha256sum /root/images.tgz"
   ```
   Done when the last upload line reads `DONE <n> / <n> bytes` **and** the remote sha256 is
   character-for-character the value from step 3. A mismatch means re-upload; an unverified archive
   is never loaded.

5. **Freeze the rollback point, then load.** The tags must capture the *currently running* images, so
   this ordering is the whole point of the step.
   ```bash
   cd "$(git rev-parse --show-toplevel)/.claude/skills/deploy/scripts"
   MSYS_NO_PATHCONV=1 SW_HOST=<resolved-ip> SW_PW='<password>' python sshx.py "
   set -e
   cd /opt/speaking
   TS=\$(date +%Y%m%d%H%M%S)
   cp .env /root/backups/env.\$TS
   cp docker-compose.prod.yml /root/backups/compose.\$TS.yml
   docker compose -f docker-compose.prod.yml exec -T db pg_dump -U seeword -d seeword -Fc > /root/backups/pg_predeploy_\$TS.dump
   docker compose -f docker-compose.prod.yml exec -T db pg_restore --list < /root/backups/pg_predeploy_\$TS.dump > /dev/null
   for s in backend celery celery-beat frontend; do docker tag speaking-\$s:latest speaking-\$s:pre-deploy; done
   gunzip -c /root/images.tgz | docker load
   docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep speaking- | sort
   "
   ```
   Done when `speaking-*:latest` shows the **new** IDs, `speaking-*:pre-deploy` still shows the old
   ones, and the `.env` / compose / `pg_predeploy_*.dump` backups exist.
   The dump is custom format and `pg_restore --list` must read it — the old
   `pg_dump | gzip` had no `pipefail`, so a failed dump could still leave a
   valid-looking empty `.gz`. This is the pre-deploy rollback point; scheduled
   off-host backups are `scripts/backup/backup.sh` (A09).

6. **Migrate — and stop if the migration fails.**
   ```bash
   cd "$(git rev-parse --show-toplevel)/.claude/skills/deploy/scripts"
   MSYS_NO_PATHCONV=1 SW_HOST=<resolved-ip> SW_PW='<password>' python sshx.py "
   cd /opt/speaking
   docker compose -f docker-compose.prod.yml run --rm --no-deps --entrypoint /app/entrypoint.sh backend migrate-only
   "
   ```
   Done when the output contains `Migrations OK.` and `alembic current` reports the same head as the
   local tree. In `migrate-only` mode a migration failure makes `entrypoint.sh` print
   `[entrypoint] ERROR: alembic upgrade head failed (exit N).` and exit non-zero, so the command above
   fails outright — treat any non-zero exit as a hard stop. (The *normal* startup path is the one that
   swallows the failure: it prints `[entrypoint] WARNING: continuing startup so /health can report the
   DB issue.` and the container still comes up green, so a green `/health` proves nothing there.) If a
   failure appears, stop before step 7 and report; services are still running the old code and the
   rollback point is intact.

7. **Switch: recreate the four app containers and re-resolve nginx's upstreams.**
   ```bash
   cd "$(git rev-parse --show-toplevel)/.claude/skills/deploy/scripts"
   MSYS_NO_PATHCONV=1 SW_HOST=<resolved-ip> SW_PW='<password>' python sshx.py "
   cd /opt/speaking
   docker compose -f docker-compose.prod.yml up -d --remove-orphans
   docker exec speaking-nginx-1 nginx -s reload
   "
   ```
   Done when all four containers report `Started` and `nginx -s reload` returns. **The reload is not
   optional**: nginx resolves `backend` / `frontend` once at startup and caches the IPs forever, so
   without it the recreated containers are unreachable and the whole site returns 502. Never
   `docker compose down` instead — with `backend` absent, nginx dies on
   `[emerg] host not found in upstream` and takes db/redis with it.

8. **Verify every line.** Each row is a separate check; report any that fails rather than reporting
   the deploy as done.
   ```bash
   cd "$(git rev-parse --show-toplevel)/.claude/skills/deploy/scripts"
   MSYS_NO_PATHCONV=1 SW_HOST=<resolved-ip> SW_PW='<password>' python sshx.py "
   cd /opt/speaking
   docker compose -f docker-compose.prod.yml ps --format '{{.Name}}|{{.Status}}'
   for c in backend celery celery-beat frontend; do printf '%s ' \$c; docker inspect speaking-\$c-1 --format '{{.Image}}'; done
   docker compose -f docker-compose.prod.yml exec -T backend alembic current 2>&1 | grep -v INFO
   docker exec speaking-celery-1 celery -A app.tasks.celery_app inspect ping 2>&1 | tail -2
   docker logs speaking-backend-1 2>&1 | grep -iE 'error|traceback' | tail -5
   "
   ```
   Externally:
   ```bash
   curl -fsS https://seeword.top/health
   curl -s -o /dev/null -w 'login=%{http_code}\n' https://seeword.top/login
   curl -s -o /dev/null -w 'api=%{http_code}\n' 'https://seeword.top/api/v1/videos/search/subtitles?q=hello'
   ```
   Expected: every container `Up` with backend healthy · the four image IDs from step 3 ·
   `alembic current` at `<local-head> (head)` · `1 node online` from the Celery ping · no error lines
   in the backend log · `{"status":"ok"}` with database and redis both `ok` · `login=200` · `api=200`.
   Done when **all** of these hold.

9. **Clean up.** Delete the 403 MB archive on both ends once step 8 passes.
   ```bash
   cd "$(git rev-parse --show-toplevel)/.claude/skills/deploy/scripts"
   MSYS_NO_PATHCONV=1 SW_HOST=<resolved-ip> SW_PW='<password>' python sshx.py "rm -f /root/images.tgz"
   rm -f "$(cygpath -m "$TEMP")/images.tgz"
   ```

## Notes

- **Rollback** is the `pre-deploy` tags plus a re-run of step 7:
  ```bash
  for s in backend celery celery-beat frontend; do docker tag speaking-$s:pre-deploy speaking-$s:latest; done
  docker compose -f docker-compose.prod.yml up -d --remove-orphans && docker exec speaking-nginx-1 nginx -s reload
  ```
  New tables and columns are purely additive, so rolling back the images normally needs no schema
  change. To back the schema out too, restore the `pg_predeploy_*.dump` from step 5 first
  (`docker compose -f docker-compose.prod.yml exec -T db pg_restore -U seeword -d seeword --clean --if-exists < /root/backups/pg_predeploy_<TS>.dump`).
- **Sync config only when it changed.** Compare the local and remote checksums:
  ```bash
  sha256sum docker-compose.prod.yml nginx.ssl.conf promtail.yml
  ```
  If they differ, copy those files to `/opt/speaking/` before step 7 (`backend/data/` is a
  bind-mount, not in git — copy it only when the ECDICT/exam data itself changed). Do **not** copy
  `nginx.conf`: `.env` sets `NGINX_CONF=nginx.ssl.conf`, so `nginx.conf` is a deliberately stale
  HTTP-only leftover, and overwriting the live one silently drops the site back to plain HTTP.
- **Identifiers on the host**: the compose project prefix is `speaking-`, but `psql` takes
  `-U seeword -d seeword`.
- **Worth fixing once**: authorizing this workstation's SSH key on the server would remove the
  password from every command above. Until then the password is passed inline per call.

## Stop signals

Stop and ask instead of pressing on:

- **The user has not explicitly asked to deploy.** Reading the repo, "is it up?", or a code change is
  not authorization for production — this skill runs only on a direct request.
- **The working tree is dirty, or HEAD is not on `origin/master`.** Shipping an image that matches no
  commit leaves nothing to roll forward to or reproduce.
- **The sha256 does not match, or `migrations` reports a failure.** Both are pre-switch, so nothing is
  broken yet and the old release is still serving — report and let the user decide.
- **Anything irreversible beyond the documented steps**: dropping a column or table, deleting media,
  `docker compose down`, `docker volume rm`. Rollback here is image-based by design; schema work goes
  through its own review.
