import { initializeApp, cert, getApps, App } from 'firebase-admin/app';
import { getDatabase, Database } from 'firebase-admin/database';
import { getFirestore, Firestore } from 'firebase-admin/firestore';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let firebaseApp: App | null = null;
let realtimeDb: Database | null = null;
let firestoreDb: Firestore | null = null;

// Initialize Firebase Admin (Realtime Database + Firestore)
export function getFirebaseAdmin(): { rtdb: Database | null; firestore: Firestore | null } {
  if (realtimeDb) return { rtdb: realtimeDb, firestore: firestoreDb };

  try {
    const credPath = path.join(__dirname, 'firebase-service-account.json');
    if (fs.existsSync(credPath)) {
      const serviceAccount = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
      if (getApps().length === 0) {
        firebaseApp = initializeApp({
          credential: cert(serviceAccount),
          databaseURL: 'https://james-bot-bf7df-default-rtdb.firebaseio.com',
          projectId: 'james-bot-bf7df'
        });
      } else {
        firebaseApp = getApps()[0];
      }

      realtimeDb = getDatabase(firebaseApp);
      try {
        firestoreDb = getFirestore(firebaseApp);
      } catch (e: any) {
        console.warn('[Firebase] Firestore init note:', e?.message || e);
      }
      console.log('[Firebase] Successfully connected to Firebase Project: james-bot-bf7df (RTDB & Firestore)');
    } else {
      console.warn('[Firebase] firebase-service-account.json not found');
    }
  } catch (err: any) {
    console.error('[Firebase] Initialization error:', err?.message || err);
  }

  return { rtdb: realtimeDb, firestore: firestoreDb };
}

export function getFirebaseFirestore(): Firestore | null {
  const { firestore } = getFirebaseAdmin();
  return firestore;
}

export function getFirebaseDatabase(): Database | null {
  const { rtdb } = getFirebaseAdmin();
  return rtdb;
}

// ── In-Memory Database Cached & Synced with Firebase ──────────────────────────
export interface User {
  id: number;
  username: string;
  role: 'admin' | 'manager' | 'agent' | 'client' | 'test';
  full_name: string;
  email: string;
  phone: string;
  status: 'active' | 'inactive' | 'suspended';
  parent_id: number | null;
  balances: { USD: number; EUR: number; GBP: number };
  api_token: string;
  created_at: string;
}

export interface RangeItem {
  id: number;
  manager_id: number;
  range_name: string;
  prefix: string;
  currency: string;
  payout_1_1: number;
  payout_7_1: number;
  payout_7_7: number;
  payout_30_45: number;
  test_number: string;
  total_numbers: number;
  available_numbers: number;
  memo: string;
  status: 'active' | 'inactive' | 'exhausted';
  request_enabled: number;
  created_at: string;
}

export interface PhoneNumber {
  id: number;
  range_id: number;
  range_name: string;
  number: string;
  assigned_to: number | null;
  assigned_username?: string;
  is_test: number;
  status: 'available' | 'assigned';
  payout_term: string;
  payout_rate: number;
  allocated_at: string;
}

export interface CDRItem {
  id: number;
  user_id: number;
  range_id: number;
  sender: string;
  recipient: string;
  message: string;
  otp_code: string;
  otp_detected: boolean;
  country: string;
  rate: number;
  payout: number;
  status: 'delivered' | 'received' | 'pending';
  created_at: string;
}

export interface NewsItem {
  id: number;
  title: string;
  content: string;
  author_id: number;
  target_role: string;
  status: string;
  created_at: string;
}

