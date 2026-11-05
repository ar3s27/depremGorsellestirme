#!/usr/bin/env bash
# Uygulamayı ev sunucusuna yayınlar: git'in izlediği dosyaları kopyalar, Docker imajını
# sunucuda derler, konteyneri yeniden başlatır.
#
# Kullanım (repo kökünden, Git Bash):   bash deploy/deploy.sh
set -euo pipefail

SERVER="${SERVER:-veysel@192.168.1.4}"
REMOTE_DIR="${REMOTE_DIR:-apps/deprem-api}"
PUBLIC_URL="https://deprem-api.veyselerkoyuncu.com.tr"

cd "$(dirname "$0")/.."

echo ">> Kaynak kod gönderiliyor: $SERVER:~/$REMOTE_DIR/app"
ssh "$SERVER" "mkdir -p ~/$REMOTE_DIR && rm -rf ~/$REMOTE_DIR/app.new && mkdir ~/$REMOTE_DIR/app.new"
# Yalnızca git'e kayıtlı (ya da yeni eklenmiş, .gitignore dışı) dosyalar gider; .env gibi dosyalar gitmez.
git ls-files -z --cached --others --exclude-standard | grep -zv '^\.env' \
  | tar --null -T - -czf - \
  | ssh "$SERVER" "tar -xzf - -C ~/$REMOTE_DIR/app.new"

echo ">> Sunucuda derleniyor ve başlatılıyor"
ssh "$SERVER" bash -s -- "$REMOTE_DIR" <<'REMOTE'
set -euo pipefail
cd ~/"$1"
rm -rf app.old
[ -d app ] && mv app app.old
mv app.new app
cp app/deploy/compose.yaml compose.yaml
if [ -f app/deploy/remote-setup.sh ]; then bash app/deploy/remote-setup.sh; fi
if [ -f .skip-start ]; then rm -f .skip-start; echo ">> Başlatma atlandı (yukarıdaki nota bak)"; exit 0; fi
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
REMOTE

echo ">> Tamam: $PUBLIC_URL"
