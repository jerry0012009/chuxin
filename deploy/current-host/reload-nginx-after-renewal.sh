#!/bin/sh
set -eu

if [ "${RENEWED_LINEAGE:-}" = /etc/letsencrypt/live/chuxin.31-220-80-196.sslip.io ]; then
    nginx -t
    systemctl reload nginx
fi
