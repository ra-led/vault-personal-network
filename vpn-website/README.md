# VPN Landing Website + YooKassa Payments

## Run with Docker

```bash
cp .env.example .env
# fill YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, BASE_URL,
# CONTROL_PLANE_API_URL, and CONTROL_PLANE_INTERNAL_TOKEN
docker compose up --build
```

In production, Caddy publishes ports 80/443, obtains Let's Encrypt certificates,
and proxies traffic to the internal website container. For local Docker-only
testing, open [http://localhost](http://localhost) or run `npm run start` outside
compose to use port 8080 directly.

## Local dev without Docker

```bash
npm install
cp .env.example .env
docker compose up -d postgres
npm run build
npm run start
```

Then open [http://localhost:8080](http://localhost:8080).

## Payment API (redirect flow)

- `POST /api/create-payment` creates YooKassa payment and returns `confirmation_url`
- `POST /api/yookassa-webhook` handles `payment.succeeded` and `payment.canceled`
- `GET /api/payment-status/:paymentId` checks and syncs status via YooKassa API
- `GET /api/health` checks API and database connectivity

Required env vars:

- `YOOKASSA_SHOP_ID`
- `YOOKASSA_SECRET_KEY`
- `BASE_URL` (for return URL)
- `DATABASE_URL` (PostgreSQL)
- `CONTROL_PLANE_API_URL` (control-plane API reachable from the website container)
- `CONTROL_PLANE_INTERNAL_TOKEN` (same value as control-plane `INTERNAL_API_TOKEN`)

## Production notes

- Payment records and webhook events are persisted in PostgreSQL (no in-memory state).
- Webhook requests are idempotent by payload fingerprint.
- Webhook events are verified by extra YooKassa API status check before marking payment as final.
- Successful payments are synced to the control plane balance endpoint.
- In `NODE_ENV=production`, `BASE_URL` must be HTTPS.
- IP filtering for YooKassa webhook sources is enabled by default in production (`YOOKASSA_ENFORCE_IP_FILTER=true`).
- `vpn-go.ru` and `www.vpn-go.ru` are served by Caddy from `Caddyfile`; `www` redirects to the apex domain.
