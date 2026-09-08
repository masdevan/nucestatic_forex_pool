# Deployment

Deployment stack: Docker Compose (FastAPI + MySQL 8.0) + Cloudflare Tunnel.

## Local/Server folders

- `docker-compose.yml` - services `db` (mysql:8.0, internal network only) and `app`
- `Dockerfile` - Python 3.12-slim, runs `uvicorn main:app` on port 8765
- `~/db-import-progress.sh` - import the forexpool.sql dump into the db container (progress bar + screen keep-alive)
- `.env.example` - copy to `.env` and fill: `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`, optional Centrifugo vars

## Commands

```bash
cp .env.example .env        # fill values
docker compose up -d --build

# import database dump (one time)
sudo ~/db-import-progress.sh /home/masdevan/forexpool.sql
```

MySQL is only reachable inside the compose network. The app binds to `127.0.0.1:8765` on the host.

## Cloudflare Tunnel

Tunnel config is separated under `deploy/cloudflared/`:

- `config-marketpool.example.yml` - template (fill in tunnel id/credentials path)
- `cloudflared-marketpool.service` - systemd unit template

Server-side (root):

```bash
cloudflared tunnel create marketpool
cloudflared tunnel route dns --overwrite-dns <TUNNEL_ID> marketpool.devan.my.id
cp deploy/cloudflared/config-marketpool.example.yml /etc/cloudflared/config-marketpool.yml
cp deploy/cloudflared/cloudflared-marketpool.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now cloudflared-marketpool
```