export interface PaymentItem {
  id: number;
  user_id: number;
  username: string;
  role: string;
  amount: number;
  currency: string;
  payment_method: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

export interface ActivityItem {
  id: number;
  user_id: number | null;
  username: string;
  action: string;
  description: string;
  ip: string;
  created_at: string;
}

export const USERS: User[] = [];
export const RANGES: RangeItem[] = [];
export const NUMBERS: PhoneNumber[] = [];
export const CDRS: CDRItem[] = [];
export const NEWS: NewsItem[] = [];
export const PAYMENTS: PaymentItem[] = [];
export const ACTIVITIES: ActivityItem[] = [];
export let SETTINGS = {
  site_name: 'IMS PRO',
  support_email: 'support@imspro.com',
  telegram_url: 'https://t.me/IMSPROSMS',
  whatsapp_url: 'https://api.whatsapp.com/send?text=Hello%20IMS%20PRO%20Support',
  skype_id: 'imspro_support',
  emergency_announcement: '⚡ Myanmar, UK & USA OTP routes are operating at 99.8% delivery speed. Special commission active!',
  emergency_announcement_active: true,
  default_currency: 'USD',
  maintenance_mode: false,
  maintenance_message: 'System is currently under scheduled maintenance. We will be back online shortly.',
  payout_min: 50.0,
  profit_markup_percent: 10.0
};

export const SMPP_ACCOUNTS = [
  {
    id: 1,
    system_id: 'smpp_carrier_eu',
    password: '••••••••',
    client_name: 'Carrier EU Transit',
    max_binds: 5,
    tps: 200,
    bind_type: 'TRX',
    status: 'bound',
    connected_ips: ['185.120.44.12'],
    messages_today: 14280,
    dlr_ratio: '99.4%'
  },
  {
    id: 2,
    system_id: 'smpp_direct_us',
    password: '••••••••',
    client_name: 'US Direct Hub',
    max_binds: 8,
    tps: 350,
    bind_type: 'TRX',
    status: 'bound',
    connected_ips: ['198.51.100.84'],
    messages_today: 23150,
    dlr_ratio: '99.8%'
  }
];

// Initial seed data if Firebase tables are fresh
export const SEED_USERS: User[] = [
  {
    id: 1,
    username: 'admin',
    role: 'admin',
    full_name: 'System Administrator',
    email: 'admin@imspro.com',
    phone: '+12025550100',
    status: 'active',
    parent_id: null,
    balances: { USD: 125400.5, EUR: 45000.0, GBP: 18200.0 },
    api_token: 'ims_admin_tok_84920',
    created_at: '2026-01-15 00:00:00'
  },
  {
    id: 2,
    username: 'admin01619789895',
    role: 'manager',
    full_name: 'Alex Rivera (Global Ops)',
    email: 'manager@imspro.com',
    phone: '+447911123456',
    status: 'active',
    parent_id: 1,
    balances: { USD: 28450.0, EUR: 12300.0, GBP: 6400.0 },
    api_token: 'ims_manager_tok_9918',
    created_at: '2026-02-01 10:00:00'
  },
  {
    id: 3,
    username: 'james9999',
    role: 'agent',
    full_name: 'David Chen (Tier 1)',
    email: 'agent1@imspro.com',
    phone: '+447922234567',
    status: 'active',
    parent_id: 2,
    balances: { USD: 8920.75, EUR: 3100.0, GBP: 1200.0 },
    api_token: 'ims_agent_tok_4431',
    created_at: '2026-02-10 11:30:00'
  },
  {
    id: 4,
    username: 'client1',
    role: 'client',
    full_name: 'Sigma Telecom UK',
    email: 'client1@imspro.com',
    phone: '+447933345678',
    status: 'active',
    parent_id: 3,
    balances: { USD: 3410.2, EUR: 950.0, GBP: 450.0 },
    api_token: 'ims_client_tok_1102',
    created_at: '2026-03-01 14:15:00'
  },
  {
    id: 5,
    username: 'client2',
    role: 'client',
    full_name: 'Apex Media Solutions',
    email: 'client2@apexmedia.io',
    phone: '+447944456789',
    status: 'active',
    parent_id: 3,
    balances: { USD: 1850.0, EUR: 400.0, GBP: 200.0 },
    api_token: 'ims_client_tok_7721',
    created_at: '2026-03-05 09:20:00'
  },
  {
    id: 6,
    username: 'test1',
    role: 'test',
    full_name: 'QA Tester Account',
    email: 'test@imspro.com',
    phone: '+12025550199',
    status: 'active',
    parent_id: 1,
    balances: { USD: 100.0, EUR: 100.0, GBP: 100.0 },
    api_token: 'ims_test_tok_8899',
    created_at: '2026-03-10 16:00:00'
  }
];

export const SEED_RANGES: RangeItem[] = [
  {
    id: 1,
    manager_id: 2,
    range_name: 'UK Premium Mobile (447)',
    prefix: '447',
    currency: 'USD',
    payout_1_1: 0.055,
    payout_7_1: 0.048,
    payout_7_7: 0.042,
    payout_30_45: 0.038,
    test_number: '+447123456701',
    total_numbers: 250,
    available_numbers: 184,
    memo: 'High delivery rate for OTP & 2FA',
    status: 'active',
    request_enabled: 1,
    created_at: '2026-02-01 12:00:00'
  },
  {
    id: 2,
    manager_id: 2,
    range_name: 'US Virtual Tier 1 (1202)',
    prefix: '1202',
    currency: 'USD',
    payout_1_1: 0.045,
    payout_7_1: 0.039,
    payout_7_7: 0.034,
    payout_30_45: 0.03,
    test_number: '+12025550123',
    total_numbers: 500,
    available_numbers: 420,
    memo: 'Direct SMPP bind to US carriers',
    status: 'active',
    request_enabled: 1,
    created_at: '2026-02-05 12:00:00'
  },
  {
    id: 3,
    manager_id: 2,
    range_name: 'Germany Mobile Direct (4915)',
    prefix: '4915',
    currency: 'EUR',
    payout_1_1: 0.062,
    payout_7_1: 0.055,
    payout_7_7: 0.049,
    payout_30_45: 0.044,
    test_number: '+491512345678',
    total_numbers: 150,
    available_numbers: 112,
    memo: 'Deutsche Telekom & Vodafone routes',
    status: 'active',
    request_enabled: 1,
    created_at: '2026-02-12 10:00:00'
  },
  {
    id: 4,
    manager_id: 2,
    range_name: 'France Orange/SFR (336)',
    prefix: '336',
    currency: 'EUR',
    payout_1_1: 0.058,
    payout_7_1: 0.05,
    payout_7_7: 0.045,
    payout_30_45: 0.04,
    test_number: '+33612345678',
    total_numbers: 300,
    available_numbers: 245,
    memo: 'High volume OTP routes',
    status: 'active',
    request_enabled: 1,
    created_at: '2026-02-18 15:00:00'
  },
  {
    id: 5,
    manager_id: 2,
    range_name: 'Myanmar MPT / Ooredoo (959)',
    prefix: '959',
    currency: 'USD',
    payout_1_1: 0.001,
    payout_7_1: 0.0009,
    payout_7_7: 0.0008,
    payout_30_45: 0.0007,
    test_number: '+95977123456',
    total_numbers: 150,
    available_numbers: 130,
    memo: 'Myanmar TikTok & Social OTP Direct Route ($0.001)',
    status: 'active',
    request_enabled: 1,
    created_at: '2026-03-01 10:00:00'
  }
];

export const SEED_NUMBERS: PhoneNumber[] = [
  {
    id: 1,
    range_id: 1,
    range_name: 'UK Premium Mobile (447)',
    number: '+447123456701',
    assigned_to: null,
    is_test: 1,
    status: 'available',
    payout_term: '1/1',
    payout_rate: 0.055,
    allocated_at: '2026-02-01 12:00:00'
  },
  {
    id: 2,
    range_id: 1,
    range_name: 'UK Premium Mobile (447)',
    number: '+447123456702',
    assigned_to: 4,
    assigned_username: 'client1',
    is_test: 0,
    status: 'assigned',
    payout_term: '7/1',
    payout_rate: 0.048,
    allocated_at: '2026-02-15 14:00:00'
  },
  {
    id: 3,
    range_id: 1,
    range_name: 'UK Premium Mobile (447)',
    number: '+447123456703',
    assigned_to: 4,
    assigned_username: 'client1',
    is_test: 0,
    status: 'assigned',
    payout_term: '7/1',
    payout_rate: 0.048,
    allocated_at: '2026-02-15 14:00:00'
  },
  {
    id: 4,
    range_id: 1,
    range_name: 'UK Premium Mobile (447)',
    number: '+447123456704',
    assigned_to: 5,
    assigned_username: 'client2',
    is_test: 0,
    status: 'assigned',
    payout_term: '1/1',
    payout_rate: 0.055,
    allocated_at: '2026-03-05 10:00:00'
  },
  {
    id: 5,
    range_id: 2,
    range_name: 'US Virtual Tier 1 (1202)',
    number: '+12025550123',
    assigned_to: null,
    is_test: 1,
    status: 'available',
    payout_term: '1/1',
    payout_rate: 0.045,
    allocated_at: '2026-02-05 12:00:00'
  },
  {
    id: 6,
    range_id: 2,
    range_name: 'US Virtual Tier 1 (1202)',
    number: '+12025550124',
    assigned_to: 4,
    assigned_username: 'client1',
    is_test: 0,
    status: 'assigned',
    payout_term: '7/1',
    payout_rate: 0.039,
    allocated_at: '2026-02-20 16:30:00'
  },
  {
    id: 7,
    range_id: 3,
    range_name: 'Germany Mobile Direct (4915)',
    number: '+491512345678',
    assigned_to: null,
    is_test: 1,
    status: 'available',
    payout_term: '1/1',
    payout_rate: 0.062,
    allocated_at: '2026-02-12 10:00:00'
  },
  {
    id: 8,
    range_id: 3,
    range_name: 'Germany Mobile Direct (4915)',
    number: '+491512345679',
    assigned_to: 5,
    assigned_username: 'client2',
    is_test: 0,
    status: 'assigned',
    payout_term: '7/1',
    payout_rate: 0.055,
    allocated_at: '2026-03-06 11:20:00'
  },
  {
    id: 9,
    range_id: 5,
    range_name: 'Myanmar MPT / Ooredoo (959)',
    number: '+95977123456',
    assigned_to: null,
    is_test: 1,
    status: 'available',
    payout_term: '1/1',
    payout_rate: 0.001,
    allocated_at: '2026-03-01 10:00:00'
  }
];

export const SEED_NEWS: NewsItem[] = [
  {
    id: 1,
    title: 'Welcome to IMS PRO Platform',
    content: 'We have upgraded all SMPP endpoints for high concurrency and sub-second OTP verification.',
    author_id: 1,
    target_role: 'all',
    status: 'published',
    created_at: '2026-03-01 09:00:00'
  },
  {
    id: 2,
    title: 'New High-Converting UK Ranges Available',
    content: 'UK Mobile ranges (447) are now live with 1/1 daily payouts and full WhatsApp & Telegram support.',
    author_id: 1,
    target_role: 'agent',
    status: 'published',
    created_at: '2026-03-15 14:30:00'
  }
];

export const SEED_PAYMENTS: PaymentItem[] = [
  {
    id: 1,
    user_id: 4,
    username: 'client1',
    role: 'client',
    amount: 1450.0,
    currency: 'USD',
    payment_method: 'USDT (TRC20)',
    status: 'approved',
    created_at: '2026-03-10 11:20:00'
  },
  {
    id: 2,
    user_id: 5,
    username: 'client2',
    role: 'client',
    amount: 820.0,
    currency: 'USD',
    payment_method: 'Bank Wire',
    status: 'pending',
    created_at: '2026-03-24 16:45:00'
  }
];

// Helper to convert Firebase RTDB snapshot map/array to typed array
function snapshotToArray<T extends { id: number }>(val: any, fallback: T[]): T[] {
  if (!val) return [...fallback];
  if (Array.isArray(val)) {
    return val.filter(Boolean) as T[];
  }
  if (typeof val === 'object') {
    return Object.values(val) as T[];
  }
  return [...fallback];
}

// ── Master Sync from Firebase (RTDB & Firestore) on Server Startup ────────────
export async function syncFromFirestore() {
  return syncFromFirebase();
}

export async function syncFromFirebase() {
  const { rtdb, firestore } = getFirebaseAdmin();

  console.log('[Firebase] Synchronizing IMS PRO data with Firebase...');

  if (rtdb) {
    try {
      // 1. Users
      const usersSnap = await rtdb.ref('users').once('value');
      const usersVal = usersSnap.val();
      if (!usersVal || Object.keys(usersVal).length === 0) {
        console.log('[Firebase] Seeding initial users into Firebase...');
        const userMap: Record<string, User> = {};
        for (const u of SEED_USERS) {
          userMap[String(u.id)] = u;
          USERS.push(u);
        }
        await rtdb.ref('users').set(userMap);
      } else {
        USERS.length = 0;
        const loadedUsers = snapshotToArray<User>(usersVal, SEED_USERS);
        USERS.push(...loadedUsers);
        USERS.sort((a, b) => a.id - b.id);

        // Ensure Manager and Agent usernames match requested credentials in RTDB & memory
        const mgr = USERS.find((u) => u.role === 'manager' || u.id === 2);
        if (mgr) {
          mgr.username = 'admin01619789895';
          mgr.full_name = 'Manager (admin01619789895)';
          rtdb.ref(`users/${mgr.id}`).set(mgr).catch(() => {});
        }
        const agt = USERS.find((u) => u.role === 'agent' || u.id === 3);
        if (agt) {
          agt.username = 'james9999';
          agt.full_name = 'Agent (james9999)';
          rtdb.ref(`users/${agt.id}`).set(agt).catch(() => {});
        }
      }

      // 2. Ranges
      const rangesSnap = await rtdb.ref('ranges').once('value');
      const rangesVal = rangesSnap.val();
      if (!rangesVal || Object.keys(rangesVal).length === 0) {
        const rangeMap: Record<string, RangeItem> = {};
        for (const r of SEED_RANGES) {
          rangeMap[String(r.id)] = r;
          RANGES.push(r);
        }
        await rtdb.ref('ranges').set(rangeMap);
      } else {
        RANGES.length = 0;
        const loadedRanges = snapshotToArray<RangeItem>(rangesVal, SEED_RANGES);
        RANGES.push(...loadedRanges);
        RANGES.sort((a, b) => a.id - b.id);
      }

      // 3. Numbers
      const numbersSnap = await rtdb.ref('numbers').once('value');
      const numbersVal = numbersSnap.val();
      if (!numbersVal || Object.keys(numbersVal).length === 0) {
        const numMap: Record<string, PhoneNumber> = {};
        for (const n of SEED_NUMBERS) {
          numMap[String(n.id)] = n;
          NUMBERS.push(n);
        }
        await rtdb.ref('numbers').set(numMap);
      } else {
        NUMBERS.length = 0;
        const loadedNums = snapshotToArray<PhoneNumber>(numbersVal, SEED_NUMBERS);
        NUMBERS.push(...loadedNums);
        NUMBERS.sort((a, b) => a.id - b.id);
      }

      // 4. CDR / SMS Logs
      const cdrSnap = await rtdb.ref('cdr').limitToLast(100).once('value');
      const cdrVal = cdrSnap.val();
      if (!cdrVal || Object.keys(cdrVal).length === 0) {
        console.log('[Firebase] Generating realistic CDR records for Firebase...');
        const cdrMap: Record<string, CDRItem> = {};
        const senders = ['WhatsApp', 'Telegram', 'Google', 'Uber', 'BankAuth', 'TikTok', 'Instagram', 'Microsoft'];
        const today = new Date();

        for (let k = 0; k < 25; k++) {
          const isOtp = Math.random() > 0.1;
          const code = Math.floor(100000 + Math.random() * 900000).toString();
          const sender = senders[Math.floor(Math.random() * senders.length)];
          const numObj = NUMBERS[k % NUMBERS.length] || SEED_NUMBERS[0];
          const dt = new Date(today.getTime() - k * 3600000);
          const timeStr = dt.toISOString().replace('T', ' ').slice(0, 19);

          const item: CDRItem = {
            id: k + 1,
            user_id: numObj.assigned_to || 4,
            range_id: numObj.range_id,
            sender,
            recipient: numObj.number,
            message: `Your IMS PRO security code is ${code}. Never share your code with anyone.`,
            otp_code: code,
            otp_detected: isOtp,
            country: numObj.number.startsWith('+44') ? 'United Kingdom' : numObj.number.startsWith('+1') ? 'United States' : 'Germany',
            rate: numObj.payout_rate || 0.05,
            payout: numObj.payout_rate || 0.05,
            status: 'delivered',
            created_at: timeStr
          };
          cdrMap[String(item.id)] = item;
          CDRS.unshift(item);
        }
        await rtdb.ref('cdr').set(cdrMap);
      } else {
        CDRS.length = 0;
        const loadedCdr = snapshotToArray<CDRItem>(cdrVal, []);
        CDRS.push(...loadedCdr);
        CDRS.sort((a, b) => b.id - a.id);
      }

      // 5. News
      const newsSnap = await rtdb.ref('news').once('value');
      const newsVal = newsSnap.val();
      if (!newsVal || Object.keys(newsVal).length === 0) {
        const newsMap: Record<string, NewsItem> = {};
        for (const n of SEED_NEWS) {
          newsMap[String(n.id)] = n;
          NEWS.push(n);
        }
        await rtdb.ref('news').set(newsMap);
      } else {
        NEWS.length = 0;
        const loadedNews = snapshotToArray<NewsItem>(newsVal, SEED_NEWS);
        NEWS.push(...loadedNews);
        NEWS.sort((a, b) => b.id - a.id);
      }

      // 6. Payments
      const paySnap = await rtdb.ref('payments').once('value');
      const payVal = paySnap.val();
      if (!payVal || Object.keys(payVal).length === 0) {
        const payMap: Record<string, PaymentItem> = {};
        for (const p of SEED_PAYMENTS) {
          payMap[String(p.id)] = p;
          PAYMENTS.push(p);
        }
        await rtdb.ref('payments').set(payMap);
      } else {
        PAYMENTS.length = 0;
        const loadedPay = snapshotToArray<PaymentItem>(payVal, SEED_PAYMENTS);
        PAYMENTS.push(...loadedPay);
        PAYMENTS.sort((a, b) => b.id - a.id);
      }

      // 7. Settings
      const settingsSnap = await rtdb.ref('settings/general').once('value');
      const settingsVal = settingsSnap.val();
      if (!settingsVal) {
        await rtdb.ref('settings/general').set(SETTINGS);
      } else {
        SETTINGS = { ...SETTINGS, ...settingsVal };
      }

      // 8. Activities
      const actSnap = await rtdb.ref('activities').limitToLast(50).once('value');
      const actVal = actSnap.val();
      if (actVal) {
        ACTIVITIES.length = 0;
        const loadedAct = snapshotToArray<ActivityItem>(actVal, []);
        ACTIVITIES.push(...loadedAct);
        ACTIVITIES.sort((a, b) => b.id - a.id);
      }

      console.log(`[Firebase RTDB] Synced successfully! Loaded ${USERS.length} users, ${NUMBERS.length} numbers, ${RANGES.length} ranges, ${CDRS.length} CDRs.`);
    } catch (err: any) {
      console.error('[Firebase RTDB] Sync error:', err?.message || err);
      fallbackPopulateMemory();
    }
  } else {
    fallbackPopulateMemory();
  }

  // Mirror to Firestore in background without blocking server
  if (firestore) {
    mirrorToFirestoreInBackground(firestore).catch((err) => {
      console.warn('[Firebase Firestore] Background mirror note:', err?.message || err);
    });
  }
}

function fallbackPopulateMemory() {
  if (USERS.length === 0) USERS.push(...SEED_USERS);
  if (RANGES.length === 0) RANGES.push(...SEED_RANGES);
  if (NUMBERS.length === 0) NUMBERS.push(...SEED_NUMBERS);
  if (NEWS.length === 0) NEWS.push(...SEED_NEWS);
  if (PAYMENTS.length === 0) PAYMENTS.push(...SEED_PAYMENTS);
}

async function mirrorToFirestoreInBackground(db: Firestore) {
  try {
    const userSnap = await db.collection('users').limit(1).get();
    if (userSnap.empty) {
      const batch = db.batch();
      for (const u of USERS) {
        batch.set(db.collection('users').doc(String(u.id)), u);
      }
      for (const r of RANGES) {
        batch.set(db.collection('ranges').doc(String(r.id)), r);
      }
      for (const n of NUMBERS) {
        batch.set(db.collection('numbers').doc(String(n.id)), n);
      }
      await batch.commit();
      console.log('[Firebase Firestore] Seeded initial collections to Firestore.');
    }
  } catch (err: any) {
    // Non-fatal
  }
}

// ── Persistence Helpers for Real-Time Synchronization ────────────────────────
export async function persistUser(user: User): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`users/${user.id}`).set(user);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist user to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('users').doc(String(user.id)).set(user, { merge: true });
    } catch (err: any) {
      // Non-fatal
    }
  }
}

