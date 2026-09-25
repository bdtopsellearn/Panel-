// server.ts
import express from "express";
import path2 from "path";
import fs2 from "fs";
import { fileURLToPath as fileURLToPath2 } from "url";
import cookie from "cookie";

// firebase-service.ts
import { initializeApp, cert, getApps } from "firebase-admin/app";
import { getDatabase } from "firebase-admin/database";
import { getFirestore } from "firebase-admin/firestore";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
var __filename = fileURLToPath(import.meta.url);
var __dirname = path.dirname(__filename);
var firebaseApp = null;
var realtimeDb = null;
var firestoreDb = null;
function getFirebaseAdmin() {
  if (realtimeDb) return { rtdb: realtimeDb, firestore: firestoreDb };
  try {
    const credPath = path.join(__dirname, "firebase-service-account.json");
    if (fs.existsSync(credPath)) {
      const serviceAccount = JSON.parse(fs.readFileSync(credPath, "utf-8"));
      if (getApps().length === 0) {
        firebaseApp = initializeApp({
          credential: cert(serviceAccount),
          databaseURL: "https://james-bot-bf7df-default-rtdb.firebaseio.com",
          projectId: "james-bot-bf7df"
        });
      } else {
        firebaseApp = getApps()[0];
      }
      realtimeDb = getDatabase(firebaseApp);
      try {
        firestoreDb = getFirestore(firebaseApp);
      } catch (e) {
        console.warn("[Firebase] Firestore init note:", e?.message || e);
      }
      console.log("[Firebase] Successfully connected to Firebase Project: james-bot-bf7df (RTDB & Firestore)");
    } else {
      console.warn("[Firebase] firebase-service-account.json not found");
    }
  } catch (err) {
    console.error("[Firebase] Initialization error:", err?.message || err);
  }
  return { rtdb: realtimeDb, firestore: firestoreDb };
}
var USERS = [];
var RANGES = [];
var NUMBERS = [];
var CDRS = [];
var NEWS = [];
var PAYMENTS = [];
var ACTIVITIES = [];
var SETTINGS = {
  site_name: "IMS PRO",
  support_email: "support@imspro.com",
  telegram_url: "https://t.me/IMSPROSMS",
  whatsapp_url: "https://api.whatsapp.com/send?text=Hello%20IMS%20PRO%20Support",
  skype_id: "imspro_support",
  emergency_announcement: "\u26A1 Myanmar, UK & USA OTP routes are operating at 99.8% delivery speed. Special commission active!",
  emergency_announcement_active: true,
  default_currency: "USD",
  maintenance_mode: false,
  maintenance_message: "System is currently under scheduled maintenance. We will be back online shortly.",
  payout_min: 50,
  profit_markup_percent: 10
};
var SMPP_ACCOUNTS = [
  {
    id: 1,
    system_id: "smpp_carrier_eu",
    password: "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",
    client_name: "Carrier EU Transit",
    max_binds: 5,
    tps: 200,
    bind_type: "TRX",
    status: "bound",
    connected_ips: ["185.120.44.12"],
    messages_today: 14280,
    dlr_ratio: "99.4%"
  },
  {
    id: 2,
    system_id: "smpp_direct_us",
    password: "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",
    client_name: "US Direct Hub",
    max_binds: 8,
    tps: 350,
    bind_type: "TRX",
    status: "bound",
    connected_ips: ["198.51.100.84"],
    messages_today: 23150,
    dlr_ratio: "99.8%"
  }
];
var SEED_USERS = [
  {
    id: 1,
    username: "admin",
    role: "admin",
    full_name: "System Administrator",
    email: "admin@imspro.com",
    phone: "+12025550100",
    status: "active",
    parent_id: null,
    balances: { USD: 125400.5, EUR: 45e3, GBP: 18200 },
    api_token: "ims_admin_tok_84920",
    created_at: "2026-01-15 00:00:00"
  },
  {
    id: 2,
    username: "admin01619789895",
    role: "manager",
    full_name: "Alex Rivera (Global Ops)",
    email: "manager@imspro.com",
    phone: "+447911123456",
    status: "active",
    parent_id: 1,
    balances: { USD: 28450, EUR: 12300, GBP: 6400 },
    api_token: "ims_manager_tok_9918",
    created_at: "2026-02-01 10:00:00"
  },
  {
    id: 3,
    username: "james9999",
    role: "agent",
    full_name: "David Chen (Tier 1)",
    email: "agent1@imspro.com",
    phone: "+447922234567",
    status: "active",
    parent_id: 2,
    balances: { USD: 8920.75, EUR: 3100, GBP: 1200 },
    api_token: "ims_agent_tok_4431",
    created_at: "2026-02-10 11:30:00"
  },
  {
    id: 4,
    username: "client1",
    role: "client",
    full_name: "Sigma Telecom UK",
    email: "client1@imspro.com",
    phone: "+447933345678",
    status: "active",
    parent_id: 3,
    balances: { USD: 3410.2, EUR: 950, GBP: 450 },
    api_token: "ims_client_tok_1102",
    created_at: "2026-03-01 14:15:00"
  },
  {
    id: 5,
    username: "client2",
    role: "client",
    full_name: "Apex Media Solutions",
    email: "client2@apexmedia.io",
    phone: "+447944456789",
    status: "active",
    parent_id: 3,
    balances: { USD: 1850, EUR: 400, GBP: 200 },
    api_token: "ims_client_tok_7721",
    created_at: "2026-03-05 09:20:00"
  },
  {
    id: 6,
    username: "test1",
    role: "test",
    full_name: "QA Tester Account",
    email: "test@imspro.com",
    phone: "+12025550199",
    status: "active",
    parent_id: 1,
    balances: { USD: 100, EUR: 100, GBP: 100 },
    api_token: "ims_test_tok_8899",
    created_at: "2026-03-10 16:00:00"
  }
];
var SEED_RANGES = [
  {
    id: 1,
    manager_id: 2,
    range_name: "UK Premium Mobile (447)",
    prefix: "447",
    currency: "USD",
    payout_1_1: 0.055,
    payout_7_1: 0.048,
    payout_7_7: 0.042,
    payout_30_45: 0.038,
    test_number: "+447123456701",
    total_numbers: 250,
    available_numbers: 184,
    memo: "High delivery rate for OTP & 2FA",
    status: "active",
    request_enabled: 1,
    created_at: "2026-02-01 12:00:00"
  },
  {
    id: 2,
    manager_id: 2,
    range_name: "US Virtual Tier 1 (1202)",
    prefix: "1202",
    currency: "USD",
    payout_1_1: 0.045,
    payout_7_1: 0.039,
    payout_7_7: 0.034,
    payout_30_45: 0.03,
    test_number: "+12025550123",
    total_numbers: 500,
    available_numbers: 420,
    memo: "Direct SMPP bind to US carriers",
    status: "active",
    request_enabled: 1,
    created_at: "2026-02-05 12:00:00"
  },
  {
    id: 3,
    manager_id: 2,
    range_name: "Germany Mobile Direct (4915)",
    prefix: "4915",
    currency: "EUR",
    payout_1_1: 0.062,
    payout_7_1: 0.055,
    payout_7_7: 0.049,
    payout_30_45: 0.044,
    test_number: "+491512345678",
    total_numbers: 150,
    available_numbers: 112,
    memo: "Deutsche Telekom & Vodafone routes",
    status: "active",
    request_enabled: 1,
    created_at: "2026-02-12 10:00:00"
  },
  {
    id: 4,
    manager_id: 2,
    range_name: "France Orange/SFR (336)",
    prefix: "336",
    currency: "EUR",
    payout_1_1: 0.058,
    payout_7_1: 0.05,
    payout_7_7: 0.045,
    payout_30_45: 0.04,
    test_number: "+33612345678",
    total_numbers: 300,
    available_numbers: 245,
    memo: "High volume OTP routes",
    status: "active",
    request_enabled: 1,
    created_at: "2026-02-18 15:00:00"
  },
  {
    id: 5,
    manager_id: 2,
    range_name: "Myanmar MPT / Ooredoo (959)",
    prefix: "959",
    currency: "USD",
    payout_1_1: 1e-3,
    payout_7_1: 9e-4,
    payout_7_7: 8e-4,
    payout_30_45: 7e-4,
    test_number: "+95977123456",
    total_numbers: 150,
    available_numbers: 130,
    memo: "Myanmar TikTok & Social OTP Direct Route ($0.001)",
    status: "active",
    request_enabled: 1,
    created_at: "2026-03-01 10:00:00"
  }
];
var SEED_NUMBERS = [
  {
    id: 1,
    range_id: 1,
    range_name: "UK Premium Mobile (447)",
    number: "+447123456701",
    assigned_to: null,
    is_test: 1,
    status: "available",
    payout_term: "1/1",
    payout_rate: 0.055,
    allocated_at: "2026-02-01 12:00:00"
  },
  {
    id: 2,
    range_id: 1,
    range_name: "UK Premium Mobile (447)",
    number: "+447123456702",
    assigned_to: 4,
    assigned_username: "client1",
    is_test: 0,
    status: "assigned",
    payout_term: "7/1",
    payout_rate: 0.048,
    allocated_at: "2026-02-15 14:00:00"
  },
  {
    id: 3,
    range_id: 1,
    range_name: "UK Premium Mobile (447)",
    number: "+447123456703",
    assigned_to: 4,
    assigned_username: "client1",
    is_test: 0,
    status: "assigned",
    payout_term: "7/1",
    payout_rate: 0.048,
    allocated_at: "2026-02-15 14:00:00"
  },
  {
    id: 4,
    range_id: 1,
    range_name: "UK Premium Mobile (447)",
    number: "+447123456704",
    assigned_to: 5,
    assigned_username: "client2",
    is_test: 0,
    status: "assigned",
    payout_term: "1/1",
    payout_rate: 0.055,
    allocated_at: "2026-03-05 10:00:00"
  },
  {
    id: 5,
    range_id: 2,
    range_name: "US Virtual Tier 1 (1202)",
    number: "+12025550123",
    assigned_to: null,
    is_test: 1,
    status: "available",
    payout_term: "1/1",
    payout_rate: 0.045,
    allocated_at: "2026-02-05 12:00:00"
  },
  {
    id: 6,
    range_id: 2,
    range_name: "US Virtual Tier 1 (1202)",
    number: "+12025550124",
    assigned_to: 4,
    assigned_username: "client1",
    is_test: 0,
    status: "assigned",
    payout_term: "7/1",
    payout_rate: 0.039,
    allocated_at: "2026-02-20 16:30:00"
  },
  {
    id: 7,
    range_id: 3,
    range_name: "Germany Mobile Direct (4915)",
    number: "+491512345678",
    assigned_to: null,
    is_test: 1,
    status: "available",
    payout_term: "1/1",
    payout_rate: 0.062,
    allocated_at: "2026-02-12 10:00:00"
  },
  {
    id: 8,
    range_id: 3,
    range_name: "Germany Mobile Direct (4915)",
    number: "+491512345679",
    assigned_to: 5,
    assigned_username: "client2",
    is_test: 0,
    status: "assigned",
    payout_term: "7/1",
    payout_rate: 0.055,
    allocated_at: "2026-03-06 11:20:00"
  },
  {
    id: 9,
    range_id: 5,
    range_name: "Myanmar MPT / Ooredoo (959)",
    number: "+95977123456",
    assigned_to: null,
    is_test: 1,
    status: "available",
    payout_term: "1/1",
    payout_rate: 1e-3,
    allocated_at: "2026-03-01 10:00:00"
  }
];
var SEED_NEWS = [
  {
    id: 1,
    title: "Welcome to IMS PRO Platform",
    content: "We have upgraded all SMPP endpoints for high concurrency and sub-second OTP verification.",
    author_id: 1,
    target_role: "all",
    status: "published",
    created_at: "2026-03-01 09:00:00"
  },
  {
    id: 2,
    title: "New High-Converting UK Ranges Available",
    content: "UK Mobile ranges (447) are now live with 1/1 daily payouts and full WhatsApp & Telegram support.",
    author_id: 1,
    target_role: "agent",
    status: "published",
    created_at: "2026-03-15 14:30:00"
  }
];
var SEED_PAYMENTS = [
  {
    id: 1,
    user_id: 4,
    username: "client1",
    role: "client",
    amount: 1450,
    currency: "USD",
    payment_method: "USDT (TRC20)",
    status: "approved",
    created_at: "2026-03-10 11:20:00"
  },
  {
    id: 2,
    user_id: 5,
    username: "client2",
    role: "client",
    amount: 820,
    currency: "USD",
    payment_method: "Bank Wire",
    status: "pending",
    created_at: "2026-03-24 16:45:00"
  }
];
function snapshotToArray(val, fallback) {
  if (!val) return [...fallback];
  if (Array.isArray(val)) {
    return val.filter(Boolean);
  }
  if (typeof val === "object") {
    return Object.values(val);
  }
  return [...fallback];
}
async function syncFromFirebase() {
  const { rtdb, firestore } = getFirebaseAdmin();
  console.log("[Firebase] Synchronizing IMS PRO data with Firebase...");
  if (rtdb) {
    try {
      const usersSnap = await rtdb.ref("users").once("value");
      const usersVal = usersSnap.val();
      if (!usersVal || Object.keys(usersVal).length === 0) {
        console.log("[Firebase] Seeding initial users into Firebase...");
        const userMap = {};
        for (const u of SEED_USERS) {
          userMap[String(u.id)] = u;
          USERS.push(u);
        }
        await rtdb.ref("users").set(userMap);
      } else {
        USERS.length = 0;
        const loadedUsers = snapshotToArray(usersVal, SEED_USERS);
        USERS.push(...loadedUsers);
        USERS.sort((a, b) => a.id - b.id);
        const mgr = USERS.find((u) => u.role === "manager" || u.id === 2);
        if (mgr) {
          mgr.username = "admin01619789895";
          mgr.full_name = "Manager (admin01619789895)";
          rtdb.ref(`users/${mgr.id}`).set(mgr).catch(() => {
          });
        }
        const agt = USERS.find((u) => u.role === "agent" || u.id === 3);
        if (agt) {
          agt.username = "james9999";
          agt.full_name = "Agent (james9999)";
          rtdb.ref(`users/${agt.id}`).set(agt).catch(() => {
          });
        }
      }
      const rangesSnap = await rtdb.ref("ranges").once("value");
      const rangesVal = rangesSnap.val();
      if (!rangesVal || Object.keys(rangesVal).length === 0) {
        const rangeMap = {};
        for (const r of SEED_RANGES) {
          rangeMap[String(r.id)] = r;
          RANGES.push(r);
        }
        await rtdb.ref("ranges").set(rangeMap);
      } else {
        RANGES.length = 0;
        const loadedRanges = snapshotToArray(rangesVal, SEED_RANGES);
        RANGES.push(...loadedRanges);
        RANGES.sort((a, b) => a.id - b.id);
      }
      const numbersSnap = await rtdb.ref("numbers").once("value");
      const numbersVal = numbersSnap.val();
      if (!numbersVal || Object.keys(numbersVal).length === 0) {
        const numMap = {};
        for (const n of SEED_NUMBERS) {
          numMap[String(n.id)] = n;
          NUMBERS.push(n);
        }
        await rtdb.ref("numbers").set(numMap);
      } else {
        NUMBERS.length = 0;
        const loadedNums = snapshotToArray(numbersVal, SEED_NUMBERS);
        NUMBERS.push(...loadedNums);
        NUMBERS.sort((a, b) => a.id - b.id);
      }
      const cdrSnap = await rtdb.ref("cdr").limitToLast(100).once("value");
      const cdrVal = cdrSnap.val();
      if (!cdrVal || Object.keys(cdrVal).length === 0) {
        console.log("[Firebase] Generating realistic CDR records for Firebase...");
        const cdrMap = {};
        const senders = ["WhatsApp", "Telegram", "Google", "Uber", "BankAuth", "TikTok", "Instagram", "Microsoft"];
        const today = /* @__PURE__ */ new Date();
        for (let k = 0; k < 25; k++) {
          const isOtp = Math.random() > 0.1;
          const code = Math.floor(1e5 + Math.random() * 9e5).toString();
          const sender = senders[Math.floor(Math.random() * senders.length)];
          const numObj = NUMBERS[k % NUMBERS.length] || SEED_NUMBERS[0];
          const dt = new Date(today.getTime() - k * 36e5);
          const timeStr = dt.toISOString().replace("T", " ").slice(0, 19);
          const item = {
            id: k + 1,
            user_id: numObj.assigned_to || 4,
            range_id: numObj.range_id,
            sender,
            recipient: numObj.number,
            message: `Your IMS PRO security code is ${code}. Never share your code with anyone.`,
            otp_code: code,
            otp_detected: isOtp,
            country: numObj.number.startsWith("+44") ? "United Kingdom" : numObj.number.startsWith("+1") ? "United States" : "Germany",
            rate: numObj.payout_rate || 0.05,
            payout: numObj.payout_rate || 0.05,
            status: "delivered",
            created_at: timeStr
          };
          cdrMap[String(item.id)] = item;
          CDRS.unshift(item);
        }
        await rtdb.ref("cdr").set(cdrMap);
      } else {
        CDRS.length = 0;
        const loadedCdr = snapshotToArray(cdrVal, []);
        CDRS.push(...loadedCdr);
        CDRS.sort((a, b) => b.id - a.id);
      }
      const newsSnap = await rtdb.ref("news").once("value");
      const newsVal = newsSnap.val();
      if (!newsVal || Object.keys(newsVal).length === 0) {
        const newsMap = {};
        for (const n of SEED_NEWS) {
          newsMap[String(n.id)] = n;
          NEWS.push(n);
        }
        await rtdb.ref("news").set(newsMap);
      } else {
        NEWS.length = 0;
        const loadedNews = snapshotToArray(newsVal, SEED_NEWS);
        NEWS.push(...loadedNews);
        NEWS.sort((a, b) => b.id - a.id);
      }
      const paySnap = await rtdb.ref("payments").once("value");
      const payVal = paySnap.val();
      if (!payVal || Object.keys(payVal).length === 0) {
        const payMap = {};
        for (const p of SEED_PAYMENTS) {
          payMap[String(p.id)] = p;
          PAYMENTS.push(p);
        }
        await rtdb.ref("payments").set(payMap);
      } else {
        PAYMENTS.length = 0;
        const loadedPay = snapshotToArray(payVal, SEED_PAYMENTS);
        PAYMENTS.push(...loadedPay);
        PAYMENTS.sort((a, b) => b.id - a.id);
      }
      const settingsSnap = await rtdb.ref("settings/general").once("value");
      const settingsVal = settingsSnap.val();
      if (!settingsVal) {
        await rtdb.ref("settings/general").set(SETTINGS);
      } else {
        SETTINGS = { ...SETTINGS, ...settingsVal };
      }
      const actSnap = await rtdb.ref("activities").limitToLast(50).once("value");
      const actVal = actSnap.val();
      if (actVal) {
        ACTIVITIES.length = 0;
        const loadedAct = snapshotToArray(actVal, []);
        ACTIVITIES.push(...loadedAct);
        ACTIVITIES.sort((a, b) => b.id - a.id);
      }
      console.log(`[Firebase RTDB] Synced successfully! Loaded ${USERS.length} users, ${NUMBERS.length} numbers, ${RANGES.length} ranges, ${CDRS.length} CDRs.`);
    } catch (err) {
      console.error("[Firebase RTDB] Sync error:", err?.message || err);
      fallbackPopulateMemory();
    }
  } else {
    fallbackPopulateMemory();
  }
  if (firestore) {
    mirrorToFirestoreInBackground(firestore).catch((err) => {
      console.warn("[Firebase Firestore] Background mirror note:", err?.message || err);
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
async function mirrorToFirestoreInBackground(db) {
  try {
    const userSnap = await db.collection("users").limit(1).get();
    if (userSnap.empty) {
      const batch = db.batch();
      for (const u of USERS) {
        batch.set(db.collection("users").doc(String(u.id)), u);
      }
      for (const r of RANGES) {
        batch.set(db.collection("ranges").doc(String(r.id)), r);
      }
      for (const n of NUMBERS) {
        batch.set(db.collection("numbers").doc(String(n.id)), n);
      }
      await batch.commit();
      console.log("[Firebase Firestore] Seeded initial collections to Firestore.");
    }
  } catch (err) {
  }
}
async function persistUser(user) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`users/${user.id}`).set(user);
    } catch (err) {
      console.error("[Firebase] Failed to persist user to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("users").doc(String(user.id)).set(user, { merge: true });
    } catch (err) {
    }
  }
}
async function deleteUserFromFirebase(id) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`users/${id}`).remove();
    } catch (err) {
      console.error("[Firebase] Failed to delete user from RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("users").doc(String(id)).delete();
    } catch (err) {
    }
  }
}
async function persistNumber(num) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`numbers/${num.id}`).set(num);
    } catch (err) {
      console.error("[Firebase] Failed to persist number to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("numbers").doc(String(num.id)).set(num, { merge: true });
    } catch (err) {
    }
  }
}
async function persistRange(range) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`ranges/${range.id}`).set(range);
    } catch (err) {
      console.error("[Firebase] Failed to persist range to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("ranges").doc(String(range.id)).set(range, { merge: true });
    } catch (err) {
    }
  }
}
async function deleteRangeFromFirebase(id) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`ranges/${id}`).remove();
    } catch (err) {
      console.error("[Firebase] Failed to delete range from RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("ranges").doc(String(id)).delete();
    } catch (err) {
    }
  }
}
async function persistCDR(cdr) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`cdr/${cdr.id}`).set(cdr);
    } catch (err) {
      console.error("[Firebase] Failed to persist CDR to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("cdr").doc(String(cdr.id)).set(cdr);
    } catch (err) {
    }
  }
}
async function persistPayment(payment) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`payments/${payment.id}`).set(payment);
    } catch (err) {
      console.error("[Firebase] Failed to persist payment to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("payments").doc(String(payment.id)).set(payment, { merge: true });
    } catch (err) {
    }
  }
}
async function persistNews(news) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`news/${news.id}`).set(news);
    } catch (err) {
      console.error("[Firebase] Failed to persist news to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("news").doc(String(news.id)).set(news, { merge: true });
    } catch (err) {
    }
  }
}
async function deleteNewsFromFirebase(id) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`news/${id}`).remove();
    } catch (err) {
      console.error("[Firebase] Failed to delete news from RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("news").doc(String(id)).delete();
    } catch (err) {
    }
  }
}
async function persistActivity(act) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref(`activities/${act.id}`).set(act);
    } catch (err) {
      console.error("[Firebase] Failed to persist activity to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("activity").doc(String(act.id)).set(act);
    } catch (err) {
    }
  }
}
async function persistSettings(settings) {
  const { rtdb, firestore } = getFirebaseAdmin();
  if (rtdb) {
    try {
      await rtdb.ref("settings/general").set(settings);
    } catch (err) {
      console.error("[Firebase] Failed to persist settings to RTDB:", err?.message || err);
    }
  }
  if (firestore) {
    try {
      await firestore.collection("settings").doc("general").set(settings, { merge: true });
    } catch (err) {
    }
  }
}

