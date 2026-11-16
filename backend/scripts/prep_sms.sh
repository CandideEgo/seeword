#!/usr/bin/env bash
# Prep server .env for new SMS credentials (no secrets written yet)
# 1. backup current .env
# 2. fix template variable names (old ALIYUN_SMS_TEMPLATE_CODE -> 3 new vars)
# 3. tighten permissions on the leaked backup file
set -e
PROJECT_DIR="${PROJECT_DIR:-/opt/speaking}"
cd "$PROJECT_DIR"

BACKUP="$(mktemp .env.bak.XXXXXXXXXX)"
(umask 077; cp .env "$BACKUP")
echo "backup created: $BACKUP"

# Replace the legacy single template var with the three per-purpose vars
# (values inherited from the old TEMPLATE_CODE=100001 as placeholders;
#  user should confirm actual template ids in Aliyun console)
if grep -q '^ALIYUN_SMS_TEMPLATE_CODE=' .env; then
  sed -i \
    -e 's/^ALIYUN_SMS_TEMPLATE_CODE=.*/ALIYUN_SMS_TEMPLATE_REGISTER=100001\nALIYUN_SMS_TEMPLATE_CHANGE_PHONE=100002\nALIYUN_SMS_TEMPLATE_RESET_PASSWORD=100003/' \
    .env
  echo "template vars replaced:"
  grep -E '^ALIYUN_SMS_TEMPLATE' .env | sed 's/=.*/=<set>/'
else
  echo "no legacy ALIYUN_SMS_TEMPLATE_CODE found (nothing to replace)"
fi

# The backup we just made holds the same plaintext secrets as .env — restrict it
# too. (This used to hardcode `.env.bak.20260805`, so it only ever chmod'ed that
# one old file and silently did nothing on any other run.)
chmod 600 "$BACKUP" && echo "chmod 600 $BACKUP"
chmod 600 .env
echo "chmod 600 .env"

echo ''
echo '=== SMS block in .env now (masked) ==='
grep -E '^SMS_|^ALIYUN_SMS_' .env | sed -E 's/=(.*)$/=<masked>/'
