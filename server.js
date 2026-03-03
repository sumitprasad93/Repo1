/**
 * FinTrack – Tink Open Banking Proxy Server
 *
 * This backend handles:
 *  1. OAuth2 code exchange  (POST /api/tink/token)
 *  2. Token refresh         (POST /api/tink/refresh)
 *  3. Accounts proxy        (GET  /api/tink/accounts)
 *  4. Transactions proxy    (GET  /api/tink/transactions)
 *  5. Balances proxy        (GET  /api/tink/balances)
 *  6. Callback handler      (GET  /callback)
 *
 * Setup:
 *   1. npm install express node-fetch dotenv cors
 *   2. Create .env (see .env.example)
 *   3. node server.js
 *
 * Tink docs: https://docs.tink.com/
 */

require('dotenv').config();
const express    = require('express');
const fetch      = require('node-fetch');
const cors       = require('cors');
const path       = require('path');

const app  = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cors({
  origin: process.env.ALLOWED_ORIGIN || 'http://localhost:3000',
  methods: ['GET','POST'],
}));

// Serve the dashboard HTML
app.use(express.static(path.join(__dirname)));

/* ══════════════════════════════════════════════════
   TINK CONSTANTS
   ══════════════════════════════════════════════════ */
const TINK_TOKEN_URL  = 'https://api.tink.com/api/v1/oauth/token';
const TINK_API_BASE   = 'https://api.tink.com';

const CLIENT_ID     = process.env.TINK_CLIENT_ID;
const CLIENT_SECRET = process.env.TINK_CLIENT_SECRET;

/* ══════════════════════════════════════════════════
   1. OAuth2 – Exchange authorization_code for tokens
   ══════════════════════════════════════════════════
   Called by your frontend after Tink redirects back
   to your redirectUri with ?code=AUTH_CODE

   Tink docs:
   https://docs.tink.com/api#connectivity/authentication/authorization-grant-delegate
   ══════════════════════════════════════════════════ */
app.post('/api/tink/token', async (req, res) => {
  const { code } = req.body;
  if (!code) return res.status(400).json({ error: 'Missing authorization code' });

  try {
    const body = new URLSearchParams({
      code,
      client_id:     CLIENT_ID,
      client_secret: CLIENT_SECRET,
      grant_type:    'authorization_code',
    });

    const response = await fetch(TINK_TOKEN_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });

    const data = await response.json();
    if (!response.ok) return res.status(response.status).json(data);

    // Return tokens to frontend.
    // In production: store refresh_token server-side, only send access_token.
    return res.json({
      access_token:  data.access_token,
      expires_in:    data.expires_in,   // seconds
      scope:         data.scope,
      token_type:    data.token_type,
    });
  } catch (err) {
    console.error('Token exchange error:', err);
    return res.status(500).json({ error: 'Token exchange failed' });
  }
});

/* ══════════════════════════════════════════════════
   2. OAuth2 – Refresh access_token
   ══════════════════════════════════════════════════ */
app.post('/api/tink/refresh', async (req, res) => {
  const { refresh_token } = req.body;
  if (!refresh_token) return res.status(400).json({ error: 'Missing refresh_token' });

  try {
    const body = new URLSearchParams({
      refresh_token,
      client_id:     CLIENT_ID,
      client_secret: CLIENT_SECRET,
      grant_type:    'refresh_token',
    });

    const response = await fetch(TINK_TOKEN_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });

    const data = await response.json();
    if (!response.ok) return res.status(response.status).json(data);
    return res.json({ access_token: data.access_token, expires_in: data.expires_in });
  } catch (err) {
    return res.status(500).json({ error: 'Token refresh failed' });
  }
});

/* ══════════════════════════════════════════════════
   HELPER: extract & validate Bearer token from header
   ══════════════════════════════════════════════════ */
function getBearerToken(req) {
  const auth = req.headers.authorization || '';
  if (!auth.startsWith('Bearer ')) return null;
  return auth.slice(7);
}

async function tinkGet(path, accessToken, queryParams = {}) {
  const qs  = new URLSearchParams(queryParams).toString();
  const url = TINK_API_BASE + path + (qs ? '?' + qs : '');
  return fetch(url, {
    headers: {
      Authorization:  'Bearer ' + accessToken,
      'Content-Type': 'application/json',
    },
  });
}

/* ══════════════════════════════════════════════════
   3. GET /api/tink/accounts
   ══════════════════════════════════════════════════
   Tink endpoint: GET /data/v2/accounts
   Scope required: accounts:read

   Response shape:
   {
     accounts: [{
       id, name, type,           // type: CHECKING | SAVINGS | CREDIT_CARD | LOAN | INVESTMENT
       balance: {
         amount: { value, currencyCode }
       },
       financialInstitutionId,
       identifiers: { iban: { iban } }
     }],
     nextPageToken
   }
   ══════════════════════════════════════════════════ */
