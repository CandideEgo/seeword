#!/usr/bin/env bash
# SeeWord versioned, verified backup (A09 / OPS-06).
#
# One run produces a directory: a custom-format pg_dump, its table-of-contents
# verification, the alembic revision, exact row counts, the media archive, the
# deployment config, and a manifest with checksums. A run that fails leaves a
# FAILED marker and no SUCCESS marker — the old failure mode here was
# `pg_dump | gzip` without pipefail, which could leave a perfectly valid *empty*
# gzip file and report success.
#
# Modes: with DB_CONTAINER set it talks to that container directly (drills,
# non-compose boxes); otherwise it uses `docker compose exec` on the db service.
#
# Environment (defaults target /opt/speaking on the production host):
#   SEEWORD_DIR            repo checkout on the host        (/opt/speaking)
#   COMPOSE_FILE           compose file                     ($SEEWORD_DIR/docker-compose.prod.yml)
#   DB_SERVICE / DB_USER / DB_NAME                          (db / seeword / seeword)
#   DB_CONTAINER           talk to this container instead of compose
#   BACKUP_ROOT            where runs are written           (/root/backups/seeword)
#   BACKUP_KEEP_DAYS       local retention                  (14)
#   BACKUP_MEDIA           1 = archive the media volume     (1)
#   MEDIA_VOLUME           docker volume to archive         (speaking_media)
#   MEDIA_PATH             host directory instead of a volume
#   MEDIA_IMAGE            image used for the tar (has tar+gzip)  (postgres:16-alpine)
#   BACKUP_CONFIG_FILES    space-separated file list; empty string disables
#                          (.env docker-compose.prod.yml nginx.ssl.conf promtail.yml)
#   BACKUP_OFFHOST_CMD     shell command run after success  (empty; e.g. `rclone copy "$BACKUP_DIR" remote:...`)
#   BACKUP_GPG_RECIPIENT   encrypt the tarball to this GPG recipient (empty = no encryption)
#   BACKUP_TARBALL         1 = bundle the run into one tar.gz          (1)
#
# Exit codes: 0 success (SUCCESS marker written), non-zero failure.
set -euo pipefail

DOCKER=${DOCKER:-docker}
SEEWORD_DIR=${SEEWORD_DIR:-/opt/speaking}
COMPOSE_FILE=${COMPOSE_FILE:-$SEEWORD_DIR/docker-compose.prod.yml}
DB_SERVICE=${DB_SERVICE:-db}
DB_USER=${DB_USER:-seeword}
DB_NAME=${DB_NAME:-seeword}
DB_CONTAINER=${DB_CONTAINER:-}
BACKUP_ROOT=${BACKUP_ROOT:-/root/backups/seeword}
BACKUP_KEEP_DAYS=${BACKUP_KEEP_DAYS:-14}
BACKUP_MEDIA=${BACKUP_MEDIA:-1}
MEDIA_VOLUME=${MEDIA_VOLUME:-speaking_media}
MEDIA_PATH=${MEDIA_PATH:-}
MEDIA_IMAGE=${MEDIA_IMAGE:-postgres:16-alpine}
# No colon: an explicitly empty value must stay empty (disable), not fall back.
BACKUP_CONFIG_FILES=${BACKUP_CONFIG_FILES-.env docker-compose.prod.yml nginx.ssl.conf promtail.yml}
OFFHOST_CMD=${BACKUP_OFFHOST_CMD:-}
GPG_RECIPIENT=${BACKUP_GPG_RECIPIENT:-}
BACKUP_TARBALL=${BACKUP_TARBALL:-1}

TS=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR="$BACKUP_ROOT/$TS"
umask 077
mkdir -p "$BACKUP_DIR"
HOSTNAME_=$(hostname 2>/dev/null || echo unknown)

log() { printf '[backup %s] %s\n' "$TS" "$*"; }
die() { printf '[backup %s] FAILED: %s\n' "$TS" "$*" >&2; echo "failed: $*" >"$BACKUP_DIR/FAILED"; exit 1; }
trap 'echo "aborted at line $LINENO" >"$BACKUP_DIR/FAILED"' ERR

db_exec() {
  if [ -n "$DB_CONTAINER" ]; then
    "$DOCKER" exec -i "$DB_CONTAINER" "$@"
  else
    "$DOCKER" compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" "$@"
  fi
}

db_query() { db_exec psql -U "$DB_USER" -d "$DB_NAME" -tAc "$1"; }

# --- 1. Database dump (custom format) and integrity verification -------------
log "dumping database $DB_NAME"
db_exec pg_dump -U "$DB_USER" -d "$DB_NAME" -Fc >"$BACKUP_DIR/db.dump" || die "pg_dump failed"
[ -s "$BACKUP_DIR/db.dump" ] || die "pg_dump produced an empty file"
db_exec pg_restore --list <"$BACKUP_DIR/db.dump" >"$BACKUP_DIR/db.toc" || die "pg_restore -l could not read the dump"
[ -s "$BACKUP_DIR/db.toc" ] || die "dump table of contents is empty"

# --- 2. Alembic revision + row counts ---------------------------------------
if db_query "SELECT version_num FROM alembic_version" >"$BACKUP_DIR/alembic_version.txt" 2>/dev/null; then
  REVISION=$(tr -d '[:space:]' <"$BACKUP_DIR/alembic_version.txt")
  log "alembic revision: ${REVISION:-unknown}"
else
  REVISION="unknown"
  echo "unknown" >"$BACKUP_DIR/alembic_version.txt"
  log "WARNING: could not read alembic_version"
fi