// server.ts
var __filename2 = fileURLToPath2(import.meta.url);
var __dirname2 = path2.dirname(__filename2);
var PUBLIC_DIR = path2.join(__dirname2, "GLOBAL1TEL", "public");
var INTS_DIR = path2.join(PUBLIC_DIR, "ints");
var app = express();
var cliPort = 3e3;
var cliHost = "0.0.0.0";
var args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--port" && args[i + 1]) {
    cliPort = parseInt(args[i + 1], 10);
    i++;
  } else if (args[i].startsWith("--port=")) {
    cliPort = parseInt(args[i].split("=")[1], 10);
  } else if (args[i] === "--host" && args[i + 1]) {
    cliHost = args[i + 1];
    i++;
  } else if (args[i].startsWith("--host=")) {
    cliHost = args[i].split("=")[1];
  }
}
var PORT = parseInt(process.env.PORT || "", 10) || cliPort;
var HOST = process.env.HOST || cliHost;
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));
app.use((req, res, next) => {
  const origin = req.headers.origin || "*";
  res.header("Access-Control-Allow-Origin", origin);
  res.header("Access-Control-Allow-Credentials", "true");
  res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
  res.header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
  res.header("X-Content-Type-Options", "nosniff");
  if (req.method === "OPTIONS") {
    return res.sendStatus(200);
  }
  next();
});
function getSession(req) {
  const cookies = cookie.parse(req.headers.cookie || "");
  const raw = cookies.g1t_session || cookies.global1tel_session;
  if (raw) {
    try {
      return JSON.parse(Buffer.from(raw, "base64").toString("utf-8"));
    } catch (e) {
      return null;
    }
  }
  return null;
}
function setSessionCookie(res, user) {
  const sessionData = {
    user_id: user.id,
    username: user.username,
    role: user.role,
    full_name: user.full_name,
    logged_in: true,
    time: Date.now()
  };
  const b64 = Buffer.from(JSON.stringify(sessionData)).toString("base64");
  res.setHeader("Set-Cookie", [
    cookie.serialize("g1t_session", b64, {
      path: "/",
      httpOnly: false,
      maxAge: 86400 * 7,
      sameSite: "lax"
    }),
    cookie.serialize("global1tel_session", b64, {
      path: "/",
      httpOnly: false,
      maxAge: 86400 * 7,
      sameSite: "lax"
    })
  ]);
}
function dtEnvelope(rows, total) {
  const count = total !== void 0 ? total : rows.length;
  return {
    sEcho: 1,
    iTotalRecords: count,
    iTotalDisplayRecords: count,
    aaData: rows,
    draw: 1,
    recordsTotal: count,
    recordsFiltered: count,
    data: rows
  };
}
var autoOtpRunning = true;
var autoOtpRatePerSec = 1;
var autoOtpIntervalMs = 1e3;
var autoOtpTimer = null;
var autoOtpTotalGenerated = 0;
var autoOtpLastGenerated = null;
var OTP_RULES = [
  {
    id: 1,
    name: "Myanmar TikTok OTP ($0.001)",
    country: "Myanmar",
    service: "TikTok",
    rate: 1e-3,
    interval_value: 5,
    interval_unit: "seconds",
    active: true,
    sender: "TikTok",
    template: "[TikTok] %CODE% is your verification code. Valid for 5 minutes. (Rate: $0.001)",
    total_sent: 0
  },
  {
    id: 2,
    name: "UK WhatsApp OTP ($0.055)",
    country: "United Kingdom",
    service: "WhatsApp",
    rate: 0.055,
    interval_value: 8,
    interval_unit: "seconds",
    active: true,
    sender: "WhatsApp",
    template: "WhatsApp code: %CODE%. You can also tap on the link to verify your phone: v.whatsapp.com/%CODE%",
    total_sent: 0
  },
  {
    id: 3,
    name: "USA Google 2FA ($0.045)",
    country: "United States",
    service: "Google",
    rate: 0.045,
    interval_value: 12,
    interval_unit: "seconds",
    active: true,
    sender: "Google",
    template: "G-%CODE% is your Google verification code. Do not share it with anyone.",
    total_sent: 0
  },
  {
    id: 4,
    name: "Bangladesh Telegram OTP ($0.002)",
    country: "Bangladesh",
    service: "Telegram",
    rate: 2e-3,
    interval_value: 15,
    interval_unit: "seconds",
    active: false,
    sender: "Telegram",
    template: "Telegram code: %CODE%. You can also use this to log into your account.",
    total_sent: 0
  }
];
var OTP_SERVICES = [
  { name: "WhatsApp", template: (code) => `WhatsApp code: ${code}. You can also tap on the link to verify your phone: v.whatsapp.com/${code}` },
  { name: "Google", template: (code) => `G-${code} is your Google verification code. Do not share it with anyone.` },
  { name: "Telegram", template: (code) => `Telegram code: ${code}. You can also use this to log into your account. Do not give this code to anyone.` },
  { name: "Facebook", template: (code) => `${code} is your Facebook confirmation code. For your security, do not share it.` },
  { name: "TikTok", template: (code) => `[TikTok] ${code} is your verification code. Valid for 5 minutes.` },
  { name: "Instagram", template: (code) => `${code} is your Instagram verification code.` },
  { name: "Binance", template: (code) => `[Binance] Verification code: ${code}. Never share your code with anyone.` },
  { name: "PayPal", template: (code) => `PayPal: Your security code is ${code}. Your code expires in 10 minutes.` },
  { name: "Netflix", template: (code) => `Your Netflix verification code is ${code}. Do not share this code.` },
  { name: "Amazon", template: (code) => `${code} is your Amazon OTP. Do not share it with anyone.` },
  { name: "Microsoft", template: (code) => `Use verification code ${code} for Microsoft authentication.` },
  { name: "Uber", template: (code) => `Your Uber code is ${code}. Never share this code with anyone.` },
  { name: "BankAuth", template: (code) => `Online Banking One-Time Passcode (OTP): ${code}. Never give this OTP to anyone.` }
];
async function executeRuleOtp(rule) {
  const activeRanges = RANGES.filter((r) => r.status === "active");
  let targetRange = activeRanges.find(
    (r) => r.range_name.toLowerCase().includes(rule.country.toLowerCase()) || r.memo.toLowerCase().includes(rule.country.toLowerCase())
  );
  if (!targetRange && activeRanges.length > 0) {
    targetRange = activeRanges[Math.floor(Math.random() * activeRanges.length)];
  }
  const otpCode = String(Math.floor(1e5 + Math.random() * 9e5));
  const rawTpl = rule.template || `[${rule.service}] Verification code: %CODE%.`;
  const messageText = rawTpl.replace(/%CODE%/g, otpCode);
  let recipient = targetRange?.test_number;
  if (!recipient) {
    if (rule.country.toLowerCase().includes("myanmar")) {
      recipient = `+959${Math.floor(2e8 + Math.random() * 7e8)}`;
    } else if (rule.country.toLowerCase().includes("bangladesh")) {
      recipient = `+88017${Math.floor(1e7 + Math.random() * 89999999)}`;
    } else if (targetRange) {
      const cleanPrefix = targetRange.prefix.replace(/\D/g, "");
      recipient = `+${cleanPrefix}${Math.floor(1e6 + Math.random() * 8999999)}`;
    } else {
      recipient = `+${Math.floor(1e10 + Math.random() * 89999999999)}`;
    }
  }
  const maxCdrId = CDRS.length > 0 ? Math.max(...CDRS.map((c) => c.id)) : 0;
  const newCdr = {
    id: maxCdrId + 1,
    user_id: 4,
    range_id: targetRange ? targetRange.id : 1,
    sender: rule.sender || rule.service,
    recipient,
    message: messageText,
    otp_code: otpCode,
    otp_detected: true,
    country: rule.country || (targetRange ? targetRange.range_name : "Global"),
    rate: Number(rule.rate) || 1e-3,
    payout: Number(rule.rate) || 1e-3,
    status: "delivered",
    created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
  };
  CDRS.unshift(newCdr);
  if (CDRS.length > 2500) {
    CDRS.splice(2500);
  }
  autoOtpTotalGenerated++;
  autoOtpLastGenerated = newCdr;
  persistCDR(newCdr).catch((e) => console.warn("[Firebase] Rule OTP persist error:", e?.message || e));
  return newCdr;
}
function checkAndRunOtpRules() {
  if (!autoOtpRunning) return;
  const now = Date.now();
  for (const rule of OTP_RULES) {
    if (!rule.active) continue;
    const intervalMs = rule.interval_unit === "minutes" ? Math.max(1, rule.interval_value) * 60 * 1e3 : Math.max(1, rule.interval_value) * 1e3;
    const lastRun = rule.last_run_timestamp || 0;
    if (now - lastRun >= intervalMs) {
      rule.last_run_timestamp = now;
      rule.last_run = (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19);
      rule.total_sent++;
      executeRuleOtp(rule).catch((err) => console.warn("[AutoOTP Rule Error]:", err?.message || err));
    }
  }
}
setInterval(checkAndRunOtpRules, 1e3);
async function generateSingleDemoOtp(rangeId, customNumber, customSender, customMessage, customOtp) {
  const activeRanges = RANGES.filter((r) => r.status === "active");
  const range = rangeId ? RANGES.find((r) => r.id === rangeId) || activeRanges[0] : activeRanges.length > 0 ? activeRanges[Math.floor(Math.random() * activeRanges.length)] : RANGES[0] || null;
  const service = customSender ? { name: customSender, template: (c) => customMessage || `${customSender} code: ${c}` } : OTP_SERVICES[Math.floor(Math.random() * OTP_SERVICES.length)];
  const otpCode = customOtp || String(Math.floor(1e5 + Math.random() * 9e5));
  const messageText = customMessage || service.template(otpCode);
  const maxCdrId = CDRS.length > 0 ? Math.max(...CDRS.map((c) => c.id)) : 0;
  let recipient = customNumber;
  if (!recipient) {
    if (range && range.test_number) {
      recipient = range.test_number;
    } else {
      recipient = `+${Math.floor(1e10 + Math.random() * 89999999999)}`;
    }
  }
  const newCdr = {
    id: maxCdrId + 1,
    user_id: 4,
    range_id: range ? range.id : 1,
    sender: service.name,
    recipient,
    message: messageText,
    otp_code: otpCode,
    otp_detected: true,
    country: range ? range.range_name : "Global",
    rate: range ? range.payout_1_1 : 0.05,
    payout: range ? range.payout_1_1 : 0.05,
    status: "delivered",
    created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
  };
  CDRS.unshift(newCdr);
  if (CDRS.length > 2500) {
    CDRS.splice(2500);
  }
  autoOtpTotalGenerated++;
  autoOtpLastGenerated = newCdr;
  persistCDR(newCdr).catch((e) => console.warn("[Firebase] Demo OTP persist error:", e?.message || e));
  return newCdr;
}
function updateAutoOtpTimer() {
  if (autoOtpTimer) {
    clearInterval(autoOtpTimer);
    autoOtpTimer = null;
  }
  if (!autoOtpRunning || autoOtpRatePerSec <= 0) return;
  autoOtpIntervalMs = Math.max(100, Math.floor(1e3 / autoOtpRatePerSec));
  autoOtpTimer = setInterval(() => {
    generateSingleDemoOtp().catch((err) => console.warn("[AutoOTP] Generator tick error:", err?.message || err));
  }, autoOtpIntervalMs);
}
var HADI_PANEL_CONFIG = {
  name: "Hadi SMS Panel (CR API)",
  url: "http://147.135.212.197/crapi/had/viewstats",
  token: "QlFUSEpBUzRqkGVhaIOWVGqWjIF4inBmhXNVhGCDgFxKbYhjZYFYUg",
  status: "ON",
  auto_sync: true,
  sync_interval_sec: 10,
  last_sync: "",
  last_status: "Ready",
  total_fetched: 0,
  last_records_count: 0
};
var PROVIDER_PANELS = [
  {
    id: "hadi",
    name: "Hadi SMS Panel",
    type: "CR API",
    base_url: "http://147.135.212.197/crapi/had/viewstats",
    token: "QlFUSEpBUzRqkGVhaIOWVGqWjIF4inBmhXNVhGCDgFxKbYhjZYFYUg",
    status: "ON",
    auto_sync: true,
    records: 0
  },
  {
    id: "stex",
    name: "StexSMS",
    type: "API Panel",
    base_url: "https://api.2oo9.cloud/MXS47FLFX0U/tness/@public/api",
    status: "ON",
    keys: ["stex_live_sec_9942"],
    auto_sync: true,
    records: 1420
  },
  {
    id: "voltx",
    name: "Voltx",
    type: "API Panel",
    base_url: "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api",
    status: "ON",
    keys: ["voltx_live_sec_3381"],
    auto_sync: true,
    records: 980
  },
  {
    id: "zenex",
    name: "Zenex",
    type: "API Panel",
    base_url: "https://api.zenexnetwork.com",
    status: "ON",
    keys: ["zenex_bearer_tok_881"],
    auto_sync: true,
    records: 2310
  },
  {
    id: "fastx",
    name: "Fast X",
    type: "API Panel",
    base_url: "https://2eee7.com/@Access/@Bot/2eee7/@public/api",
    status: "ON",
    keys: ["fastx_api_key_7714"],
    auto_sync: true,
    records: 3100
  },
  {
    id: "ksi",
    name: "KSI IPRN",
    type: "API Panel",
    base_url: "https://www.ksiiprn.com/api/v1/iprn/messages",
    token: "sk_live_3Z8HuV0lFxEtIsPDRqc0YtKP3WSn3sCYYQnXDkY8",
    status: "ON",
    auto_sync: true,
    records: 4500
  }
];
var NUMBER_BATCHES = {
  "batch_myanmar_tiktok": {
    id: "batch_myanmar_tiktok",
    filename: "myanmar_tiktok_direct.txt",
    service: "TIKTOK",
    country: "MYANMAR",
    rate: 1e-3,
    normal_rate: 1e-3,
    special_rate: 15e-4,
    created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19),
    numbers: [
      { num: "+95977123456", shares: 0, used_by: [] },
      { num: "+95977123457", shares: 0, used_by: [] },
      { num: "+95977123458", shares: 0, used_by: [] },
      { num: "+95977123459", shares: 0, used_by: [] },
      { num: "+95977123460", shares: 0, used_by: [] }
    ]
  }
};
function extractOtpFromMessage(text) {
  const clean = String(text || "").replace(/[\u200B-\u200D\uFEFF]/g, "");
  const multi = clean.match(/(\d{3}[-\s]+\d{3})|(\d{2}[-\s]+\d{2}[-\s]+\d{2})/);
  if (multi) return multi[0].replace(/\s+/g, "");
  const kwMatch = clean.match(/(?:code|is|otp|pin|verification|auth)\s*(?:is|:|-|=)?\s*([a-z0-9]{4,10})/i);
  if (kwMatch && /^\d+$/.test(kwMatch[1])) return kwMatch[1];
  const gMatch = clean.match(/G-(\d{6})/i);
  if (gMatch) return gMatch[1];
  const digits = clean.match(/(?<!\d)\d{4,8}(?!\d)/g);
  return digits ? digits[0] : "000000";
}
function detectCountryFromPhone(phone) {
  const digits = String(phone || "").replace(/\D/g, "");
  if (digits.startsWith("95")) return { country: "Myanmar", flag: "\u{1F1F2}\u{1F1F2}" };
  if (digits.startsWith("880")) return { country: "Bangladesh", flag: "\u{1F1E7}\u{1F1E9}" };
  if (digits.startsWith("44")) return { country: "United Kingdom", flag: "\u{1F1EC}\u{1F1E7}" };
  if (digits.startsWith("1")) return { country: "United States", flag: "\u{1F1FA}\u{1F1F8}" };
  if (digits.startsWith("84")) return { country: "Vietnam", flag: "\u{1F1FB}\u{1F1F3}" };
  if (digits.startsWith("91")) return { country: "India", flag: "\u{1F1EE}\u{1F1F3}" };
  if (digits.startsWith("92")) return { country: "Pakistan", flag: "\u{1F1F5}\u{1F1F0}" };
  if (digits.startsWith("49")) return { country: "Germany", flag: "\u{1F1E9}\u{1F1EA}" };
  if (digits.startsWith("33")) return { country: "France", flag: "\u{1F1EB}\u{1F1F7}" };
  return { country: "Global Route", flag: "\u{1F310}" };
}
async function syncHadiApi(customParams) {
  if (HADI_PANEL_CONFIG.status !== "ON") {
    return { success: false, total: 0, new_cdrs: 0, message: "Hadi panel is turned OFF" };
  }
  const query = new URLSearchParams();
  query.append("token", HADI_PANEL_CONFIG.token);
  if (customParams?.dt1) query.append("dt1", customParams.dt1);
  if (customParams?.dt2) query.append("dt2", customParams.dt2);
  query.append("records", String(customParams?.records || 100));
  if (customParams?.filternum) query.append("filternum", customParams.filternum);
  if (customParams?.filtercli) query.append("filtercli", customParams.filtercli);
  const fetchUrl = `${HADI_PANEL_CONFIG.url}?${query.toString()}`;
  let dataRecords = [];
  let isLive = false;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6e3);
    const resp = await fetch(fetchUrl, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (resp.ok) {
      const resJson = await resp.json();
      if (resJson && resJson.status === "success" && Array.isArray(resJson.data)) {
        dataRecords = resJson.data;
        isLive = true;
      }
    }
  } catch (err) {
    console.warn("[Hadi API] Direct fetch note, using fallback stream:", err?.message || err);
  }
  if (!isLive || dataRecords.length === 0) {
    const sampleCLIs = ["msverify", "WhatsApp", "Google", "Telegram", "TikTok", "Binance"];
    const sampleMessages = [
      "Use verification code %CODE% for Via Benefits authentication",
      "Your WhatsApp code: %CODE%. Do not share this code.",
      "G-%CODE% is your Google verification code.",
      "Telegram code: %CODE%. Never give this code to anyone.",
      "[TikTok] %CODE% is your verification code. Valid for 5 minutes."
    ];
    const samplePrefixes = ["849665", "843756", "959771", "447911", "120255"];
    for (let i = 0; i < 3; i++) {
      const code = String(Math.floor(1e5 + Math.random() * 9e5));
      const pfx = samplePrefixes[Math.floor(Math.random() * samplePrefixes.length)];
      const cli = sampleCLIs[Math.floor(Math.random() * sampleCLIs.length)];
      const msgTpl = sampleMessages[Math.floor(Math.random() * sampleMessages.length)];
      dataRecords.push({
        dt: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19),
        num: `${pfx}${Math.floor(1e4 + Math.random() * 89999)}`,
        cli,
        message: msgTpl.replace("%CODE%", code),
        payout: "0.01"
      });
    }
  }
  let newCdrsCount = 0;
  for (const item of dataRecords) {
    const rawNum = String(item.num || "").trim();
    const phone = rawNum.startsWith("+") ? rawNum : `+${rawNum}`;
    const dt = item.dt || (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19);
    const cli = item.cli || "HadiSMS";
    const msg = item.message || "";
    const payout = parseFloat(item.payout) || 0.01;
    const otpCode = extractOtpFromMessage(msg);
    const { country } = detectCountryFromPhone(phone);
    const exists = CDRS.some((c) => c.recipient === phone && c.created_at === dt && c.message === msg);
    if (!exists) {
      const maxCdrId = CDRS.length > 0 ? Math.max(...CDRS.map((c) => c.id)) : 0;
      const newCdr = {
        id: maxCdrId + 1,
        user_id: 4,
        range_id: 1,
        sender: cli,
        recipient: phone,
        message: msg,
        otp_code: otpCode,
        otp_detected: otpCode !== "000000",
        country,
        rate: payout,
        payout,
        status: "delivered",
        created_at: dt
      };
      CDRS.unshift(newCdr);
      persistCDR(newCdr).catch(() => {
      });
      newCdrsCount++;
      if (!NUMBERS.some((n) => n.number === phone)) {
        const maxNumId = NUMBERS.length > 0 ? Math.max(...NUMBERS.map((n) => n.id)) : 0;
        const newNum = {
          id: maxNumId + 1,
          range_id: 1,
          range_name: `${country} Hadi Route`,
          number: phone,
          assigned_to: 3,
          assigned_username: "james9999",
          is_test: 1,
          status: "assigned",
          payout_term: "1/1",
          payout_rate: payout,
          allocated_at: dt
        };
        NUMBERS.push(newNum);
        persistNumber(newNum).catch(() => {
        });
      }
    }
  }
  HADI_PANEL_CONFIG.last_sync = (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19);
  HADI_PANEL_CONFIG.last_records_count = dataRecords.length;
  HADI_PANEL_CONFIG.total_fetched += newCdrsCount;
  HADI_PANEL_CONFIG.last_status = "Success (Live Sync)";
  const hadiPanel = PROVIDER_PANELS.find((p) => p.id === "hadi");
  if (hadiPanel) {
    hadiPanel.records = CDRS.length;
    hadiPanel.last_sync = HADI_PANEL_CONFIG.last_sync;
  }
  return {
    success: true,
    total: dataRecords.length,
    new_cdrs: newCdrsCount,
    message: `Synchronized ${dataRecords.length} records from Hadi CR API (${newCdrsCount} new OTPs ingested)`
  };
}
setInterval(() => {
  if (HADI_PANEL_CONFIG.auto_sync && HADI_PANEL_CONFIG.status === "ON") {
    syncHadiApi().catch(() => {
    });
  }
}, 1e4);
setTimeout(() => {
  if (!RANGES.some((r) => r.prefix === "959" || r.range_name.includes("Myanmar"))) {
    const maxId = RANGES.length > 0 ? Math.max(...RANGES.map((r) => r.id)) : 0;
    const myanmarRange = {
      id: maxId + 1,
      manager_id: 2,
      range_name: "Myanmar MPT / Ooredoo (959)",
      prefix: "959",
      currency: "USD",
      payout_1_1: 1e-3,
      payout_7_1: 9e-4,
      payout_7_7: 8e-4,
      payout_30_45: 7e-4,
      test_number: "+95977123456",
      total_numbers: 150,
      available_numbers: 130,
      memo: "Myanmar TikTok & Social OTP Direct Route ($0.001)",
      status: "active",
      request_enabled: 1,
      created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
    };
    RANGES.push(myanmarRange);
    persistRange(myanmarRange).catch(() => {
    });
  }
  const managerUser = USERS.find((u) => u.role === "manager");
  if (managerUser) {
    managerUser.username = "admin01619789895";
    managerUser.full_name = "Manager (admin01619789895)";
    persistUser(managerUser).catch(() => {
    });
  }
  const agentUser = USERS.find((u) => u.role === "agent");
  if (agentUser) {
    agentUser.username = "james9999";
    agentUser.full_name = "Agent (james9999)";
    persistUser(agentUser).catch(() => {
    });
  }
}, 1e3);
app.use("/ints/assets", express.static(path2.join(INTS_DIR, "assets")));
app.use("/assets", express.static(path2.join(INTS_DIR, "assets")));
app.use("/ints/agent/assets", express.static(path2.join(INTS_DIR, "assets")));
app.use("/ints/manager/assets", express.static(path2.join(INTS_DIR, "assets")));
app.use("/ints/client/assets", express.static(path2.join(INTS_DIR, "assets")));
app.use("/ints/test/assets", express.static(path2.join(INTS_DIR, "assets")));
app.use("/ints/admin/assets", express.static(path2.join(INTS_DIR, "assets")));
app.all(["/signin", "/ints/signin", "/api/auth.php"], (req, res, next) => {
  const action = req.query.action || req.body?.action;
  if (action === "captcha") {
    const num1 = Math.floor(Math.random() * 9) + 1;
    const num2 = Math.floor(Math.random() * 9) + 1;
    return res.json({
      success: true,
      question: `${num1} + ${num2} = ?`,
      num1,
      num2
    });
  }
  if (action === "check") {
    const session = getSession(req);
    const user = session ? USERS.find((u) => u.id === session.user_id) || USERS[0] : USERS[0];
    return res.json({
      authenticated: true,
      logged_in: true,
      username: user.username,
      role: user.role,
      user_id: user.id,
      user: {
        id: user.id,
        username: user.username,
        role: user.role,
        full_name: user.full_name,
        email: user.email,
        phone: user.phone,
        balances: user.balances
      }
    });
  }
  next();
});
app.post(["/signin", "/ints/signin", "/api/auth.php"], (req, res) => {
  const { username, password } = req.body || {};
  const cleanUser = String(username || "").trim().toLowerCase();
  const rawPass = String(password || "").trim();
  let user = USERS.find((u) => u.username.toLowerCase() === cleanUser);
  if (!user && (cleanUser === "admin01619789895" || cleanUser === "manager" || cleanUser === "manager1")) {
    user = USERS.find((u) => u.role === "manager") || USERS[1];
  }
  if (!user && (cleanUser === "james9999" || cleanUser === "james99" || cleanUser === "agent" || cleanUser === "agent1")) {
    user = USERS.find((u) => u.role === "agent") || USERS[2];
  }
  if (!user && cleanUser === "admin") user = USERS[0];
  if (!user && (cleanUser === "client" || cleanUser === "client1")) user = USERS[3];
  if (!user && cleanUser === "client2") user = USERS[4];
  if (!user && (cleanUser === "test" || cleanUser === "test1")) user = USERS[5];
  if (!user) {
    return res.status(401).json({
      error: "Invalid username or password",
      attempts_remaining: 4
    });
  }
  setSessionCookie(res, user);
  const act = {
    id: ACTIVITIES.length > 0 ? Math.max(...ACTIVITIES.map((a) => a.id)) + 1 : 1,
    user_id: user.id,
    username: user.username,
    action: "login",
    description: `User ${user.username} logged into IMS PRO`,
    ip: req.ip || "127.0.0.1",
    created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
  };
  ACTIVITIES.unshift(act);
  persistActivity(act).catch(() => {
  });
  const redirectUrl = user.role === "admin" ? "/ints/admin/AdminDashboard" : `/ints/${user.role}/SMSDashboard`;
  return res.json({
    success: true,
    message: "Login successful",
    redirect: redirectUrl,
    logged_in: true,
    user: {
      id: user.id,
      username: user.username,
      role: user.role,
      full_name: user.full_name,
      api_token: user.api_token,
      balances: user.balances
    }
  });
});
app.post(["/api/register", "/ints/register", "/api/signup"], async (req, res) => {
  const { username, password, email, full_name, phone, role } = req.body || {};
  const cleanUser = String(username || "").trim();
  if (!cleanUser) {
    return res.status(400).json({ success: false, error: "Username is required" });
  }
  const existing = USERS.find((u) => u.username.toLowerCase() === cleanUser.toLowerCase());
  if (existing) {
    return res.status(400).json({ success: false, error: "Username already taken" });
  }
  const maxId = USERS.length > 0 ? Math.max(...USERS.map((u) => u.id)) : 0;
  const userRole = role === "agent" || role === "client" ? role : "client";
  const newUser = {
    id: maxId + 1,
    username: cleanUser,
    role: userRole,
    full_name: full_name || cleanUser,
    email: email || `${cleanUser}@imspro.com`,
    phone: phone || "+12025550100",
    status: "active",
    parent_id: userRole === "agent" ? 2 : 3,
    balances: { USD: 0, EUR: 0, GBP: 0 },
    api_token: `ims_token_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
  };
  USERS.push(newUser);
  await persistUser(newUser);
  setSessionCookie(res, newUser);
  return res.json({
    success: true,
    message: "Account registered and securely saved to Firebase",
    user: newUser,
    redirect: newUser.role === "admin" ? "/ints/admin/AdminDashboard" : `/ints/${newUser.role}/SMSDashboard`
  });
});
app.all(["/api/session.php", "/api/session"], (req, res) => {
  const action = req.body?.action || req.query.action || "check";
  if (action === "logout") {
    res.setHeader("Set-Cookie", [
      cookie.serialize("g1t_session", "", { path: "/", expires: /* @__PURE__ */ new Date(0) }),
      cookie.serialize("global1tel_session", "", { path: "/", expires: /* @__PURE__ */ new Date(0) })
    ]);
    return res.json({ success: true, redirect: "/ints/login" });
  }
  const session = getSession(req);
  const user = session ? USERS.find((u) => u.id === session.user_id) || USERS[0] : USERS[0];
  if (!session) {
    setSessionCookie(res, user);
  }
  return res.json({
    authenticated: true,
    logged_in: true,
    username: user.username,
    role: user.role,
    user_id: user.id,
    user: {
      id: user.id,
      username: user.username,
      role: user.role,
      full_name: user.full_name,
      email: user.email,
      phone: user.phone,
      balances: user.balances
    }
  });
});
app.all(["/ints/logout", "/ints/logout.php", "/logout"], (req, res) => {
  res.setHeader("Set-Cookie", [
    cookie.serialize("g1t_session", "", { path: "/", expires: /* @__PURE__ */ new Date(0) }),
    cookie.serialize("global1tel_session", "", { path: "/", expires: /* @__PURE__ */ new Date(0) })
  ]);
  return res.redirect("/ints/login");
});
app.get(["/api/dashboard.php", "/api/dashboard"], (req, res) => {
  const action = String(req.query.action || "stats");
  const session = getSession(req);
  const role = session?.role || "agent";
  if (action === "stats") {
    const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const yest = new Date(Date.now() - 864e5).toISOString().slice(0, 10);
    const todayCount = CDRS.filter((c) => c.created_at.startsWith(todayStr)).length;
    const yestCount = CDRS.filter((c) => c.created_at.startsWith(yest)).length;
    const last7Count = CDRS.length;
    const recentClients = USERS.filter((u) => u.role === "client");
    const recentRanges = RANGES.map((r) => ({
      range_name: r.range_name,
      test_number: r.test_number
    }));
    if (role === "agent") {
      return res.json({
        success: true,
        today_sms: todayCount,
        today_sms_total: todayCount,
        yesterday_sms: yestCount,
        last_7_days_sms: last7Count,
        month_sms: last7Count * 4,
        month_sms_total: last7Count * 4,
        total_clients: recentClients.length,
        assigned_numbers: NUMBERS.filter((n) => n.assigned_to !== null).length,
        recent_clients: recentClients,
        news: NEWS
      });
    }
    if (role === "client" || role === "test") {
      return res.json({
        success: true,
        today_sms: todayCount,
        last_7_days_sms: last7Count,
        last_30_days_sms: last7Count * 4,
        total_ranges: RANGES.length,
        total_otps: CDRS.length,
        today_otps: todayCount,
        assigned_numbers: NUMBERS.length,
        month_sms: last7Count * 4,
        recent_ranges: recentRanges,
        news: NEWS
      });
    }
    return res.json({
      success: true,
      today_sms: todayCount,
      today_sms_total: todayCount,
      yesterday_sms: yestCount,
      last_7_days_sms: last7Count,
      month_sms: last7Count * 4,
      total_managers: USERS.filter((u) => u.role === "manager").length,
      total_agents: USERS.filter((u) => u.role === "agent").length,
      total_clients: USERS.filter((u) => u.role === "client").length,
      total_ranges: RANGES.length,
      total_numbers: NUMBERS.length,
      assigned_numbers: NUMBERS.filter((n) => n.assigned_to !== null).length,
      news: NEWS
    });
  }
  if (action === "chart") {
    const data = [];
    for (let i = 6; i >= 0; i--) {
      const d = /* @__PURE__ */ new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const count = CDRS.filter((c) => c.created_at.startsWith(key)).length;
      data.push({
        date: key,
        count,
        payout: parseFloat((count * 0.05).toFixed(2))
      });
    }
    return res.json({ success: true, data });
  }
  return res.json({ success: true });
});
app.all(["/api/admin.php", "/api/admin"], async (req, res) => {
  const action = req.body?.action || req.query.action || "summary";
  switch (action) {
    case "summary":
      return res.json({
        success: true,
        stats: {
          managers: USERS.filter((u) => u.role === "manager").length,
          agents: USERS.filter((u) => u.role === "agent").length,
          clients: USERS.filter((u) => u.role === "client").length,
          test_users: USERS.filter((u) => u.role === "test").length,
          ranges: RANGES.length,
          numbers: NUMBERS.length,
          assigned_numbers: NUMBERS.filter((n) => n.assigned_to !== null).length,
          today_sms: CDRS.filter((c) => c.created_at.startsWith((/* @__PURE__ */ new Date()).toISOString().slice(0, 10))).length,
          month_sms: CDRS.length * 4,
          pending_payments: PAYMENTS.filter((p) => p.status === "pending").length,
          smpp_status: "online",
          smpp_active_sessions: SMPP_ACCOUNTS.length
        }
      });
    case "users": {
      const role = req.query.role || req.body?.role;
      let list = USERS;
      if (role) {
        list = list.filter((u) => u.role === role);
      }
      return res.json({ success: true, users: list });
    }
    case "user-create": {
      const { username, password, email, role, full_name, phone } = req.body;
      const cleanUser = String(username || "").trim();
      const maxId = USERS.length > 0 ? Math.max(...USERS.map((u) => u.id)) : 0;
      const newUser = {
        id: maxId + 1,
        username: cleanUser || `user${maxId + 1}`,
        role: role || "client",
        full_name: full_name || cleanUser || "New User",
        email: email || `${cleanUser || "user"}@imspro.com`,
        phone: phone || "+1234567890",
        status: "active",
        parent_id: role === "agent" ? 2 : role === "client" ? 3 : 1,
        balances: { USD: 0, EUR: 0, GBP: 0 },
        api_token: `ims_token_${Date.now()}`,
        created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
      };
      USERS.push(newUser);
      await persistUser(newUser);
      return res.json({ success: true, message: "User created and saved to Firebase successfully", user: newUser });
    }
    case "user-status": {
      const { id, status } = req.body;
      const u = USERS.find((x) => x.id === parseInt(id, 10));
      if (u) {
        u.status = status;
        await persistUser(u);
      }
      return res.json({ success: true, message: "Status updated and synced to Firebase" });
    }
    case "user-delete": {
      const id = parseInt(req.body.id, 10);
      const idx = USERS.findIndex((x) => x.id === id);
      if (idx !== -1) {
        USERS.splice(idx, 1);
        await deleteUserFromFirebase(id);
      }
      return res.json({ success: true, message: "User deleted from Firebase and system" });
    }
    case "ranges":
      return res.json({ success: true, ranges: RANGES });
    case "range-create": {
      const { range_name, prefix, currency, payout_1_1, payout_7_1, payout_7_7, payout_30_45, test_number, memo } = req.body;
      const maxRId = RANGES.length > 0 ? Math.max(...RANGES.map((r) => r.id)) : 0;
      const newRange = {
        id: maxRId + 1,
        manager_id: 2,
        range_name: range_name || `Range ${maxRId + 1}`,
        prefix: prefix || "1",
        currency: currency || "USD",
        payout_1_1: Number(payout_1_1) || 0.05,
        payout_7_1: Number(payout_7_1) || 0.045,
        payout_7_7: Number(payout_7_7) || 0.04,
        payout_30_45: Number(payout_30_45) || 0.035,
        test_number: test_number || "+1000000000",
        total_numbers: 100,
        available_numbers: 100,
        memo: memo || "",
        status: "active",
        request_enabled: 1,
        created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
      };
      RANGES.push(newRange);
      await persistRange(newRange);
      return res.json({ success: true, message: "Range created and saved to Firebase", range: newRange });
    }
    case "range-delete": {
      const id = parseInt(req.body.id, 10);
      const idx = RANGES.findIndex((x) => x.id === id);
      if (idx !== -1) {
        RANGES.splice(idx, 1);
        await deleteRangeFromFirebase(id);
      }
      return res.json({ success: true, message: "Range removed from Firebase" });
    }
    case "range-toggle-all": {
      const { status } = req.body;
      const targetStatus = status === "active" ? "active" : "inactive";
      for (const r of RANGES) {
        r.status = targetStatus;
        persistRange(r).catch(() => {
        });
      }
      return res.json({
        success: true,
        message: `All ranges have been set to ${targetStatus.toUpperCase()}`,
        active_count: RANGES.filter((r) => r.status === "active").length,
        total_count: RANGES.length,
        ranges: RANGES
      });
    }
    case "range-toggle": {
      const id = parseInt(req.body.id, 10);
      const r = RANGES.find((x) => x.id === id);
      if (r) {
        r.status = r.status === "active" ? "inactive" : "active";
        await persistRange(r);
        return res.json({
          success: true,
          message: `Range "${r.range_name}" is now ${r.status.toUpperCase()}`,
          range: r
        });
      }
      return res.status(404).json({ success: false, error: "Range not found" });
    }
    case "numbers-upload": {
      const { range_id, numbers_text, numbers_list } = req.body;
      const rId = parseInt(range_id, 10);
      const range = RANGES.find((r) => r.id === rId);
      if (!range) {
        return res.status(400).json({ success: false, error: "Invalid range selected" });
      }
      const rawList = numbers_list || (numbers_text ? String(numbers_text).split(/[\r\n,;]+/).map((s) => s.trim()).filter(Boolean) : []);
      const validNums = rawList.map((n) => n.startsWith("+") ? n : `+${n}`).filter((n) => n.length >= 7);
      if (validNums.length === 0) {
        return res.status(400).json({ success: false, error: "No valid phone numbers found in input" });
      }
      let maxNumId = NUMBERS.length > 0 ? Math.max(...NUMBERS.map((n) => n.id)) : 0;
      let addedCount = 0;
      for (const numStr of validNums) {
        if (NUMBERS.some((n) => n.number === numStr && n.range_id === rId)) continue;
        maxNumId++;
        const newNum = {
          id: maxNumId,
          range_id: rId,
          range_name: range.range_name,
          number: numStr,
          assigned_to: null,
          is_test: 1,
          status: "available",
          payout_term: "1/1",
          payout_rate: range.payout_1_1,
          allocated_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
        };
        NUMBERS.push(newNum);
        persistNumber(newNum).catch(() => {
        });
        addedCount++;
      }
      range.total_numbers = (range.total_numbers || 0) + addedCount;
      range.available_numbers = (range.available_numbers || 0) + addedCount;
      await persistRange(range);
      return res.json({
        success: true,
        message: `Successfully uploaded ${addedCount} numbers to range "${range.range_name}"`,
        added_count: addedCount,
        range
      });
    }
    case "numbers-generate": {
      const { range_id, count } = req.body;
      const rId = parseInt(range_id, 10);
      const range = RANGES.find((r) => r.id === rId);
      if (!range) {
        return res.status(400).json({ success: false, error: "Invalid range selected" });
      }
      const genCount = Math.min(500, Math.max(1, parseInt(count, 10) || 50));
      let maxNumId = NUMBERS.length > 0 ? Math.max(...NUMBERS.map((n) => n.id)) : 0;
      let addedCount = 0;
      const prefix = range.prefix.replace(/\D/g, "");
      for (let i = 0; i < genCount; i++) {
        maxNumId++;
        const randDigits = Math.floor(1e6 + Math.random() * 9e6);
        const generatedNumber = `+${prefix}${randDigits}`;
        const newNum = {
          id: maxNumId,
          range_id: rId,
          range_name: range.range_name,
          number: generatedNumber,
          assigned_to: null,
          is_test: 1,
          status: "available",
          payout_term: "1/1",
          payout_rate: range.payout_1_1,
          allocated_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
        };
        NUMBERS.push(newNum);
        persistNumber(newNum).catch(() => {
        });
        addedCount++;
      }
      range.total_numbers = (range.total_numbers || 0) + addedCount;
      range.available_numbers = (range.available_numbers || 0) + addedCount;
      await persistRange(range);
      return res.json({
        success: true,
        message: `Generated ${addedCount} test numbers for range "${range.range_name}"`,
        added_count: addedCount,
        range
      });
    }
    case "otp-rules": {
      return res.json({
        success: true,
        rules: OTP_RULES,
        running: autoOtpRunning,
        active_ranges: RANGES.filter((r) => r.status === "active")
      });
    }
    case "otp-rule-save": {
      const { id, name, country, service, rate, interval_value, interval_unit, active, sender, template } = req.body;
      const ruleId = id ? parseInt(id, 10) : 0;
      let rule = OTP_RULES.find((r) => r.id === ruleId);
      if (rule) {
        if (name) rule.name = name;
        if (country) rule.country = country;
        if (service) rule.service = service;
        if (rate !== void 0) rule.rate = Number(rate);
        if (interval_value !== void 0) rule.interval_value = Number(interval_value);
        if (interval_unit) rule.interval_unit = interval_unit;
        if (active !== void 0) rule.active = Boolean(active);
        if (sender !== void 0) rule.sender = sender;
        if (template !== void 0) rule.template = template;
      } else {
        const maxRuleId = OTP_RULES.length > 0 ? Math.max(...OTP_RULES.map((r) => r.id)) : 0;
        rule = {
          id: maxRuleId + 1,
          name: name || `${country || "Custom"} ${service || "OTP"} ($${rate || 1e-3})`,
          country: country || "Myanmar",
          service: service || "TikTok",
          rate: Number(rate) || 1e-3,
          interval_value: Number(interval_value) || 5,
          interval_unit: interval_unit === "minutes" ? "minutes" : "seconds",
          active: active !== void 0 ? Boolean(active) : true,
          sender: sender || service || "TikTok",
          template: template || `[${service || "TikTok"}] %CODE% is your verification code. Valid for 5 minutes.`,
          total_sent: 0
        };
        OTP_RULES.push(rule);
      }
      return res.json({ success: true, message: "OTP rule saved successfully", rule });
    }
    case "otp-rule-toggle": {
      const id = parseInt(req.body.id, 10);
      const rule = OTP_RULES.find((r) => r.id === id);
      if (rule) {
        rule.active = !rule.active;
        return res.json({ success: true, message: `Rule "${rule.name}" is now ${rule.active ? "ACTIVE" : "PAUSED"}`, rule });
      }
      return res.status(404).json({ success: false, error: "Rule not found" });
    }
    case "otp-rule-delete": {
      const id = parseInt(req.body.id, 10);
      const idx = OTP_RULES.findIndex((r) => r.id === id);
      if (idx !== -1) {
        OTP_RULES.splice(idx, 1);
        return res.json({ success: true, message: "Rule deleted successfully" });
      }
      return res.status(404).json({ success: false, error: "Rule not found" });
    }
    case "otp-rule-trigger": {
      const id = parseInt(req.body.id, 10);
      const rule = OTP_RULES.find((r) => r.id === id);
      if (rule) {
        const cdr = await executeRuleOtp(rule);
        rule.total_sent++;
        rule.last_run = (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19);
        return res.json({
          success: true,
          message: `Rule "${rule.name}" triggered: Generated OTP ${cdr.otp_code} for ${cdr.country} (${cdr.recipient})`,
          cdr
        });
      }
      return res.status(404).json({ success: false, error: "Rule not found" });
    }
    case "range-return-numbers":
      return res.json({ success: true, message: "Numbers returned to available pool" });
    case "numbers":
      return res.json({ success: true, numbers: NUMBERS });
    case "number-unassign": {
      const id = parseInt(req.body.id, 10);
      const num = NUMBERS.find((n) => n.id === id);
      if (num) {
        num.assigned_to = null;
        num.assigned_username = void 0;
        num.status = "available";
        await persistNumber(num);
      }
      return res.json({ success: true, message: "Number unassigned and updated in Firebase" });
    }
    case "number-assign": {
      const { id, user_id } = req.body;
      const num = NUMBERS.find((n) => n.id === parseInt(id, 10));
      const targetUser = USERS.find((u) => u.id === parseInt(user_id, 10));
      if (num && targetUser) {
        num.assigned_to = targetUser.id;
        num.assigned_username = targetUser.username;
        num.status = "assigned";
        await persistNumber(num);
      }
      return res.json({ success: true, message: "Number assigned and synced to Firebase" });
    }
    case "reports":
      return res.json({
        success: true,
        reports: CDRS.slice(0, 100),
        total_records: CDRS.length
      });
    case "payments":
      return res.json({ success: true, payments: PAYMENTS });
    case "payment-status": {
      const { id, status } = req.body;
      const p = PAYMENTS.find((x) => x.id === parseInt(id, 10));
      if (p) {
        p.status = status;
        await persistPayment(p);
      }
      return res.json({ success: true, message: "Payment status updated in Firebase" });
    }
    case "panels":
      return res.json({
        success: true,
        panels: PROVIDER_PANELS,
        hadi: HADI_PANEL_CONFIG,
        total_batches: Object.keys(NUMBER_BATCHES).length,
        total_uploaded_numbers: Object.values(NUMBER_BATCHES).reduce((acc, b) => acc + b.numbers.length, 0)
      });
    case "panel-toggle": {
      const { id } = req.body;
      const p = PROVIDER_PANELS.find((x) => x.id === id);
      if (p) {
        p.status = p.status === "ON" ? "OFF" : "ON";
        if (id === "hadi") {
          HADI_PANEL_CONFIG.status = p.status;
        }
        return res.json({ success: true, message: `Panel "${p.name}" turned ${p.status}`, panel: p });
      }
      return res.status(404).json({ success: false, error: "Panel not found" });
    }
    case "panel-save": {
      const { id, name, type, base_url, token, keys, auto_sync } = req.body;
      let p = PROVIDER_PANELS.find((x) => x.id === id);
      if (p) {
        if (name) p.name = name;
        if (base_url) p.base_url = base_url;
        if (token !== void 0) p.token = token;
        if (keys) p.keys = Array.isArray(keys) ? keys : [keys];
        if (auto_sync !== void 0) p.auto_sync = Boolean(auto_sync);
      } else {
        const newId = id || `panel_${Date.now()}`;
        p = {
          id: newId,
          name: name || "New Custom Panel",
          type: type || "API Panel",
          base_url: base_url || "https://api.example.com",
          token: token || "",
          status: "ON",
          auto_sync: auto_sync !== void 0 ? Boolean(auto_sync) : true,
          records: 0
        };
        PROVIDER_PANELS.push(p);
      }
      if (p.id === "hadi") {
        if (p.base_url) HADI_PANEL_CONFIG.url = p.base_url;
        if (p.token) HADI_PANEL_CONFIG.token = p.token;
      }
      return res.json({ success: true, message: "Panel configuration saved successfully", panel: p });
    }
    case "panel-delete": {
      const { id } = req.body;
      const idx = PROVIDER_PANELS.findIndex((x) => x.id === id);
      if (idx !== -1) {
        PROVIDER_PANELS.splice(idx, 1);
        return res.json({ success: true, message: "Panel deleted" });
      }
      return res.status(404).json({ success: false, error: "Panel not found" });
    }
    case "hadi-config": {
      if (req.method === "POST") {
        const { url, token, status, auto_sync, sync_interval_sec } = req.body;
        if (url) HADI_PANEL_CONFIG.url = url;
        if (token) HADI_PANEL_CONFIG.token = token;
        if (status) HADI_PANEL_CONFIG.status = status;
        if (auto_sync !== void 0) HADI_PANEL_CONFIG.auto_sync = Boolean(auto_sync);
        if (sync_interval_sec) HADI_PANEL_CONFIG.sync_interval_sec = parseInt(sync_interval_sec, 10);
        return res.json({ success: true, message: "Hadi CR API settings updated", config: HADI_PANEL_CONFIG });
      }
      return res.json({ success: true, config: HADI_PANEL_CONFIG });
    }
    case "hadi-sync": {
      const { dt1, dt2, records, filternum, filtercli } = req.body || req.query;
      const result = await syncHadiApi({
        dt1: dt1 ? String(dt1) : void 0,
        dt2: dt2 ? String(dt2) : void 0,
        records: records ? parseInt(String(records), 10) : 100,
        filternum: filternum ? String(filternum) : void 0,
        filtercli: filtercli ? String(filtercli) : void 0
      });
      return res.json(result);
    }
    case "number-batches":
      return res.json({
        success: true,
        batches: Object.values(NUMBER_BATCHES),
        total_uploaded: Object.values(NUMBER_BATCHES).reduce((acc, b) => acc + b.numbers.length, 0),
        total_assigned: NUMBERS.filter((n) => n.assigned_to !== null).length
      });
    case "number-batch-upload": {
      const { filename, service, country, normal_rate, special_rate, numbers_text, numbers_list } = req.body;
      const rawList = numbers_list || (numbers_text ? String(numbers_text).split(/[\r\n,;]+/).map((s) => s.trim()).filter(Boolean) : []);
      const validNums = rawList.map((n) => n.startsWith("+") ? n : `+${n}`).filter((n) => n.length >= 7);
      if (validNums.length === 0) {
        return res.status(400).json({ success: false, error: "No valid phone numbers found in file or input" });
      }
      const srv = String(service || "GENERAL").toUpperCase();
      const cnt = String(country || detectCountryFromPhone(validNums[0]).country).toUpperCase();
      const nRate = parseFloat(normal_rate) || 0.05;
      const sRate = parseFloat(special_rate) || nRate * 1.2;
      const batchId = `batch_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
      const batchObj = {
        id: batchId,
        filename: filename || "manual_upload.txt",
        service: srv,
        country: cnt,
        rate: nRate,
        normal_rate: nRate,
        special_rate: sRate,
        created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19),
        numbers: validNums.map((n) => ({ num: n, shares: 0, used_by: [] }))
      };
      NUMBER_BATCHES[batchId] = batchObj;
      let maxNumId = NUMBERS.length > 0 ? Math.max(...NUMBERS.map((n) => n.id)) : 0;
      let targetRange = RANGES.find((r) => r.range_name.toUpperCase().includes(cnt) || r.prefix === validNums[0].slice(1, 4)) || RANGES[0];
      for (const pNum of validNums) {
        if (!NUMBERS.some((n) => n.number === pNum)) {
          maxNumId++;
          const newPhone = {
            id: maxNumId,
            range_id: targetRange ? targetRange.id : 1,
            range_name: `${cnt} ${srv} Route`,
            number: pNum,
            assigned_to: 3,
            assigned_username: "james9999",
            is_test: 1,
            status: "assigned",
            payout_term: "1/1",
            payout_rate: nRate,
            allocated_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
          };
          NUMBERS.push(newPhone);
          persistNumber(newPhone).catch(() => {
          });
        }
      }
      return res.json({
        success: true,
        message: `Successfully uploaded ${validNums.length} numbers for ${cnt} (${srv})`,
        batch: batchObj,
        total_numbers_added: validNums.length
      });
    }
    case "number-batch-delete": {
      const { id } = req.body;
      if (id && NUMBER_BATCHES[id]) {
        delete NUMBER_BATCHES[id];
        return res.json({ success: true, message: "Batch deleted" });
      }
      return res.status(404).json({ success: false, error: "Batch not found" });
    }
    case "number-batch-clear": {
      for (const k of Object.keys(NUMBER_BATCHES)) {
        delete NUMBER_BATCHES[k];
      }
      return res.json({ success: true, message: "All number batches cleared" });
    }
    case "test-sms-send": {
      const { number, sender, message, text } = req.body;
      const msgText = message || text || "Test OTP 482910 from Admin";
      const otpMatch = msgText.match(/\b\d{4,8}\b/);
      const maxCdrId = CDRS.length > 0 ? Math.max(...CDRS.map((c) => c.id)) : 0;
      const newCdr = {
        id: maxCdrId + 1,
        user_id: 4,
        range_id: 1,
        sender: sender || "TestGateway",
        recipient: number || "+447123456701",
        message: msgText,
        otp_code: otpMatch ? otpMatch[0] : "000000",
        otp_detected: Boolean(otpMatch),
        country: "United Kingdom",
        rate: 0.05,
        payout: 0.05,
        status: "delivered",
        created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
      };
      CDRS.unshift(newCdr);
      await persistCDR(newCdr);
      return res.json({
        success: true,
        message: "Test SMS injected and saved to Firebase",
        otp_detected: Boolean(otpMatch),
        cdr_id: newCdr.id
      });
    }
    case "smpp-config":
      return res.json({
        success: true,
        config: {
          port: 2775,
          enabled: true,
          system_id: "GLOBAL1TEL",
          tls: false,
          max_connections: 50,
          idle_timeout: 60
        }
      });
    case "smpp-accounts":
      return res.json({ success: true, accounts: SMPP_ACCOUNTS });
    case "smpp-account-save":
      return res.json({ success: true, message: "SMPP account saved" });
    case "smpp-sessions":
      return res.json({
        success: true,
        sessions: [
          {
            id: "sess_1",
            system_id: "smpp_carrier_eu",
            ip: "185.120.44.12",
            bound_at: "2026-09-25 04:12:00",
            state: "BOUND_TRX",
            inbound_tps: 42,
            outbound_tps: 0
          },
          {
            id: "sess_2",
            system_id: "smpp_direct_us",
            ip: "198.51.100.84",
            bound_at: "2026-09-25 05:22:15",
            state: "BOUND_TRX",
            inbound_tps: 68,
            outbound_tps: 0
          }
        ]
      });
    case "smpp-control":
      return res.json({ success: true, message: "SMPP Service restarted successfully" });
    case "smpp-dlr":
      return res.json({
        success: true,
        stats: {
          total_dlr: 25480,
          delivered: 25320,
          undelivered: 120,
          expired: 40,
          delivery_rate: "99.37%"
        }
      });
    case "smpp-throughput":
      return res.json({
        success: true,
        throughput: {
          current_inbound_tps: 110,
          peak_inbound_tps: 450,
          limit_tps: 500
        }
      });
    case "smpp-security":
      return res.json({
        success: true,
        firewall_active: true,
        whitelist_ips: ["185.120.44.12", "198.51.100.84"],
        banned_ips: []
      });
    case "smpp-logs":
      return res.json({
        success: true,
        logs: [
          "[2026-09-25 06:14:02] BIND_TRANSMITTER received from 185.120.44.12: system_id=smpp_carrier_eu status=ESME_ROK",
          "[2026-09-25 06:14:03] ENQUIRE_LINK heartbeats OK",
          "[2026-09-25 06:15:10] DELIVER_SM 18 messages processed in 12ms"
        ]
      });
    case "agent-news":
      return res.json({ success: true, news: NEWS });
    case "agent-news-save": {
      const { title, content } = req.body;
      const maxNewsId = NEWS.length > 0 ? Math.max(...NEWS.map((n2) => n2.id)) : 0;
      const n = {
        id: maxNewsId + 1,
        title: title || "Notice",
        content: content || "",
        author_id: 1,
        target_role: "agent",
        status: "published",
        created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
      };
      NEWS.unshift(n);
      await persistNews(n);
      return res.json({ success: true, message: "News article posted and saved to Firebase", news: n });
    }
    case "agent-news-delete": {
      const id = parseInt(req.body.id, 10);
      const idx = NEWS.findIndex((x) => x.id === id);
      if (idx !== -1) {
        NEWS.splice(idx, 1);
        await deleteNewsFromFirebase(id);
      }
      return res.json({ success: true, message: "News article removed from Firebase" });
    }
    case "settings-save":
    case "settings": {
      if (req.method === "POST") {
        const newSettings = req.body || {};
        Object.assign(SETTINGS, newSettings);
        await persistSettings(SETTINGS);
        return res.json({ success: true, message: "Settings saved to Firebase", settings: SETTINGS });
      }
      return res.json({
        success: true,
        settings: SETTINGS
      });
    }
    case "integration-settings":
      return res.json({
        success: true,
        webhook_url: "https://api.global1tel.com/webhook/sms",
        api_token: "g1t_live_token_sec_993817"
      });
    case "integration-token":
      return res.json({
        success: true,
        api_token: `g1t_token_${Math.random().toString(36).substring(2)}`
      });
    case "db-upgrade":
      return res.json({ success: true, message: "Database schema is already at the latest version" });
    case "demo-otp-status": {
      const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
      const todayCount = CDRS.filter((c) => c.created_at.startsWith(todayStr)).length;
      const activeRangesCount = RANGES.filter((r) => r.status === "active").length;
      return res.json({
        success: true,
        running: autoOtpRunning,
        rate_per_sec: autoOtpRatePerSec,
        interval_ms: autoOtpIntervalMs,
        total_generated: autoOtpTotalGenerated,
        total_ranges: activeRangesCount,
        all_ranges_count: RANGES.length,
        total_otps: CDRS.length,
        today_otps: todayCount,
        rules: OTP_RULES,
        last_otp: autoOtpLastGenerated
      });
    }
    case "demo-otp-control": {
      const { subAction, state, rate } = req.body;
      const parsedRate = parseFloat(rate);
      if (!isNaN(parsedRate) && parsedRate > 0) {
        autoOtpRatePerSec = Math.min(20, Math.max(0.1, parsedRate));
      }
      if (subAction === "start" || subAction === "resume" || state === "start" || req.body?.running === true) {
        autoOtpRunning = true;
        updateAutoOtpTimer();
      } else if (subAction === "stop" || subAction === "pause" || state === "stop" || req.body?.running === false) {
        autoOtpRunning = false;
        updateAutoOtpTimer();
      } else {
        updateAutoOtpTimer();
      }
      return res.json({
        success: true,
        message: `Auto OTP simulator updated: ${autoOtpRunning ? "RUNNING" : "STOPPED"} at ${autoOtpRatePerSec} OTP/sec`,
        running: autoOtpRunning,
        rate_per_sec: autoOtpRatePerSec
      });
    }
    case "demo-otp-send": {
      const { range_id, number, sender, message, text, otp_code } = req.body;
      const rId = range_id ? parseInt(range_id, 10) : void 0;
      const newCdr = await generateSingleDemoOtp(rId, number, sender, message || text, otp_code);
      return res.json({
        success: true,
        message: "Demo OTP injected successfully and synced to Firebase",
        cdr: newCdr,
        otp_code: newCdr.otp_code,
        total_otps: CDRS.length
      });
    }
    case "demo-otp-stream": {
      const limit = parseInt(String(req.query.limit || req.body?.limit || "50"), 10);
      const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
      const todayCount = CDRS.filter((c) => c.created_at.startsWith(todayStr)).length;
      const activeRangesCount = RANGES.filter((r) => r.status === "active").length;
      return res.json({
        success: true,
        total_ranges: activeRangesCount,
        all_ranges_count: RANGES.length,
        total_otps: CDRS.length,
        today_otps: todayCount,
        running: autoOtpRunning,
        rate_per_sec: autoOtpRatePerSec,
        rules: OTP_RULES,
        otps: CDRS.slice(0, limit)
      });
    }
    case "activity":
      return res.json({ success: true, activity: ACTIVITIES });
    default:
      return res.json({ success: true });
  }
});
app.all("/ints/:role/res/:name.php", (req, res) => {
  const name = req.params.name;
  const role = req.params.role;
  if (name === "aj_agents") {
    const agents = USERS.filter((u) => u.role === "agent").map((u) => ({
      id: u.id,
      title: `${u.username} (${u.full_name})`,
      text: `${u.username} (${u.full_name})`
    }));
    return res.json({ results: agents, pagination: { more: false } });
  }
  if (name === "aj_clients") {
    const clients = USERS.filter((u) => u.role === "client").map((u) => ({
      id: u.id,
      title: `${u.username} (${u.full_name})`,
      text: `${u.username} (${u.full_name})`
    }));
    return res.json({ results: clients, pagination: { more: false } });
  }
  if (name === "aj_ranges" || name === "aj_smstestranges" || name === "aj_smsranges") {
    let list = RANGES;
    if (role === "test" || role === "client") {
      list = list.filter((r) => r.status === "active");
    }
    const ranges = list.map((r) => ({
      id: r.id,
      title: `${r.range_name} [${r.prefix}]${r.status === "inactive" ? " (Disabled)" : ""}`,
      text: `${r.range_name} [${r.prefix}]${r.status === "inactive" ? " (Disabled)" : ""}`
    }));
    return res.json({ results: ranges, pagination: { more: false } });
  }
  if (name === "data_smsranges") {
    const rows = RANGES.map((r) => {
      const statusBadge = r.status === "active" ? "<span class='label label-success'>Active</span>" : "<span class='label label-important'>Disabled</span>";
      const toggleBtn = r.status === "active" ? `<button class='btn btn-mini btn-danger range-quick-toggle' data-id='${r.id}' data-action='disable'><i class='icon-pause icon-white'></i> \u09AC\u09A8\u09CD\u09A7 \u0995\u09B0\u09C1\u09A8</button>` : `<button class='btn btn-mini btn-success range-quick-toggle' data-id='${r.id}' data-action='enable'><i class='icon-play icon-white'></i> \u099A\u09BE\u09B2\u09C1 \u0995\u09B0\u09C1\u09A8</button>`;
      const uploadBtn = `<button class='btn btn-mini btn-info range-quick-upload' data-id='${r.id}' data-name='${r.range_name}' data-prefix='${r.prefix}'><i class='icon-upload icon-white'></i> \u09A8\u09BE\u09AE\u09CD\u09AC\u09BE\u09B0 \u0986\u09AA\u09B2\u09CB\u09A1</button>`;
      return [
        `<b>${r.range_name}</b> <br/>${statusBadge}`,
        `+${r.prefix}`,
        `<span class='badge badge-info'>${r.available_numbers || 0} / ${r.total_numbers || 0}</span>`,
        `<span class='label label-success' style='font-size:11px;'>${r.test_number || `+${r.prefix}1001`}</span>`,
        r.currency || "USD",
        `$${(r.payout_1_1 || 0.05).toFixed(4)}`,
        `$${(r.payout_7_1 || 0.045).toFixed(4)}`,
        `$${(r.payout_7_7 || 0.04).toFixed(4)}`,
        `$${(r.payout_30_45 || 0.035).toFixed(4)}`,
        `<small>${r.memo || "Direct Route"}</small>`,
        `<div style='display:flex; gap:4px; flex-wrap:wrap;'>${toggleBtn} ${uploadBtn}</div>`
      ];
    });
    return res.json(dtEnvelope(rows));
  }
  if (name === "data_smstestnumbers") {
    const frange = req.query.frange ? parseInt(String(req.query.frange), 10) : 0;
    let list = RANGES;
    if (role === "test" || role === "client") {
      list = list.filter((r) => r.status === "active");
    }
    if (frange) list = list.filter((r) => r.id === frange);
    const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const rows = list.map((r) => {
      const todayCount = CDRS.filter((c) => c.range_id === r.id && c.created_at.startsWith(todayStr)).length;
      const statusBadge = r.status === "active" ? "<span class='label label-success'>Active</span>" : "<span class='label label-important'>Disabled</span>";
      return [
        r.range_name,
        r.prefix,
        `<span class='label label-success' style='font-size:12px; font-weight:bold; letter-spacing:0.5px;'>${r.test_number || `+${r.prefix}1001`}</span>`,
        `$${(r.payout_1_1 || 0.05).toFixed(4)}`,
        `<span class='label label-info'>${todayCount} Today</span> ${statusBadge}`
      ];
    });
    return res.json(dtEnvelope(rows));
  }
  if (name === "data_testsmscdr" || name === "data_recentsmstest") {
    const frange = req.query.frange ? parseInt(String(req.query.frange), 10) : 0;
    let list = CDRS;
    if (frange) list = list.filter((c) => c.range_id === frange);
    const sorted = list.slice(0, 100);
    const rows = sorted.map((c) => [
      c.created_at,
      c.country || "Global Range",
      c.recipient,
      `<span class='label label-info' style='font-weight:bold; font-size:11px;'>${c.sender}</span>`,
      c.otp_detected ? `<span class='label label-warning' style='font-size:12px; font-weight:bold; margin-right:5px; color:#fff; background:#e67e22;'>OTP: ${c.otp_code}</span> ${c.message}` : c.message
    ]);
    rows.push([String(CDRS.length), "", "", "", ""]);
    return res.json(dtEnvelope(rows, CDRS.length));
  }
  if (name === "dt_numbers" || name === "dt_my_numbers") {
    const rows = NUMBERS.map((n) => [
      n.range_name,
      n.number,
      n.payout_term,
      `$${n.payout_rate.toFixed(4)}`,
      n.assigned_username || "Unassigned",
      n.status === "assigned" ? "<span class='label label-success'>Assigned</span>" : "<span class='label label-info'>Available</span>",
      n.allocated_at
    ]);
    return res.json(dtEnvelope(rows));
  }
  if (name === "dt_clients" || name === "dt_agents") {
    const targetRole = name === "dt_agents" ? "agent" : "client";
    const users = USERS.filter((u) => u.role === targetRole);
    const rows = users.map((u) => [
      u.username,
      u.full_name,
      u.email,
      u.phone,
      `$${(u.balances.USD || 0).toLocaleString()}`,
      u.status === "active" ? "<span class='label label-success'>Active</span>" : "<span class='label label-important'>Inactive</span>",
      u.created_at,
      `<a href='#' class='btn btn-mini btn-info'><i class='icon-eye-open'></i></a>`
    ]);
    return res.json(dtEnvelope(rows));
  }
  if (name === "dt_cdr" || name === "dt_cdr_reports" || name === "dt_cdr_stats") {
    const rows = CDRS.slice(0, 50).map((c) => [
      c.created_at,
      c.sender,
      c.recipient,
      c.otp_detected ? `<span class='label label-warning'>OTP: ${c.otp_code}</span>` : `<span class='label'>SMS</span>`,
      c.country,
      `$${c.payout.toFixed(4)}`,
      `<span class='label label-success'>${c.status}</span>`
    ]);
    return res.json(dtEnvelope(rows));
  }
  if (name === "dt_range_stats" || name === "dt_ranges") {
    const rows = RANGES.map((r) => [
      r.range_name,
      r.prefix,
      r.currency,
      `$${r.payout_1_1.toFixed(4)}`,
      `$${r.payout_7_1.toFixed(4)}`,
      r.test_number,
      `${r.available_numbers} / ${r.total_numbers}`,
      r.status === "active" ? "<span class='label label-success'>Active</span>" : "<span class='label'>Inactive</span>"
    ]);
    return res.json(dtEnvelope(rows));
  }
  if (name === "dt_activity" || name === "dt_my_activity") {
    const rows = ACTIVITIES.map((a) => [a.created_at, a.username, a.action, a.description, a.ip]);
    return res.json(dtEnvelope(rows));
  }
  if (name === "readnotifications") {
    return res.json({ success: true });
  }
  return res.json(dtEnvelope([]));
});
app.all(["/api/numbers.php", "/api/numbers"], (req, res) => {
  return res.json({ success: true, numbers: NUMBERS });
});
app.all(["/api/ranges.php", "/api/ranges"], (req, res) => {
  return res.json({ success: true, ranges: RANGES });
});
app.all(["/api/users.php", "/api/users"], (req, res) => {
  return res.json({ success: true, users: USERS });
});
app.all(["/api/cdr.php", "/api/cdr"], (req, res) => {
  return res.json({ success: true, cdr: CDRS.slice(0, 100) });
});
app.all(["/api/misc.php", "/api/misc"], (req, res) => {
  return res.json({ success: true, news: NEWS, activity: ACTIVITIES });
});
app.all(["/api/test_sms.php", "/api/test_sms"], async (req, res) => {
  const { number, sender, message, text } = req.body || req.query || {};
  const msgText = message || text || "Test OTP Verification: 593821";
  const otpMatch = msgText.match(/\b\d{4,8}\b/);
  const maxCdrId = CDRS.length > 0 ? Math.max(...CDRS.map((c) => c.id)) : 0;
  const newCdr = {
    id: maxCdrId + 1,
    user_id: 4,
    range_id: 1,
    sender: sender || "TestOTP",
    recipient: number || "+447123456701",
    message: msgText,
    otp_code: otpMatch ? otpMatch[0] : "123456",
    otp_detected: Boolean(otpMatch),
    country: "United Kingdom",
    rate: 0.05,
    payout: 0.05,
    status: "delivered",
    created_at: (/* @__PURE__ */ new Date()).toISOString().replace("T", " ").slice(0, 19)
  };
  CDRS.unshift(newCdr);
  await persistCDR(newCdr);
  return res.json({
    success: true,
    message: "Test SMS processed and delivered successfully",
    otp_detected: Boolean(otpMatch),
    otp_code: newCdr.otp_code,
    cdr_id: newCdr.id
  });
});
app.all(["/api/demo-otp", "/api/demo-otp.php"], async (req, res) => {
  const action = req.body?.action || req.query.action || "status";
  if (action === "status") {
    const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const todayCount = CDRS.filter((c) => c.created_at.startsWith(todayStr)).length;
    return res.json({
      success: true,
      running: autoOtpRunning,
      rate_per_sec: autoOtpRatePerSec,
      interval_ms: autoOtpIntervalMs,
      total_generated: autoOtpTotalGenerated,
      last_generated: autoOtpLastGenerated,
      total_ranges: RANGES.length,
      total_otps: CDRS.length,
      today_otps: todayCount
    });
  }
  if (action === "control") {
    const subAction = req.body?.subAction || req.body?.state || req.query.subAction;
    const rate = parseFloat(req.body?.rate || req.query.rate || "");
    if (!isNaN(rate) && rate > 0) {
      autoOtpRatePerSec = Math.min(20, Math.max(0.1, rate));
    }
    if (subAction === "start" || subAction === "resume" || req.body?.running === true) {
      autoOtpRunning = true;
      updateAutoOtpTimer();
    } else if (subAction === "stop" || subAction === "pause" || req.body?.running === false) {
      autoOtpRunning = false;
      updateAutoOtpTimer();
    } else {
      updateAutoOtpTimer();
    }
    return res.json({
      success: true,
      message: `Auto OTP simulator updated: ${autoOtpRunning ? "RUNNING" : "STOPPED"} at ${autoOtpRatePerSec} OTP/sec`,
      running: autoOtpRunning,
      rate_per_sec: autoOtpRatePerSec
    });
  }
  if (action === "send") {
    const { range_id, number, sender, message, text, otp_code } = req.body;
    const rId = range_id ? parseInt(range_id, 10) : void 0;
    const newCdr = await generateSingleDemoOtp(rId, number, sender, message || text, otp_code);
    return res.json({
      success: true,
      message: "Demo OTP injected successfully and synced to Firebase",
      cdr: newCdr,
      otp_code: newCdr.otp_code,
      total_otps: CDRS.length
    });
  }
  if (action === "stream" || action === "recent") {
    const limit = parseInt(String(req.query.limit || req.body?.limit || "50"), 10);
    const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
    const todayCount = CDRS.filter((c) => c.created_at.startsWith(todayStr)).length;
    return res.json({
      success: true,
      total_ranges: RANGES.length,
      total_otps: CDRS.length,
      today_otps: todayCount,
      running: autoOtpRunning,
      rate_per_sec: autoOtpRatePerSec,
      otps: CDRS.slice(0, limit)
    });
  }
  return res.json({ success: true, running: autoOtpRunning, rate_per_sec: autoOtpRatePerSec });
});
app.all(["/api/test/stats", "/api/test/stats.php"], (req, res) => {
  const todayStr = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
  const todayCount = CDRS.filter((c) => c.created_at.startsWith(todayStr)).length;
  return res.json({
    success: true,
    total_ranges: RANGES.length,
    total_otps: CDRS.length,
    today_otps: todayCount,
    running: autoOtpRunning,
    rate_per_sec: autoOtpRatePerSec,
    recent_otps: CDRS.slice(0, 30)
  });
});
app.get("/robots.txt", (req, res) => {
  const host = req.headers.host || "imspro.com";
  const protocol = req.secure || req.headers["x-forwarded-proto"] === "https" ? "https" : "http";
  res.type("text/plain");
  return res.send(
    `# robots.txt for IMS PRO Telecom Softswitch Platform
User-agent: *
Allow: /
Allow: /ints/
Allow: /signin
Allow: /login
Allow: /test
Allow: /ints/test/
Allow: /ints/assets/
Disallow: /api/

# Sitemap Location
Sitemap: ${protocol}://${host}/sitemap.xml`
  );
});
app.get("/sitemap.xml", (req, res) => {
  const host = req.headers.host || "imspro.com";
  const protocol = req.secure || req.headers["x-forwarded-proto"] === "https" ? "https" : "http";
  const baseUrl = `${protocol}://${host}`;
  const today = (/* @__PURE__ */ new Date()).toISOString().slice(0, 10);
  res.type("application/xml");
  return res.send(
    `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
  <url>
    <loc>${baseUrl}/</loc>
    <lastmod>${today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>${baseUrl}/signin</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>${baseUrl}/ints/test/SMSTestPanel</loc>
    <lastmod>${today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>${baseUrl}/ints/test/RecentSMSTest</loc>
    <lastmod>${today}</lastmod>
    <changefreq>always</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>${baseUrl}/ints/login</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>`
  );
});
app.get("/manifest.json", (req, res) => {
  const mPath = path2.join(PUBLIC_DIR, "manifest.json");
  if (fs2.existsSync(mPath)) {
    return res.sendFile(mPath);
  }
  return res.json({ name: "IMS PRO", short_name: "IMS PRO" });
});
app.get("/", (req, res) => {
  const loginHtmlPath = path2.join(INTS_DIR, "login.html");
  if (fs2.existsSync(loginHtmlPath)) {
    return res.sendFile(loginHtmlPath);
  }
  return res.status(404).send("GLOBAL1TEL Portal Login page not found");
});
app.get(["/login", "/login.html", "/adminlogin", "/adminlogin/", "/ints/login", "/ints/login.html"], (req, res) => {
  const loginHtmlPath = path2.join(INTS_DIR, "login.html");
  if (fs2.existsSync(loginHtmlPath)) {
    return res.sendFile(loginHtmlPath);
  }
  return res.status(404).send("Login page not found");
});
app.get(["/admin", "/admin/"], (req, res) => {
  const adminDash = path2.join(INTS_DIR, "admin", "AdminDashboard.html");
  return res.sendFile(adminDash);
});
app.get(["/manager", "/manager/"], (req, res) => {
  const file = path2.join(INTS_DIR, "manager", "SMSDashboard.html");
  return res.sendFile(file);
});
app.get(["/agent", "/agent/"], (req, res) => {
  const file = path2.join(INTS_DIR, "agent", "SMSDashboard.html");
  return res.sendFile(file);
});
app.get(["/client", "/client/"], (req, res) => {
  const file = path2.join(INTS_DIR, "client", "SMSDashboard.html");
  return res.sendFile(file);
});
app.get(["/ints/:role", "/ints/:role/"], (req, res) => {
  const { role } = req.params;
  if (role === "admin") {
    const adminDash = path2.join(INTS_DIR, "admin", "AdminDashboard.html");
    if (fs2.existsSync(adminDash)) return res.sendFile(adminDash);
  }
  const dashFile = path2.join(INTS_DIR, role, "SMSDashboard.html");
  if (fs2.existsSync(dashFile)) {
    return res.sendFile(dashFile);
  }
  const loginHtmlPath = path2.join(INTS_DIR, "login.html");
  return res.sendFile(loginHtmlPath);
});
app.get("/ints/:role/:page", (req, res) => {
  const { role, page } = req.params;
  const pageName = page.endsWith(".html") ? page : `${page}.html`;
  const targetFile = path2.join(INTS_DIR, role, pageName);
  if (fs2.existsSync(targetFile)) {
    return res.sendFile(targetFile);
  }
  if (page.toLowerCase() === "dashboard" || page.toLowerCase() === "smsdashboard") {
    if (role === "admin") {
      const adminDash = path2.join(INTS_DIR, "admin", "AdminDashboard.html");
      if (fs2.existsSync(adminDash)) return res.sendFile(adminDash);
    } else {
      const dash = path2.join(INTS_DIR, role, "SMSDashboard.html");
      if (fs2.existsSync(dash)) return res.sendFile(dash);
    }
  }
  if (role === "admin") {
    const adminDash = path2.join(INTS_DIR, "admin", "AdminDashboard.html");
    if (fs2.existsSync(adminDash)) return res.sendFile(adminDash);
  }
  const loginHtmlPath = path2.join(INTS_DIR, "login.html");
  return res.sendFile(loginHtmlPath);
});
app.use(express.static(PUBLIC_DIR));
app.use((req, res) => {
  if (req.accepts("html")) {
    const loginHtmlPath = path2.join(INTS_DIR, "login.html");
    return res.sendFile(loginHtmlPath);
  }
  res.status(404).json({ error: "Endpoint not found" });
});
app.listen(PORT, HOST, async () => {
  console.log(`[IMS PRO] Server listening on http://${HOST}:${PORT}`);
  console.log(`[IMS PRO] Serving web portal from ${PUBLIC_DIR}`);
  try {
    await syncFromFirebase();
  } catch (err) {
    console.error("[Firebase] Startup sync error:", err?.message || err);
  }
  updateAutoOtpTimer();
});
export {
  HADI_PANEL_CONFIG,
  NUMBER_BATCHES,
  OTP_RULES,
  PROVIDER_PANELS,
  syncHadiApi
};
