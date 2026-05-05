import { useMemo, useState } from 'react';

export default function VPNLandingPage() {
  const [isPaying, setIsPaying] = useState(false);
  const [paymentError, setPaymentError] = useState('');
  const [customAmount, setCustomAmount] = useState('10');

  const plans = [
    { name: '1 Month', priceRub: 399, note: 'Flexible access' },
    { name: '6 Months', priceRub: 2190, note: 'Save 16%' },
    { name: '12 Months', priceRub: 3990, note: 'Best value' }
  ];
  const plansWithDisplayPrice = useMemo(
    () =>
      plans.map((plan) => ({
        ...plan,
        price: `${plan.priceRub.toLocaleString('ru-RU')} ₽`
      })),
    [plans]
  );

  const devices = [
    {
      name: 'MacBook Pro',
      ip: '185.24.16.72',
      location: 'Amsterdam, NL',
      status: 'Protected'
    },
    {
      name: 'iPhone 15',
      ip: '185.24.16.98',
      location: 'Berlin, DE',
      status: 'Protected'
    },
    {
      name: 'Windows PC',
      ip: '185.24.16.54',
      location: 'Warsaw, PL',
      status: 'Offline'
    }
  ];

  const payments = [
    {
      id: 'INV-2048',
      date: '2026-04-12',
      method: 'Visa •••• 4242',
      amount: '$9.99',
      status: 'Paid'
    },
    {
      id: 'INV-1922',
      date: '2026-03-12',
      method: 'Visa •••• 4242',
      amount: '$9.99',
      status: 'Paid'
    },
    {
      id: 'INV-1784',
      date: '2026-02-12',
      method: 'PayPal',
      amount: '$9.99',
      status: 'Paid'
    }
  ];

  const features = [
    'High-speed global VPN network',
    'No-logs privacy policy',
    'Unlimited bandwidth',
    'Streaming and gaming optimized',
    'Apps for all major devices',
    '24/7 customer support'
  ];
  const customerId = useMemo(() => {
    const storageKey = 'vaultvpn_customer_id';
    const existingId = window.localStorage.getItem(storageKey);
    if (existingId && /^\d+$/.test(existingId)) {
      return existingId;
    }
    const created = String(Math.floor(Date.now() + Math.random() * 1_000_000));
    window.localStorage.setItem(storageKey, created);
    return created;
  }, []);

  async function createPayment({ amountRub, planName }) {
    setPaymentError('');
    setIsPaying(true);

    const requestId = window.crypto?.randomUUID?.();

    try {
      const response = await fetch('/api/create-payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(requestId ? { 'Idempotence-Key': requestId } : {})
        },
        body: JSON.stringify({
          amount_rub: amountRub,
          plan_name: planName || null,
          user_id: customerId
        })
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload?.error || 'Payment creation failed');
      }
      if (!payload?.confirmation_url) {
        throw new Error('Payment confirmation URL is missing');
      }

      window.location.href = payload.confirmation_url;
    } catch (error) {
      setPaymentError(error instanceof Error ? error.message : 'Unexpected payment error');
    } finally {
      setIsPaying(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-500 text-lg font-bold text-slate-950">
              V
            </div>
            <div>
              <div className="text-lg font-semibold">VaultVPN</div>
              <div className="text-xs text-slate-400">Secure. Fast. Simple.</div>
            </div>
          </div>

          <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
            <a href="#features" className="transition hover:text-white">
              Features
            </a>
            <a href="#pricing" className="transition hover:text-white">
              Pricing
            </a>
            <a href="#account" className="transition hover:text-white">
              Personal Account
            </a>
            <a href="#support" className="transition hover:text-white">
              Support
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <button className="rounded-xl border border-white/15 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-white/30 hover:bg-white/5">
              Sign In
            </button>
            <button className="rounded-xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400">
              Get Started
            </button>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.18),transparent_28%),radial-gradient(circle_at_left,rgba(59,130,246,0.15),transparent_25%)]" />
          <div className="relative mx-auto grid max-w-7xl gap-10 px-6 py-20 lg:grid-cols-[1.15fr_0.85fr] lg:py-28">
            <div className="max-w-2xl">
              <div className="mb-6 inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300">
                Trusted by 120,000+ users worldwide
              </div>
              <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
                Private internet access with a dashboard your customers will actually
                use.
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-8 text-slate-300">
                Launch a modern VPN service with fast connections, secure browsing, and
                a polished personal account for subscriptions, devices, and payments.
              </p>

              <div className="mt-8 flex flex-col gap-4 sm:flex-row">
                <button className="rounded-2xl bg-emerald-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400">
                  Start Free Trial
                </button>
                <button className="rounded-2xl border border-white/15 px-6 py-3 font-semibold text-white transition hover:border-white/30 hover:bg-white/5">
                  View Demo Account
                </button>
              </div>

              <div className="mt-10 grid gap-4 sm:grid-cols-2">
                {features.map((feature) => (
                  <div
                    key={feature}
                    className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-200"
                  >
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-300">
                      ✓
                    </span>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-[28px] border border-white/10 bg-white/5 p-5 shadow-2xl shadow-black/20 backdrop-blur">
              <div className="rounded-[24px] border border-white/10 bg-slate-900/80 p-5">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <div>
                    <div className="text-sm text-slate-400">Current Session</div>
                    <div className="mt-1 text-xl font-semibold">
                      Protected via Netherlands
                    </div>
                  </div>
                  <div className="rounded-full bg-emerald-500/15 px-3 py-1 text-sm font-medium text-emerald-300">
                    Connected
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-4">
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-sm text-slate-400">New IP</div>
                    <div className="mt-2 text-lg font-semibold">185.24.16.72</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-sm text-slate-400">Speed</div>
                    <div className="mt-2 text-lg font-semibold">920 Mbps</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-sm text-slate-400">Encryption</div>
                    <div className="mt-2 text-lg font-semibold">AES-256</div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-sm text-slate-400">Uptime</div>
                    <div className="mt-2 text-lg font-semibold">99.99%</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="mx-auto max-w-7xl px-6 py-20">
          <div className="mb-10 flex items-end justify-between gap-6">
            <div>
              <div className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">
                Features
              </div>
              <h2 className="mt-3 text-3xl font-bold sm:text-4xl">
                Everything needed for a commercial VPN product
              </h2>
            </div>
            <p className="max-w-xl text-slate-400">
              This layout combines conversion-focused landing content with the client
              area users rely on after they subscribe.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            {[
              {
                title: 'Fast global network',
                text: 'Deploy premium routing across major regions with stable latency and smart server selection.'
              },
              {
                title: 'Subscription management',
                text: 'Users can top up balance, extend plans, and keep payment methods up to date.'
              },
              {
                title: 'Device control',
                text: 'View active sessions, revoke access, and manage concurrent device limits.'
              },
              {
                title: 'Billing history',
                text: 'Keep invoices, payment statuses, and renewal details visible in one place.'
              }
            ].map((item) => (
              <div
                key={item.title}
                className="rounded-[24px] border border-white/10 bg-white/5 p-6"
              >
                <div className="mb-4 h-12 w-12 rounded-2xl bg-emerald-500/15" />
                <h3 className="text-xl font-semibold">{item.title}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-400">{item.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="pricing" className="border-y border-white/10 bg-white/5">
          <div className="mx-auto max-w-7xl px-6 py-20">
            <div className="text-center">
              <div className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">
                Pricing
              </div>
              <h2 className="mt-3 text-3xl font-bold sm:text-4xl">
                Simple subscription plans
              </h2>
              <p className="mx-auto mt-4 max-w-2xl text-slate-400">
                Transparent billing, renewable balance, and clear value for monthly and
                yearly customers.
              </p>
            </div>

            <div className="mt-10 grid gap-6 md:grid-cols-3">
              {plansWithDisplayPrice.map((plan, index) => (
                <div
                  key={plan.name}
                  className={`rounded-[28px] border p-7 ${
                    index === 2
                      ? 'border-emerald-400 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                      : 'border-white/10 bg-slate-950/60'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-lg font-semibold">{plan.name}</div>
                      <div className="mt-2 text-4xl font-bold">{plan.price}</div>
                    </div>
                    {index === 2 && (
                      <div className="rounded-full bg-emerald-400 px-3 py-1 text-xs font-bold uppercase text-slate-950">
                        Popular
                      </div>
                    )}
                  </div>
                  <div className="mt-3 text-sm text-slate-400">{plan.note}</div>
                  <ul className="mt-6 space-y-3 text-sm text-slate-300">
                    <li>Up to 10 devices</li>
                    <li>All server locations</li>
                    <li>24/7 support</li>
                    <li>Instant activation</li>
                  </ul>
                  <button
                    onClick={() =>
                      createPayment({
                        amountRub: plan.priceRub,
                        planName: plan.name
                      })
                    }
                    disabled={isPaying}
                    className={`mt-8 w-full rounded-2xl px-5 py-3 font-semibold transition ${
                      index === 2
                        ? 'bg-emerald-500 text-slate-950 hover:bg-emerald-400'
                        : 'border border-white/10 bg-white/5 hover:bg-white/10'
                    } ${isPaying ? 'cursor-not-allowed opacity-70' : ''}`}
                  >
                    {isPaying ? 'Redirecting...' : 'Choose Plan'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="account" className="mx-auto max-w-7xl px-6 py-20">
          <div className="mb-8">
            <div className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">
              Personal Account
            </div>
            <h2 className="mt-3 text-3xl font-bold sm:text-4xl">Customer dashboard</h2>
            <p className="mt-4 max-w-3xl text-slate-400">
              A realistic account interface with wallet balance, device management, and
              payment history.
            </p>
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="space-y-6">
              <div className="rounded-[28px] border border-white/10 bg-white/5 p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-sm text-slate-400">Account Balance</div>
                    <div className="mt-2 text-4xl font-bold">$24.80</div>
                    <div className="mt-2 text-sm text-slate-400">
                      Next renewal: April 28, 2026
                    </div>
                  </div>
                  <div className="rounded-2xl bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-300">
                    Active Plan
                  </div>
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <button className="rounded-2xl bg-emerald-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400">
                    Top Up Balance
                  </button>
                  <button className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 font-semibold transition hover:bg-white/10">
                    Change Plan
                  </button>
                </div>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-white/5 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xl font-semibold">Quick Payment</div>
                    <div className="mt-1 text-sm text-slate-400">
                      Securely recharge balance or extend service
                    </div>
                  </div>
                  <div className="rounded-full bg-white/5 px-3 py-1 text-xs text-slate-300">
                    PCI Ready UI
                  </div>
                </div>

                <div className="mt-6 grid gap-4">
                  <div>
                    <label className="mb-2 block text-sm text-slate-300">Amount</label>
                    <input
                      value={customAmount}
                      onChange={(e) => setCustomAmount(e.target.value)}
                      className="w-full rounded-2xl border border-white/10 bg-slate-950 px-4 py-3 text-white outline-none ring-0 placeholder:text-slate-500 focus:border-emerald-400"
                    />
                  </div>
                  <div className="rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
                    После нажатия откроется защищенная страница ЮKassa для выбора метода оплаты.
                  </div>
                  {paymentError && (
                    <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
                      {paymentError}
                    </div>
                  )}
                  <button
                    onClick={() =>
                      createPayment({
                        amountRub: customAmount,
                        planName: 'Custom top up'
                      })
                    }
                    disabled={isPaying}
                    className={`rounded-2xl bg-emerald-500 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400 ${
                      isPaying ? 'cursor-not-allowed opacity-70' : ''
                    }`}
                  >
                    {isPaying ? 'Redirecting...' : 'Pay via YooKassa'}
                  </button>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-[28px] border border-white/10 bg-white/5 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xl font-semibold">Device List</div>
                    <div className="mt-1 text-sm text-slate-400">
                      Manage all linked devices and sessions
                    </div>
                  </div>
                  <button className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium hover:bg-white/5">
                    Add Device
                  </button>
                </div>

                <div className="mt-6 overflow-hidden rounded-2xl border border-white/10">
                  <div className="hidden grid-cols-[1.4fr_1fr_1fr_0.8fr] gap-4 bg-white/5 px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-400 md:grid">
                    <div>Device</div>
                    <div>IP</div>
                    <div>Location</div>
                    <div>Status</div>
                  </div>

                  <div className="divide-y divide-white/10">
                    {devices.map((device) => (
                      <div
                        key={device.name}
                        className="grid gap-3 px-5 py-4 md:grid-cols-[1.4fr_1fr_1fr_0.8fr] md:items-center"
                      >
                        <div>
                          <div className="font-medium">{device.name}</div>
                          <div className="mt-1 text-sm text-slate-400 md:hidden">
                            {device.ip} • {device.location}
                          </div>
                        </div>
                        <div className="hidden text-sm text-slate-300 md:block">
                          {device.ip}
                        </div>
                        <div className="hidden text-sm text-slate-300 md:block">
                          {device.location}
                        </div>
                        <div>
                          <span
                            className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                              device.status === 'Protected'
                                ? 'bg-emerald-500/15 text-emerald-300'
                                : 'bg-slate-700 text-slate-300'
                            }`}
                          >
                            {device.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="rounded-[28px] border border-white/10 bg-white/5 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xl font-semibold">Payment History</div>
                    <div className="mt-1 text-sm text-slate-400">
                      Recent invoices and successful charges
                    </div>
                  </div>
                  <button className="rounded-xl border border-white/10 px-4 py-2 text-sm font-medium hover:bg-white/5">
                    Download Invoices
                  </button>
                </div>

                <div className="mt-6 space-y-3">
                  {payments.map((payment) => (
                    <div
                      key={payment.id}
                      className="flex flex-col justify-between gap-4 rounded-2xl border border-white/10 bg-slate-950/60 p-4 sm:flex-row sm:items-center"
                    >
                      <div>
                        <div className="font-medium">{payment.id}</div>
                        <div className="mt-1 text-sm text-slate-400">
                          {payment.date} • {payment.method}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="font-semibold">{payment.amount}</div>
                          <div className="text-sm text-emerald-300">{payment.status}</div>
                        </div>
                        <button className="rounded-xl border border-white/10 px-4 py-2 text-sm hover:bg-white/5">
                          View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="support" className="border-t border-white/10 bg-white/5">
          <div className="mx-auto grid max-w-7xl gap-8 px-6 py-20 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="text-sm font-medium uppercase tracking-[0.2em] text-emerald-300">
                Support
              </div>
              <h2 className="mt-3 text-3xl font-bold sm:text-4xl">
                Need help with setup, billing, or devices?
              </h2>
              <p className="mt-4 max-w-2xl text-slate-400">
                Add live chat, documentation, and ticket management to support customers
                after purchase.
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row">
              <button className="rounded-2xl bg-emerald-500 px-6 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400">
                Contact Support
              </button>
              <button className="rounded-2xl border border-white/10 px-6 py-3 font-semibold transition hover:bg-white/5">
                Open Knowledge Base
              </button>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/10 bg-slate-950">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-8 text-sm text-slate-400 md:flex-row md:items-center md:justify-between">
          <div>© 2026 VaultVPN. All rights reserved.</div>
          <div className="flex gap-5">
            <a href="#" className="hover:text-white">
              Privacy Policy
            </a>
            <a href="#" className="hover:text-white">
              Terms of Service
            </a>
            <a href="#" className="hover:text-white">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