app.get('/api/tink/accounts', async (req, res) => {
  const token = getBearerToken(req);
  if (!token) return res.status(401).json({ error: 'Missing Bearer token' });

  try {
    const r = await tinkGet('/data/v2/accounts', token, {
      pageSize: req.query.pageSize || 100,
    });
    const data = await r.json();
    if (!r.ok) return res.status(r.status).json(data);
    return res.json(data);
  } catch (err) {
    return res.status(500).json({ error: 'Failed to fetch accounts' });
  }
});

/* ══════════════════════════════════════════════════
   4. GET /api/tink/transactions
   ══════════════════════════════════════════════════
   Tink endpoint: GET /data/v2/transactions
   Scope required: transactions:read

   Query params:
     accountIdIn        – comma-separated account IDs
     bookedDateGte      – ISO date e.g. 2026-01-01
     bookedDateLte      – ISO date e.g. 2026-03-03
     pageSize           – max 100 per page
     pageToken          – for pagination

   Response shape:
   {
     transactions: [{
       id, accountId,
       amount: { value: { scale, unscaledValue }, currencyCode },
       dates: { booked, value },
       description,
       categories: { pfm: { id, name } },
       merchantInformation: { merchantName, merchantCategoryCode },
       status                // BOOKED | PENDING
     }],
     nextPageToken
   }
   ══════════════════════════════════════════════════ */
app.get('/api/tink/transactions', async (req, res) => {
  const token = getBearerToken(req);
  if (!token) return res.status(401).json({ error: 'Missing Bearer token' });

  try {
    const params = {
      pageSize:   req.query.pageSize   || 100,
      pageToken:  req.query.pageToken  || undefined,
    };
    if (req.query.accountIdIn)   params.accountIdIn   = req.query.accountIdIn;
    if (req.query.bookedDateGte) params.bookedDateGte = req.query.bookedDateGte;
    if (req.query.bookedDateLte) params.bookedDateLte = req.query.bookedDateLte;

    const r    = await tinkGet('/data/v2/transactions', token, params);
    const data = await r.json();
    if (!r.ok) return res.status(r.status).json(data);
    return res.json(data);
  } catch (err) {
    return res.status(500).json({ error: 'Failed to fetch transactions' });
  }
});

/* ══════════════════════════════════════════════════
   5. GET /api/tink/balances
   ══════════════════════════════════════════════════
   Tink endpoint: GET /data/v2/accounts/{id}/balances
   Scope required: balances:read
   ══════════════════════════════════════════════════ */
app.get('/api/tink/balances/:accountId', async (req, res) => {
  const token = getBearerToken(req);
  if (!token) return res.status(401).json({ error: 'Missing Bearer token' });

  try {
    const r    = await tinkGet(`/data/v2/accounts/${req.params.accountId}/balances`, token);
    const data = await r.json();
    if (!r.ok) return res.status(r.status).json(data);
    return res.json(data);
  } catch (err) {
    return res.status(500).json({ error: 'Failed to fetch balances' });
  }
});

/* ══════════════════════════════════════════════════
   6. OAuth2 callback – Tink redirects here with ?code=
   ══════════════════════════════════════════════════
   In production: exchange code for token server-side,
   store token in session/DB, redirect to dashboard.
   ══════════════════════════════════════════════════ */
app.get('/callback', async (req, res) => {
  const { code, state, error } = req.query;

  if (error) {
    return res.redirect(`/?error=${encodeURIComponent(error)}`);
  }

  if (!code) {
    return res.redirect('/?error=missing_code');
  }

  try {
    const body = new URLSearchParams({
      code,
      client_id:     CLIENT_ID,
      client_secret: CLIENT_SECRET,
      grant_type:    'authorization_code',
    });

    const tokenRes = await fetch(TINK_TOKEN_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });

    const tokenData = await tokenRes.json();
    if (!tokenRes.ok) {
      return res.redirect(`/?error=${encodeURIComponent(tokenData.error_description || 'token_error')}`);
    }

    // In production: save tokenData.access_token + refresh_token to session/DB
    // For demo: pass via URL fragment (not for production!)
    return res.redirect(`/dashboard.html#access_token=${tokenData.access_token}`);
  } catch (err) {
    console.error('Callback error:', err);
    return res.redirect('/?error=server_error');
  }
});

app.listen(PORT, () => {
  console.log(`\n  FinTrack Tink proxy running on http://localhost:${PORT}`);
  console.log(`  Dashboard: http://localhost:${PORT}/dashboard.html\n`);
});
