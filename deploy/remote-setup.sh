#!/usr/bin/env bash
# deploy.sh tarafından sunucuda, ~/apps/deprem içinde çalıştırılır.
set -euo pipefail

# Veri klasörü konteynerdeki "app" kullanıcısına (uid 10001) yazılabilir olmalı.
mkdir -p data
if [ "$(stat -c %u data)" != "10001" ]; then
  docker run --rm -v "$PWD/data:/data" alpine:3.20 chown 10001:10001 /data
fi

# Telegram botu isteğe bağlı: token'ı kullanıcı kendisi yazar. Boşken site ve API çalışır.
if [ ! -f .env ]; then
  umask 077
  cat > .env <<'ENV'
# @BotFather'dan alınan token. Boş bırakılırsa Telegram botu başlamaz.
TELEGRAM_BOT_TOKEN=
ENV
  echo ">> ~/apps/deprem/.env oluşturuldu (Telegram token'ı isteğe bağlı)"
fi
