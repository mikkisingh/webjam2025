# MediCheck — Payment System Setup Guide

## Overview

MediCheck uses Stripe Checkout for one-time credit pack purchases. Users get 1 free scan, then buy credits: $0.99/scan, 5-pack $4.49, 20-pack $14.99.

---

## Step 1: Run Supabase Schema Migration

Go to **Supabase Dashboard > SQL Editor > New query** and run the following (also found in `supabase_schema.sql`):

```sql
-- PROFILES TABLE
create table if not exists profiles (
  user_id         uuid references auth.users(id) on delete cascade primary key,
  scan_credits    integer default 0 not null,
  free_scan_used  boolean default false not null,
  total_scans     integer default 0 not null,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now()
);

alter table profiles enable row level security;

create policy "Users can view their own profile"
  on profiles for select
  using (auth.uid() = user_id);

-- PURCHASES TABLE
create table if not exists purchases (
  id                    uuid default uuid_generate_v4() primary key,
  user_id               uuid references auth.users(id) on delete cascade not null,
  stripe_session_id     text unique not null,
  stripe_payment_intent text,
  price_id              text not null,
  credits_purchased     integer not null,
  amount_cents          integer not null,
  status                text default 'completed' not null,
  created_at            timestamptz default now()
);

alter table purchases enable row level security;

create policy "Users can view their own purchases"
  on purchases for select
  using (auth.uid() = user_id);

-- AUTO-CREATE PROFILE ON SIGNUP
create or replace function handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (user_id)
  values (new.id)
  on conflict (user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- BACKFILL PROFILES FOR EXISTING USERS
insert into profiles (user_id)
select id from auth.users
on conflict (user_id) do nothing;
```

---

## Step 2: Create Stripe Account & Products

### 2a. Create Stripe Account
1. Go to https://dashboard.stripe.com/register
2. Complete onboarding (business info, bank account for payouts)
3. Start in **Test Mode** (toggle in top-right of dashboard)

### 2b. Create Products and Prices
Go to **Products > Add product** and create three products:

| Product Name | Price | Type | Metadata |
|---|---|---|---|
| MediCheck Single Scan | $0.99 | One-time | `credits: 1` |
| MediCheck 5-Pack | $4.49 | One-time | `credits: 5` |
| MediCheck 20-Pack | $14.99 | One-time | `credits: 20` |

After creating each, copy the **Price ID** (starts with `price_`).

### 2c. Set Up Webhook
1. Go to **Developers > Webhooks > Add endpoint**
2. Endpoint URL: `https://your-backend-domain.com/stripe/webhook`
3. Select event: `checkout.session.completed`
4. Click **Add endpoint**
5. Copy the **Signing secret** (starts with `whsec_`)

For local testing, use the Stripe CLI:
```bash
stripe listen --forward-to localhost:5001/stripe/webhook
```
This will print a webhook signing secret for local use.

### 2d. Get API Keys
Go to **Developers > API Keys**:
- **Secret key** (starts with `sk_test_` or `sk_live_`)
- **Publishable key** — not needed (we use Checkout Sessions, not client-side Stripe.js)

---

## Step 3: Configure Environment Variables

### Backend (`backend/.env`)
```env
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PRICE_SINGLE=price_xxxxxxxxxxxxxx
STRIPE_PRICE_5PACK=price_xxxxxxxxxxxxxx
STRIPE_PRICE_20PACK=price_xxxxxxxxxxxxxx
FRONTEND_URL=http://localhost:5173
```

### Frontend (`frontend/.env`)
```env
VITE_STRIPE_PRICE_SINGLE=price_xxxxxxxxxxxxxx
VITE_STRIPE_PRICE_5PACK=price_xxxxxxxxxxxxxx
VITE_STRIPE_PRICE_20PACK=price_xxxxxxxxxxxxxx
```

The frontend price IDs must match the backend ones. They are public (safe to expose).

---

## Step 4: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt  # includes stripe==12.1.0
```

---

## Step 5: Test the Flow

1. Start backend: `cd backend && python run.py`
2. Start frontend: `cd frontend && npm run dev`
3. Sign up / sign in
4. Navigate to **Scan Bill**
5. Upload a file — your first scan should be free
6. After the free scan, click **Upload & Analyze** again — the purchase modal should appear
7. Click **Buy Now** on any pack
8. On the Stripe Checkout page, use test card: `4242 4242 4242 4242` (any future expiry, any CVC)
9. After payment, you'll be redirected back with credits added

---

## Step 6: Go Live

1. Toggle Stripe from **Test Mode** to **Live Mode** in the dashboard
2. Create the same 3 products/prices in Live Mode
3. Set up the webhook for Live Mode
4. Replace all `sk_test_` and `price_` values with live ones in your environment
5. Update `FRONTEND_URL` to your production domain
6. Deploy

---

## Troubleshooting

| Issue | Fix |
|---|---|
| "Payments not configured" error | Check `STRIPE_SECRET_KEY` is set in backend `.env` |
| "Invalid price selected" | Ensure `STRIPE_PRICE_*` env vars match between frontend and backend |
| Credits not added after payment | Check webhook is receiving events (Stripe Dashboard > Webhooks > Recent events). Ensure `STRIPE_WEBHOOK_SECRET` is correct |
| Webhook signature verification fails | Make sure you're using the correct signing secret (different for test vs live, and different for CLI vs dashboard) |
| Profile not found | Run the backfill SQL or ensure the trigger is created |

---

## Architecture Notes

- **Backend** handles all credit modifications via Supabase REST API with `service_role` key (bypasses RLS)
- **Frontend** can only READ credit balance (RLS enforced — SELECT policy only on `profiles`)
- **Webhook** is idempotent — `stripe_session_id` has a UNIQUE constraint, preventing double-crediting
- **Credit deduction** happens BEFORE the LLM analysis call — credits are consumed even if the analysis fails (prevents abuse)