# 已删表不列入：orders / jinshuju_payments / user_video_unlocks 在迁移
# d4e5f6a7b8c9 中 drop，列进来只会每轮打印 `orders=missing`。
TABLES=${BACKUP_TABLES:-users videos subtitles vocabulary learning_records learning_events user_learning_profiles user_favorites user_notes exam_papers exam_questions exam_sessions}
: >"$BACKUP_DIR/row_counts.txt"
for t in $TABLES; do
  if count=$(db_query "SELECT count(*) FROM $t" 2>/dev/null); then
    printf '%s=%s\n' "$t" "$(echo "$count" | tr -d '[:space:]')" >>"$BACKUP_DIR/row_counts.txt"
  else
    printf '%s=missing\n' "$t" >>"$BACKUP_DIR/row_counts.txt"
  fi
done

# --- 3. Media archive -------------------------------------------------------
MEDIA_FILES=0
if [ "$BACKUP_MEDIA" = "1" ]; then
  if [ -n "$MEDIA_PATH" ]; then
    log "archiving media path $MEDIA_PATH"
    tar czf "$BACKUP_DIR/media.tar.gz" -C "$MEDIA_PATH" . || die "media tar failed"
  else
    log "archiving media volume $MEDIA_VOLUME"
    "$DOCKER" run --rm -v "$MEDIA_VOLUME:/media:ro" -v "$BACKUP_DIR:/backup" "$MEDIA_IMAGE" \
      sh -c 'cd /media && tar czf /backup/media.tar.gz .' || die "media volume tar failed"
  fi
  tar -tzf "$BACKUP_DIR/media.tar.gz" >"$BACKUP_DIR/media.toc" || die "media archive is unreadable"
  MEDIA_FILES=$(grep -cv '/$' "$BACKUP_DIR/media.toc" || true)
fi

# --- 4. Deployment config ---------------------------------------------------
mkdir -p "$BACKUP_DIR/config"
for f in $BACKUP_CONFIG_FILES; do
  if [ -f "$SEEWORD_DIR/$f" ]; then
    cp "$SEEWORD_DIR/$f" "$BACKUP_DIR/config/$f"
  elif [ "$f" = ".env" ] || [ "$f" = "$(basename "$COMPOSE_FILE")" ]; then
    die "required config file $SEEWORD_DIR/$f is missing"
  else
    log "WARNING: optional config $f not found, skipped"
  fi
done

# --- 5. Manifest ------------------------------------------------------------
GIT_REV=$(git -C "$SEEWORD_DIR" rev-parse HEAD 2>/dev/null || echo unknown)
BACKEND_IMAGE=$(
  "$DOCKER" inspect --format '{{.Image}}' speaking-backend-1 2>/dev/null || echo unknown
)
sha() { sha256sum "$1" 2>/dev/null | awk '{print $1}'; }
{
  printf '{\n'
  printf '  "created_at": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '  "hostname": "%s",\n' "$HOSTNAME_"
  printf '  "git_revision": "%s",\n' "$GIT_REV"
  printf '  "backend_image": "%s",\n' "$BACKEND_IMAGE"
  printf '  "alembic_revision": "%s",\n' "${REVISION:-unknown}"
  printf '  "db_name": "%s",\n' "$DB_NAME"
  printf '  "db_dump_sha256": "%s",\n' "$(sha "$BACKUP_DIR/db.dump")"
  printf '  "db_dump_bytes": %s,\n' "$(wc -c <"$BACKUP_DIR/db.dump" | tr -d ' ')"
  printf '  "media_sha256": "%s",\n' "$([ -f "$BACKUP_DIR/media.tar.gz" ] && sha "$BACKUP_DIR/media.tar.gz" || echo none)"
  printf '  "media_files": %s,\n' "$MEDIA_FILES"
  printf '  "media_volume": "%s",\n' "$MEDIA_VOLUME"
  printf '  "row_counts_file": "row_counts.txt"\n'
  printf '}\n'
} >"$BACKUP_DIR/manifest.json"

(cd "$BACKUP_DIR" && sha256sum db.dump manifest.json row_counts.txt alembic_version.txt >SHA256SUMS)

# --- 6. Bundle, encrypt, ship off-host --------------------------------------
if [ "$BACKUP_TARBALL" = "1" ]; then
  tar czf "$BACKUP_DIR.tar.gz" -C "$BACKUP_ROOT" "$TS" || die "tarball failed"
  if [ -n "$GPG_RECIPIENT" ]; then
    gpg --batch --yes --encrypt --recipient "$GPG_RECIPIENT" "$BACKUP_DIR.tar.gz" || die "gpg encryption failed"
    rm -f "$BACKUP_DIR.tar.gz"
    log "encrypted: $BACKUP_DIR.tar.gz.gpg"
  fi
fi

if [ -n "$OFFHOST_CMD" ]; then
  log "off-host copy: $OFFHOST_CMD"
  BACKUP_DIR="$BACKUP_DIR" sh -c "$OFFHOST_CMD" || die "off-host copy failed"
fi

# --- 7. Success marker, then retention -------------------------------------
date -u +%Y-%m-%dT%H:%M:%SZ >"$BACKUP_DIR/SUCCESS"
echo "$(sha "$BACKUP_DIR/manifest.json")" >>"$BACKUP_DIR/SUCCESS"
log "SUCCESS: $BACKUP_DIR"

find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +"$BACKUP_KEEP_DAYS" | while read -r old; do
  if [ -f "$old/SUCCESS" ]; then
    log "pruning $old (older than ${BACKUP_KEEP_DAYS}d, has SUCCESS)"
    rm -rf "$old" "$old.tar.gz" "$old.tar.gz.gpg"
  fi
done