export async function deleteUserFromFirebase(id: number): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`users/${id}`).remove();
    } catch (err: any) {
      console.error('[Firebase] Failed to delete user from RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('users').doc(String(id)).delete();
    } catch (err: any) {}
  }
}

export async function persistNumber(num: PhoneNumber): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`numbers/${num.id}`).set(num);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist number to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('numbers').doc(String(num.id)).set(num, { merge: true });
    } catch (err: any) {}
  }
}

export async function persistRange(range: RangeItem): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`ranges/${range.id}`).set(range);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist range to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('ranges').doc(String(range.id)).set(range, { merge: true });
    } catch (err: any) {}
  }
}

export async function deleteRangeFromFirebase(id: number): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`ranges/${id}`).remove();
    } catch (err: any) {
      console.error('[Firebase] Failed to delete range from RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('ranges').doc(String(id)).delete();
    } catch (err: any) {}
  }
}

export async function persistCDR(cdr: CDRItem): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`cdr/${cdr.id}`).set(cdr);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist CDR to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('cdr').doc(String(cdr.id)).set(cdr);
    } catch (err: any) {}
  }
}

export async function persistPayment(payment: PaymentItem): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`payments/${payment.id}`).set(payment);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist payment to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('payments').doc(String(payment.id)).set(payment, { merge: true });
    } catch (err: any) {}
  }
}

export async function persistNews(news: NewsItem): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`news/${news.id}`).set(news);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist news to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('news').doc(String(news.id)).set(news, { merge: true });
    } catch (err: any) {}
  }
}

export async function deleteNewsFromFirebase(id: number): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`news/${id}`).remove();
    } catch (err: any) {
      console.error('[Firebase] Failed to delete news from RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('news').doc(String(id)).delete();
    } catch (err: any) {}
  }
}

export async function persistActivity(act: ActivityItem): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`activities/${act.id}`).set(act);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist activity to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('activity').doc(String(act.id)).set(act);
    } catch (err: any) {}
  }
}

export async function persistSettings(settings: typeof SETTINGS): Promise<void> {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref('settings/general').set(settings);
    } catch (err: any) {
      console.error('[Firebase] Failed to persist settings to RTDB:', err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection('settings').doc('general').set(settings, { merge: true });
    } catch (err: any) {}
  }
}
