#!/usr/bin/env bash
set -euo pipefail

export PATH=/opt/nodejs/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
repo=/opt/foxelli/source
current=/opt/foxelli/current
revision_file=/opt/foxelli/deployed-revision

exec 9>/run/lock/foxelli-deploy.lock
flock -n 9 || exit 0

git -C "$repo" fetch --quiet origin main
revision=$(git -C "$repo" rev-parse FETCH_HEAD)
deployed=$(cat "$revision_file" 2>/dev/null || true)
if [ "$revision" = "$deployed" ]; then
    exit 0
fi

previous=$(readlink -f "$current")
git -C "$repo" checkout --force --detach "$revision" >/dev/null
npm ci --prefix "$repo/frontend" --no-audit --no-fund
npm run build --prefix "$repo/frontend"
/opt/foxelli/venv/bin/pip install --quiet -r "$repo/backend/requirements.txt"
PYTHONPATH="$repo/backend" /opt/foxelli/venv/bin/python -m unittest discover -s "$repo/backend/tests"

release="/opt/foxelli/releases/$revision"
if [ ! -d "$release" ]; then
    staged=$(mktemp -d /opt/foxelli/releases/.incoming.XXXXXX)
    chmod 755 "$staged"
    cp -a "$repo/backend" "$staged/backend"
    cp -a "$repo/frontend/out" "$staged/web"
    cp -a "$repo/deploy" "$staged/deploy"
    mv "$staged" "$release"
fi

activate() {
    ln -sfn "$1" "$current.next" &&
    mv -Tf "$current.next" "$current" &&
    systemctl daemon-reload &&
    nginx -t &&
    systemctl restart foxelli-api foxelli-worker &&
    systemctl reload nginx
}

healthy() {
    for _ in $(seq 1 20); do
        if curl -fsS --max-time 2 http://127.0.0.1:8000/api/health 2>/dev/null | grep -q '"ok":true' &&
           curl -fsS --max-time 2 http://127.0.0.1:8000/api/videos >/dev/null 2>&1 &&
           curl -fsS --max-time 3 --resolve 5.22.217.149:443:127.0.0.1 https://5.22.217.149/ 2>/dev/null | grep -q 'Video Review Lab'; then
            return 0
        fi
        sleep 1
    done
    return 1
}

if ! activate "$release" || ! healthy; then
    echo "Deployment $revision failed; restoring $previous" >&2
    activate "$previous"
    exit 1
fi

install -m 755 "$repo/deploy/foxelli-deploy.sh" /usr/local/sbin/foxelli-deploy
printf '%s\n' "$revision" > "$revision_file"
echo "Deployed $revision"
