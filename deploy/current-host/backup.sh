#!/usr/bin/env bash
set -euo pipefail
umask 077

directory=/var/backups/chuxin
stamp=$(date -u +%Y%m%dT%H%M%SZ)
temporary=$(mktemp "$directory/.db.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT

docker exec chuxin-mysql-1 sh -ec '
  export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"
  exec mysqldump -u root --single-transaction --no-tablespaces --set-gtid-purged=OFF "$MYSQL_DATABASE"
' | gzip > "$temporary"
gzip -t "$temporary"
mv "$temporary" "$directory/mysql-$stamp.sql.gz"
find "$directory" -maxdepth 1 -type f -name 'mysql-*.sql.gz' -mtime +14 -delete
