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

## Payment API (YooKassa redirect flow)

- `POST /api/create-payment` creates YooKassa payment and returns `confirmation_url`
- `POST /api/yookassa-webhook` handles `payment.succeeded` and `payment.canceled`
- `GET /api/payment-status/:paymentId` checks and syncs status via YooKassa API
- `GET /api/payment-status-by-order/:orderId` checks and syncs status by local order id
- `GET /api/health` checks API and database connectivity

Required env vars:

- `YOOKASSA_SHOP_ID`
- `YOOKASSA_SECRET_KEY`
- `YOUKASSA_SHOP_ID` and `YOUKASSA_API_KEY` are also accepted as aliases.
- `BASE_URL` (for return URL)
- `DATABASE_URL` (PostgreSQL)
- `CONTROL_PLANE_API_URL` (control-plane API reachable from the website container)
- `CONTROL_PLANE_INTERNAL_TOKEN` (same value as control-plane `INTERNAL_API_TOKEN`)

### Technical payment flow

The website uses YooKassa Smart Payment with redirect confirmation. Card details
and payment-method selection are handled by YooKassa, not by this application.

1. The customer logs in to the website cabinet and chooses a balance top-up
   amount.
2. The browser calls `POST /api/create-payment` with:
   - `amount_rub`
   - `user_id` (browser-local numeric account id)
   - `order_id` (optional; generated server-side if omitted)
   - `plan_name` / `description` for human-readable payment context
3. The website backend creates a YooKassa payment via `POST /v3/payments` using:
   - `amount.value`
   - `amount.currency = RUB`
   - `capture = true`
   - `confirmation.type = redirect`
   - `confirmation.return_url = ${BASE_URL}/payment-return?order_id=...`
   - `metadata.user_id`, `metadata.order_id`, `metadata.plan_name`
4. The backend stores the pending payment in the website PostgreSQL database and
   returns `confirmation_url`.
5. The browser redirects the customer to `confirmation_url` on YooKassa.
6. After payment, YooKassa redirects the customer back to `/payment-return`.
7. On `/payment-return`, the frontend calls
   `GET /api/payment-status-by-order/:orderId`. This endpoint fetches the real
   payment status from YooKassa, updates the local payment row, and syncs a
   successful payment to the control plane.
8. Separately, YooKassa should send webhook notifications to
   `POST /api/yookassa-webhook`. Webhooks are the primary reliable server-side
   completion path if the customer closes the payment page before returning.
9. For a verified `succeeded` payment, the website calls the control plane:
   - `POST /v1/payments/external/confirm`
   - Header: `X-Internal-Token: ${CONTROL_PLANE_INTERNAL_TOKEN}`
   - Body includes `external_payment_id`, `amount_kopecks`, numeric `user_id`,
     and `provider = yookassa`
10. The control plane idempotently records the external payment and credits the
    user balance.

### Idempotency and safety

- `POST /api/create-payment` accepts an `Idempotence-Key` header. If the same
  key is repeated and a pending local payment already has a `confirmation_url`,
  the existing payment is returned instead of creating a duplicate.
- If `order_id` is repeated and the local payment is still pending, the existing
  `confirmation_url` is reused.
- YooKassa webhook events are stored by payload fingerprint, so repeated webhook
  delivery is safe.
- Webhook payloads are not trusted blindly. The server fetches the payment from
  YooKassa API before accepting `succeeded` or `canceled` as final.
- Control-plane crediting is idempotent by `external_payment_id`, so webhook
  delivery and return-page polling cannot double-credit the same YooKassa
  payment.

### YooKassa cabinet setup

Configure these URLs in the YooKassa shop cabinet:

- Return URL is generated automatically per payment:
  `https://vpn-go.ru/payment-return?order_id=...`
- Webhook URL:
  `https://vpn-go.ru/api/yookassa-webhook`
- Webhook events:
  - `payment.succeeded`
  - `payment.canceled`

The current implementation does not send `payment_method_data`, `payment_token`,
or `payment_method_id`. YooKassa shows its hosted payment page where the
customer selects the payment method.

## Production notes

- Payment records and webhook events are persisted in PostgreSQL (no in-memory state).
- Webhook requests are idempotent by payload fingerprint.
- Webhook events are verified by extra YooKassa API status check before marking payment as final.
- Successful payments are synced to the control plane balance endpoint.
- In `NODE_ENV=production`, `BASE_URL` must be HTTPS.
- IP filtering for YooKassa webhook sources is enabled by default in production (`YOOKASSA_ENFORCE_IP_FILTER=true`).
- `vpn-go.ru` and `www.vpn-go.ru` are served by Caddy from `Caddyfile`; `www` redirects to the apex domain.
