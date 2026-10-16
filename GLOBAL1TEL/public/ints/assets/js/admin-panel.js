function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t.return && (u = t.return(), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i.return) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); } r ? i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n : (o("next", 0), o("throw", 1), o("return", 2)); }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
(function () {
  'use strict';

  var $ = function $(s) {
      var r = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : document;
      return r.querySelector(s);
    },
    $$ = function $$(s) {
      var r = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : document;
      return Array.from(r.querySelectorAll(s));
    };
  var api = '/api/admin.php';
  var adminUser = null;
  var smppProfiles = [];
  var agentNewsRows = [];
  var rangeRows = [];
  var globalAgentRows = [];
  var roleMeta = {
    manager: {
      body: '#managersBody',
      search: '#managerSearch',
      status: '#managerStatus'
    },
    agent: {
      body: '#agentsBody',
      search: '#agentSearch',
      status: '#agentStatus'
    },
    client: {
      body: '#clientsBody',
      search: '#clientSearch',
      status: '#clientStatus'
    },
    test: {
      body: '#testBody',
      search: '#testSearch',
      status: '#testStatus'
    }
  };
  var titles = {
    dashboard: ['Dashboard', 'Global system overview'],
    managers: ['Managers', 'Create and control Manager accounts'],
    agents: ['Agents', 'All Agents across every Manager'],
    clients: ['Clients', 'All Clients across every Agent'],
    test: ['Test Accounts', 'Separate Test-role accounts controlled by Admin'],
    ranges: ['SMS Ranges', 'Admin-owned range creation and number import'],
    numbers: ['All Numbers', 'Global number inventory'],
    reports: ['SMS / OTP Stats', 'CDR metadata and masked OTP-event analytics'],
    payments: ['Payment Requests', 'Review withdrawals across the hierarchy'],
    testsms: ['Test SMS', 'Manually inject a fake incoming SMS for any number'],
    'smpp-dashboard': ['SMPP Dashboard', 'Server performance and inbound SMS overview'],
    'smpp-accounts': ['SMPP Accounts', 'Supplier/client credentials for SMPP binds'],
    'smpp-sessions': ['SMPP Sessions', 'Gateway session telemetry'],
    'connected-clients': ['Connected Clients', 'Current SMPP clients known to gateway telemetry'],
    'dlr-monitor': ['DLR Monitor', 'Delivery receipt status from SMPP CDR'],
    'throughput-monitor': ['Throughput Monitor', 'Inbound SMPP message rate'],
    'smpp-security': ['SMPP Security Center', 'SMPP credential and access controls'],
    'connection-logs': ['Connection Logs', 'Recent SMPP gateway events'],
    http: ['HTTP Provider', 'HTTP/SMS provider connection and field setup'],
    api: ['API Tokens', 'External application API access'],
    webhook: ['Webhook Config', 'Automatic event delivery to external systems'],
    endpoint: ['API Playground', 'Test Gateway API requests from Admin'],
    agentnews: ['News for Agents', 'Publish announcements to Agent dashboards'],
    settings: ['System Settings', 'Global operational controls'],
    activity: ['Activity Log', 'Latest system activity']
  };
  function esc(v) {
    return String(v !== null && v !== void 0 ? v : '').replace(/[&<>'"]/g, function (c) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[c];
    });
  }
  function badge(v) {
    var x = String(v || '').toLowerCase().replace(/[^a-z0-9_-]/g, '');
    return "<span class=\"badge ".concat(esc(x), "\">").concat(esc(v || '-'), "</span>");
  }
  function money(v) {
    var n = Number(v || 0);
    return Number.isFinite(n) ? n.toFixed(4) : '0.0000';
  }
  function dt(v) {
    if (!v) return '—';
    return esc(String(v).replace('T', ' ').slice(0, 19));
  }
  function toast(msg) {
    var error = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : false;
    var el = $('#toast');
    el.textContent = msg;
    el.className = 'toast show' + (error ? ' error' : '');
    clearTimeout(toast.t);
    toast.t = setTimeout(function () {
      return el.className = 'toast';
    }, 3600);
  }
  function req(_x) {
    return _req.apply(this, arguments);
  }
  function _req() {
    _req = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee4(action) {
      var opt,
        method,
        url,
        init,
        r,
        data,
        _args4 = arguments,
        _t3;
      return _regenerator().w(function (_context4) {
        while (1) switch (_context4.p = _context4.n) {
          case 0:
            opt = _args4.length > 1 && _args4[1] !== undefined ? _args4[1] : {};
            method = opt.method || 'GET';
            url = api + '?action=' + encodeURIComponent(action);
            if (opt.params) url += '&' + new URLSearchParams(opt.params).toString();
            init = {
              method: method,
              credentials: 'include',
              cache: 'no-store',
              headers: {
                'Accept': 'application/json'
              }
            };
            if (opt.body) {
              init.headers['Content-Type'] = 'application/json';
              init.body = JSON.stringify(opt.body);
            }
            _context4.n = 1;
            return fetch(url, init);
          case 1:
            r = _context4.v;
            data = {};
            _context4.p = 2;
            _context4.n = 3;
            return r.json();
          case 3:
            data = _context4.v;
            _context4.n = 5;
            break;
          case 4:
            _context4.p = 4;
            _t3 = _context4.v;
          case 5:
            if (r.ok) {
              _context4.n = 6;
              break;
            }
            if ((r.status === 401 || r.status === 403) && String(data.error || '').toLowerCase().includes('admin')) {
              location.replace('/adminlogin');
            }
            throw new Error(data.error || "Request failed (".concat(r.status, ")"));
          case 6:
            return _context4.a(2, data);
        }
      }, _callee4, null, [[2, 4]]);
    }));
    return _req.apply(this, arguments);
  }
  function reqForm(_x2, _x3) {
    return _reqForm.apply(this, arguments);
  }
  function _reqForm() {
    _reqForm = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee5(action, formData) {
      var r, data, _t4;
      return _regenerator().w(function (_context5) {
        while (1) switch (_context5.p = _context5.n) {
          case 0:
            _context5.n = 1;
            return fetch(api + '?action=' + encodeURIComponent(action), {
              method: 'POST',
              credentials: 'include',
              cache: 'no-store',
              headers: {
                'Accept': 'application/json'
              },
              body: formData
            });
          case 1:
            r = _context5.v;
            data = {};
            _context5.p = 2;
            _context5.n = 3;
            return r.json();
          case 3:
            data = _context5.v;
            _context5.n = 5;
            break;
          case 4:
            _context5.p = 4;
            _t4 = _context5.v;
          case 5:
            if (r.ok) {
              _context5.n = 6;
              break;
            }
            throw new Error(data.error || "Request failed (".concat(r.status, ")"));
          case 6:
            return _context5.a(2, data);
        }
      }, _callee5, null, [[2, 4]]);
    }));
    return _reqForm.apply(this, arguments);
  }
  function verifySession() {
    return _verifySession.apply(this, arguments);
  }
  function _verifySession() {
    _verifySession = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee6() {
      var r, d;
      return _regenerator().w(function (_context6) {
        while (1) switch (_context6.n) {
          case 0:
            _context6.n = 1;
            return fetch('/api/session.php', {
              credentials: 'include',
              cache: 'no-store'
            });
          case 1:
            r = _context6.v;
            if (r.ok) {
              _context6.n = 2;
              break;
            }
            location.replace('/ints/login');
            return _context6.a(2, false);
          case 2:
            _context6.n = 3;
            return r.json();
          case 3:
            d = _context6.v;
            adminUser = d.user;
            if (!(!adminUser || adminUser.role !== 'admin')) {
              _context6.n = 4;
              break;
            }
            location.replace(d.dashboard_url || '/ints/login');
            return _context6.a(2, false);
          case 4:
            $('#adminName').textContent = adminUser.username || 'Admin';
            $('.avatar').textContent = (adminUser.username || 'A').slice(0, 1).toUpperCase();
            return _context6.a(2, true);
        }
      }, _callee6);
    }));
    return _verifySession.apply(this, arguments);
  }
  function show(view) {
    $$('.view').forEach(function (x) {
      return x.classList.remove('active');
    });
    $$('.nav-item').forEach(function (x) {
      return x.classList.toggle('active', x.dataset.view === view);
    });
    var el = $('#view-' + view);
    if (el) el.classList.add('active');
    var t = titles[view] || [view, ''];
    $('#pageTitle').textContent = t[0];
    $('#pageSubtitle').textContent = t[1];
    $('#sidebar').classList.remove('open');
    loadView(view);
    location.hash = view;
  }
  function loadView(_x4) {
    return _loadView.apply(this, arguments);
  }
  function _loadView() {
    _loadView = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee7(view) {
      var _t5;
      return _regenerator().w(function (_context7) {
        while (1) switch (_context7.p = _context7.n) {
          case 0:
            _context7.p = 0;
            if (!(view === 'dashboard')) {
              _context7.n = 2;
              break;
            }
            _context7.n = 1;
            return loadDashboard();
          case 1:
            _context7.n = 43;
            break;
          case 2:
            if (!['managers', 'agents', 'clients'].includes(view)) {
              _context7.n = 4;
              break;
            }
            _context7.n = 3;
            return loadUsers(view.slice(0, -1));
          case 3:
            _context7.n = 43;
            break;
          case 4:
            if (!(view === 'test')) {
              _context7.n = 6;
              break;
            }
            _context7.n = 5;
            return loadUsers('test');
          case 5:
            _context7.n = 43;
            break;
          case 6:
            if (!(view === 'ranges')) {
              _context7.n = 8;
              break;
            }
            _context7.n = 7;
            return loadRanges();
          case 7:
            _context7.n = 43;
            break;
          case 8:
            if (!(view === 'numbers')) {
              _context7.n = 10;
              break;
            }
            _context7.n = 9;
            return loadNumbers();
          case 9:
            _context7.n = 43;
            break;
          case 10:
            if (!(view === 'reports')) {
              _context7.n = 12;
              break;
            }
            _context7.n = 11;
            return loadReports();
          case 11:
            _context7.n = 43;
            break;
          case 12:
            if (!(view === 'payments')) {
              _context7.n = 14;
              break;
            }
            _context7.n = 13;
            return loadPayments();
          case 13:
            _context7.n = 43;
            break;
          case 14:
            if (!(view === 'smpp-dashboard')) {
              _context7.n = 16;
              break;
            }
            _context7.n = 15;
            return loadSmppControl();
          case 15:
            _context7.n = 43;
            break;
          case 16:
            if (!(view === 'smpp-accounts')) {
              _context7.n = 18;
              break;
            }
            _context7.n = 17;
            return loadSmppAccounts();
          case 17:
            _context7.n = 43;
            break;
          case 18:
            if (!(view === 'smpp-sessions')) {
              _context7.n = 20;
              break;
            }
            _context7.n = 19;
            return loadSmppSessions();
          case 19:
            _context7.n = 43;
            break;
          case 20:
            if (!(view === 'connected-clients')) {
              _context7.n = 22;
              break;
            }
            _context7.n = 21;
            return loadSmppClients();
          case 21:
            _context7.n = 43;
            break;
          case 22:
            if (!(view === 'dlr-monitor')) {
              _context7.n = 24;
              break;
            }
            _context7.n = 23;
            return loadSmppDlr();
          case 23:
            _context7.n = 43;
            break;
          case 24:
            if (!(view === 'throughput-monitor')) {
              _context7.n = 26;
              break;
            }
            _context7.n = 25;
            return loadSmppThroughput();
          case 25:
            _context7.n = 43;
            break;
          case 26:
            if (!(view === 'smpp-security')) {
              _context7.n = 28;
              break;
            }
            _context7.n = 27;
            return loadSmppSecurity();
          case 27:
            _context7.n = 43;
            break;
          case 28:
            if (!(view === 'connection-logs')) {
              _context7.n = 30;
              break;
            }
            _context7.n = 29;
            return loadSmppLogs();
          case 29:
            _context7.n = 43;
            break;
          case 30:
            if (!(view === 'http')) {
              _context7.n = 32;
              break;
            }
            _context7.n = 31;
            return loadIntegrationSettings('http');
          case 31:
            _context7.n = 43;
            break;
          case 32:
            if (!(view === 'api')) {
              _context7.n = 34;
              break;
            }
            _context7.n = 33;
            return loadIntegrationSettings('api');
          case 33:
            _context7.n = 43;
            break;
          case 34:
            if (!(view === 'webhook')) {
              _context7.n = 36;
              break;
            }
            _context7.n = 35;
            return loadIntegrationSettings('webhook');
          case 35:
            _context7.n = 43;
            break;
          case 36:
            if (!(view === 'endpoint')) {
              _context7.n = 38;
              break;
            }
            _context7.n = 37;
            return loadIntegrationSettings('endpoint');
          case 37:
            _context7.n = 43;
            break;
          case 38:
            if (!(view === 'agentnews')) {
              _context7.n = 40;
              break;
            }
            _context7.n = 39;
            return loadAgentNews();
          case 39:
            _context7.n = 43;
            break;
          case 40:
            if (!(view === 'settings')) {
              _context7.n = 42;
              break;
            }
            _context7.n = 41;
            return loadSettings();
          case 41:
            _context7.n = 43;
            break;
          case 42:
            if (!(view === 'activity')) {
              _context7.n = 43;
              break;
            }
            _context7.n = 43;
            return loadActivity();
          case 43:
            _context7.n = 45;
            break;
          case 44:
            _context7.p = 44;
            _t5 = _context7.v;
            toast(_t5.message, true);
          case 45:
            return _context7.a(2);
        }
      }, _callee7, null, [[0, 44]]);
    }));
    return _loadView.apply(this, arguments);
  }
  function loadDashboard() {
    return _loadDashboard.apply(this, arguments);
  }
  function _loadDashboard() {
    _loadDashboard = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee8() {
      var state, setCounts, d, _val$total, _val, _val$total2, _val2, _val$total3, _val3, _val$total4, _val4, _val$total5, _val5, _val$total6, _val6, results, val, _t6;
      return _regenerator().w(function (_context8) {
        while (1) switch (_context8.p = _context8.n) {
          case 0:
            state = $('#dashboardRefreshState');
            if (state) state.textContent = 'Refreshing…';
            setCounts = function setCounts() {
              var _c$numbers, _c$agent, _c$manager, _c$client, _c$ranges, _c$otp_total, _c$otp_today, _c$sms_today, _c$sms_total, _c$pending_payments, _c$active_agent, _c$active_manager, _c$active_client;
              var c = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
              $('#sNumbers').textContent = (_c$numbers = c.numbers) !== null && _c$numbers !== void 0 ? _c$numbers : 0;
              $('#sAgents').textContent = (_c$agent = c.agent) !== null && _c$agent !== void 0 ? _c$agent : 0;
              $('#sManagers').textContent = (_c$manager = c.manager) !== null && _c$manager !== void 0 ? _c$manager : 0;
              $('#sClients').textContent = (_c$client = c.client) !== null && _c$client !== void 0 ? _c$client : 0;
              $('#sRanges').textContent = (_c$ranges = c.ranges) !== null && _c$ranges !== void 0 ? _c$ranges : 0;
              $('#sOtp').textContent = (_c$otp_total = c.otp_total) !== null && _c$otp_total !== void 0 ? _c$otp_total : 0;
              $('#sOtpToday').textContent = 'Today ' + ((_c$otp_today = c.otp_today) !== null && _c$otp_today !== void 0 ? _c$otp_today : 0);
              $('#sSmsToday').textContent = (_c$sms_today = c.sms_today) !== null && _c$sms_today !== void 0 ? _c$sms_today : 0;
              $('#sSmsTotal').textContent = 'Total ' + ((_c$sms_total = c.sms_total) !== null && _c$sms_total !== void 0 ? _c$sms_total : 0);
              $('#sPayments').textContent = (_c$pending_payments = c.pending_payments) !== null && _c$pending_payments !== void 0 ? _c$pending_payments : 0;
              if ($('#sAgentsMeta')) $('#sAgentsMeta').textContent = "".concat((_c$active_agent = c.active_agent) !== null && _c$active_agent !== void 0 ? _c$active_agent : 0, " active");
              if ($('#sManagersMeta')) $('#sManagersMeta').textContent = "".concat((_c$active_manager = c.active_manager) !== null && _c$active_manager !== void 0 ? _c$active_manager : 0, " active");
              if ($('#sClientsMeta')) $('#sClientsMeta').textContent = "".concat((_c$active_client = c.active_client) !== null && _c$active_client !== void 0 ? _c$active_client : 0, " active");
            };
            _context8.p = 1;
            _context8.n = 2;
            return req('summary');
          case 2:
            d = _context8.v;
            setCounts(d.counts || {});
            $('#topManagersBody').innerHTML = (d.top_managers || []).map(function (x) {
              return "<tr><td><b>".concat(esc(x.username), "</b></td><td>").concat(esc(x.agent_count), "</td><td>").concat(esc(x.range_count), "</td><td>").concat(esc(x.number_count), "</td><td>").concat(esc(x.sms_30d), "</td><td>").concat(badge(x.status), "</td></tr>");
            }).join('') || '<tr><td colspan="6" class="empty">No managers yet</td></tr>';
            $('#recentSms').innerHTML = (d.recent_sms || []).map(function (x) {
              return "<div class=\"event\"><div class=\"event-icon\">".concat(Number(x.otp_detected) ? '◉' : '✉', "</div><div><strong>").concat(esc(x.number), " \xB7 ").concat(esc(x.manager_name || '-'), "</strong><small>").concat(esc(x.agent_name || '-'), " / ").concat(esc(x.client_name || '-'), " \xB7 ").concat(Number(x.otp_detected) ? 'OTP event detected' : 'SMS event', "</small></div><span class=\"event-time\">").concat(dt(x.date_time), "</span></div>");
            }).join('') || '<div class="empty">No SMS events</div>';
            if (state) state.textContent = d.degraded ? 'Core totals loaded · optional stats need setup' : 'Live';
            _context8.n = 5;
            break;
          case 3:
            _context8.p = 3;
            _t6 = _context8.v;
            _context8.n = 4;
            return Promise.allSettled([req('users', {
              params: {
                role: 'manager',
                limit: 1
              }
            }), req('users', {
              params: {
                role: 'agent',
                limit: 1
              }
            }), req('users', {
              params: {
                role: 'client',
                limit: 1
              }
            }), req('numbers', {
              params: {
                limit: 1
              }
            }), req('ranges', {
              params: {
                limit: 1
              }
            }), req('payments', {
              params: {
                status: 'pending',
                limit: 1
              }
            })]);
          case 4:
            results = _context8.v;
            val = function val(i) {
              return results[i].status === 'fulfilled' ? results[i].value : null;
            };
            setCounts({
              manager: (_val$total = (_val = val(0)) === null || _val === void 0 ? void 0 : _val.total) !== null && _val$total !== void 0 ? _val$total : 0,
              agent: (_val$total2 = (_val2 = val(1)) === null || _val2 === void 0 ? void 0 : _val2.total) !== null && _val$total2 !== void 0 ? _val$total2 : 0,
              client: (_val$total3 = (_val3 = val(2)) === null || _val3 === void 0 ? void 0 : _val3.total) !== null && _val$total3 !== void 0 ? _val$total3 : 0,
              numbers: (_val$total4 = (_val4 = val(3)) === null || _val4 === void 0 ? void 0 : _val4.total) !== null && _val$total4 !== void 0 ? _val$total4 : 0,
              ranges: (_val$total5 = (_val5 = val(4)) === null || _val5 === void 0 ? void 0 : _val5.total) !== null && _val$total5 !== void 0 ? _val$total5 : 0,
              pending_payments: (_val$total6 = (_val6 = val(5)) === null || _val6 === void 0 ? void 0 : _val6.total) !== null && _val$total6 !== void 0 ? _val$total6 : 0,
              sms_total: 0,
              sms_today: 0,
              otp_total: 0,
              otp_today: 0
            });
            $('#topManagersBody').innerHTML = '<tr><td colspan="6" class="empty">Account totals loaded. Run setup.php to repair optional dashboard statistics.</td></tr>';
            $('#recentSms').innerHTML = '<div class="empty">SMS event feed temporarily unavailable</div>';
            if (state) state.textContent = 'Compatibility mode';
            toast('Account totals loaded; some optional dashboard statistics need database setup.', true);
          case 5:
            return _context8.a(2);
        }
      }, _callee8, null, [[1, 3]]);
    }));
    return _loadDashboard.apply(this, arguments);
  }
  function loadUsers(_x5) {
    return _loadUsers.apply(this, arguments);
  }
  function _loadUsers() {
    _loadUsers = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee9(role) {
      var _$2, _$3, _d$total;
      var m, search, status, d, body, totalEl;
      return _regenerator().w(function (_context9) {
        while (1) switch (_context9.n) {
          case 0:
            m = roleMeta[role], search = ((_$2 = $(m.search)) === null || _$2 === void 0 ? void 0 : _$2.value) || '', status = ((_$3 = $(m.status)) === null || _$3 === void 0 ? void 0 : _$3.value) || '';
            _context9.n = 1;
            return req('users', {
              params: {
                role: role,
                status: status,
                search: search,
                limit: 500
              }
            });
          case 1:
            d = _context9.v;
            body = $(m.body);
            body.innerHTML = (d.data || []).map(function (x) {
              return userRow(role, x);
            }).join('') || "<tr><td colspan=\"8\" class=\"empty\">No ".concat(esc(role), " accounts</td></tr>");
            totalEl = $('#' + role + 'Total');
            if (totalEl) totalEl.textContent = ((_d$total = d.total) !== null && _d$total !== void 0 ? _d$total : 0) + ' total';
            if (role === 'manager') fillManagerSelects(d.data || []);
            if (role === 'agent') {
              globalAgentRows = d.data || [];
              fillAgentSelect(globalAgentRows);
            }
          case 2:
            return _context9.a(2);
        }
      }, _callee9);
    }));
    return _loadUsers.apply(this, arguments);
  }
  var COUNTRY_NAMES = ["Afghanistan", "Albania", "Algeria", "American Samoa", "Andorra", "Angola", "Anguilla", "Antarctica", "Antigua and Barbuda", "Argentina", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia", "Bonaire, Sint Eustatius and Saba", "Bosnia and Herzegovina", "Botswana", "Bouvet Island", "Brazil", "British Indian Ocean Territory", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Cayman Islands", "Central African Republic", "Chad", "Chile", "China", "Christmas Island", "Cocos (Keeling) Islands", "Colombia", "Comoros", "Congo (DRC)", "Congo (Republic)", "Cook Islands", "Costa Rica", "Croatia", "Cuba", "Curaçao", "Cyprus", "Czechia", "Côte d’Ivoire", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Falkland Islands (Malvinas)", "Faroe Islands", "Fiji", "Finland", "France", "French Guiana", "French Polynesia", "French Southern Territories", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland", "Grenada", "Guadeloupe", "Guam", "Guatemala", "Guernsey", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Heard Island and McDonald Islands", "Holy See (Vatican City State)", "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Isle of Man", "Israel", "Italy", "Jamaica", "Japan", "Jersey", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Macao", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Martinique", "Mauritania", "Mauritius", "Mayotte", "Mexico", "Micronesia, Federated States of", "Moldova", "Monaco", "Mongolia", "Montenegro", "Montserrat", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Caledonia", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Niue", "Norfolk Island", "North Korea", "North Macedonia", "Northern Mariana Islands", "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Pitcairn", "Poland", "Portugal", "Puerto Rico", "Qatar", "Romania", "Russia", "Rwanda", "Réunion", "Saint Barthélemy", "Saint Helena, Ascension and Tristan da Cunha", "Saint Kitts and Nevis", "Saint Lucia", "Saint Martin (French part)", "Saint Pierre and Miquelon", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Sint Maarten (Dutch part)", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Georgia and the South Sandwich Islands", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Svalbard and Jan Mayen", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tokelau", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "United States Minor Outlying Islands", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Virgin Islands, British", "Virgin Islands, U.S.", "Wallis and Futuna", "Western Sahara", "Yemen", "Zambia", "Zimbabwe", "Åland Islands"];
  function populateCountrySelect() {
    var e = $('#countrySelect');
    if (!e) return;
    var keep = e.value;
    e.innerHTML = '<option value="">Select Country</option>' + COUNTRY_NAMES.map(function (c) {
      return "<option value=\"".concat(esc(c), "\">").concat(esc(c), "</option>");
    }).join('');
    if (keep && Array.from(e.options).some(function (o) {
      return o.value === keep;
    })) e.value = keep;
  }
  function userRow(role, x) {
    var contact = [x.email, x.phone, x.skype_id ? 'Skype: ' + x.skype_id : ''].filter(Boolean).map(esc).join('<br>') || '—',
      balances = esc(x.balances || '—'),
      parent = esc(x.parent_username || '—');
    var cells = '';
    var profileName = "".concat(esc(x.full_name || '—')).concat(x.company ? '<br><small>' + esc(x.company) + '</small>' : '').concat(x.country ? '<br><small>' + esc(x.country) + '</small>' : '');
    if (role === 'manager') cells = "<td><b>".concat(esc(x.username), "</b></td><td>").concat(profileName, "</td><td>").concat(contact, "</td><td>").concat(esc(x.child_count || 0), "</td><td>").concat(balances, "</td><td>").concat(badge(x.status), "</td><td>").concat(dt(x.last_login), "</td>");
    if (role === 'agent') cells = "<td><b>".concat(esc(x.username), "</b></td><td>").concat(profileName, "</td><td>").concat(parent, "</td><td>").concat(esc(x.child_count || 0), "</td><td>").concat(esc(x.direct_number_count || 0), "</td><td>").concat(badge(x.status), "</td><td>").concat(dt(x.last_login), "</td>");
    if (role === 'client') cells = "<td><b>".concat(esc(x.username), "</b></td><td>").concat(esc(x.full_name || '—'), "</td><td>").concat(parent, "</td><td>").concat(esc(x.direct_number_count || 0), "</td><td>").concat(balances, "</td><td>").concat(badge(x.status), "</td><td>").concat(dt(x.last_login), "</td>");
    if (role === 'test') cells = "<td><b>".concat(esc(x.username), "</b></td><td>").concat(esc(x.full_name || '—'), "</td><td>").concat(parent, "</td><td>").concat(contact, "</td><td><span class=\"count-pill\">test</span></td><td>").concat(badge(x.status), "</td><td>").concat(dt(x.last_login), "</td>");
    var next = x.status === 'active' ? 'suspended' : 'active';
    return "<tr>".concat(cells, "<td><div class=\"action-row\"><button class=\"mini-btn ").concat(next === 'active' ? 'ok' : 'warn', "\" data-user-status=\"").concat(x.id, "\" data-next=\"").concat(next, "\" data-role=\"").concat(role, "\">").concat(next === 'active' ? 'Activate' : 'Suspend', "</button><button class=\"mini-btn danger\" data-user-delete=\"").concat(x.id, "\" data-role=\"").concat(role, "\">Delete</button></div></td></tr>");
  }
  function fillManagerSelects(rows) {
    var opts = '<option value="">All managers</option>' + rows.filter(function (x) {
      return x.status === 'active';
    }).map(function (x) {
      return "<option value=\"".concat(x.id, "\">").concat(esc(x.username), "</option>");
    }).join('');
    ['#numberManager', '#reportManager'].forEach(function (s) {
      var e = $(s);
      if (!e) return;
      var keep = e.value;
      e.innerHTML = opts;
      if (keep && Array.from(e.options).some(function (o) {
        return o.value === String(keep);
      })) e.value = keep;
    });
  }
  function fillAgentSelect(rows) {
    var _$;
    var e = $('#reportAgent');
    if (!e) return;
    var keep = e.value,
      managerId = ((_$ = $('#reportManager')) === null || _$ === void 0 ? void 0 : _$.value) || '';
    var filtered = (rows || []).filter(function (x) {
      return x.status === 'active' && (!managerId || String(x.parent_id) === String(managerId));
    });
    e.innerHTML = '<option value="">All agents</option>' + filtered.map(function (x) {
      return "<option value=\"".concat(x.id, "\">").concat(esc(x.username), "</option>");
    }).join('');
    if (keep && Array.from(e.options).some(function (o) {
      return o.value === String(keep);
    })) e.value = keep;
  }
  function ensureParents(_x6) {
    return _ensureParents.apply(this, arguments);
  }
  function _ensureParents() {
    _ensureParents = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee0(role) {
      var wrap, sel, parentRole, d;
      return _regenerator().w(function (_context0) {
        while (1) switch (_context0.n) {
          case 0:
            wrap = $('#parentWrap'), sel = $('#parentSelect');
            if (!(role === 'manager' || role === 'test')) {
              _context0.n = 1;
              break;
            }
            wrap.style.display = 'none';
            sel.innerHTML = '';
            return _context0.a(2);
          case 1:
            wrap.style.display = 'grid';
            parentRole = role === 'agent' ? 'manager' : 'agent';
            _context0.n = 2;
            return req('users', {
              params: {
                role: parentRole,
                status: 'active',
                limit: 500
              }
            });
          case 2:
            d = _context0.v;
            wrap.firstChild.nodeValue = role === 'agent' ? 'Manager' : 'Agent';
            sel.innerHTML = '<option value="">Select ' + (role === 'agent' ? 'Manager' : 'Agent') + '</option>' + (d.data || []).map(function (x) {
              return "<option value=\"".concat(x.id, "\">").concat(esc(x.username)).concat(x.parent_username ? ' · ' + esc(x.parent_username) : '', "</option>");
            }).join('');
          case 3:
            return _context0.a(2);
        }
      }, _callee0);
    }));
    return _ensureParents.apply(this, arguments);
  }
  function openCreate(_x7) {
    return _openCreate.apply(this, arguments);
  }
  function _openCreate() {
    _openCreate = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee1(role) {
      return _regenerator().w(function (_context1) {
        while (1) switch (_context1.n) {
          case 0:
            $('#createUserForm').reset();
            populateCountrySelect();
            $('#createRole').value = role;
            $('#modalTitle').textContent = 'Create ' + role.charAt(0).toUpperCase() + role.slice(1);
            $('#modalHint').textContent = role === 'manager' ? 'Manager will be controlled from this Admin panel.' : role === 'agent' ? 'Choose the Manager that owns this Agent.' : role === 'client' ? 'Choose the Agent that owns this Client.' : 'Separate Test account controlled directly by Admin.';
            _context1.n = 1;
            return ensureParents(role);
          case 1:
            $('#userModal').hidden = false;
          case 2:
            return _context1.a(2);
        }
      }, _callee1);
    }));
    return _openCreate.apply(this, arguments);
  }
  function closeCreate() {
    $('#userModal').hidden = true;
  }
  function ensureRangeManagers() {
    return _ensureRangeManagers.apply(this, arguments);
  }
  function _ensureRangeManagers() {
    _ensureRangeManagers = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee10() {
      return _regenerator().w(function (_context10) {
        while (1) switch (_context10.n) {
          case 0:
            return _context10.a(2, true);
        }
      }, _callee10);
    }));
    return _ensureRangeManagers.apply(this, arguments);
  }
  function clearRangeForm() {
    var f = $('#rangeForm');
    if (!f) return;
    f.reset();
    $('#rangeId').value = '0';
    $('#rangeCurrency').value = 'USD';
    $('#rangeStatus').value = 'active';
    $('#rangeRequestEnabled').value = '1';
    $('#rangeMaxRequests').value = '';
    $('#rangeP11Enabled').checked = true;
    $('#rangeP71Enabled').checked = true;
    $('#rangeP77Enabled').checked = true;
    $('#rangeP3045Enabled').checked = true;
    $('#rangeFormTitle').textContent = 'Create Global SMS Range';
    $('#rangeNumbersFile').required = true;
  }
  function editRange(id) {
    var _x$request_enabled, _x$payout_1_, _x$payout_7_, _x$payout_7_2, _x$payout_30_, _x$payout_1_1_enabled, _x$payout_7_1_enabled, _x$payout_7_7_enabled, _x$payout_30_45_enabl;
    var x = rangeRows.find(function (v) {
      return Number(v.id) === Number(id);
    });
    if (!x) return;
    $('#rangeId').value = x.id;
    $('#rangeName').value = x.range_name || '';
    $('#rangePrefix').value = x.prefix || '';
    $('#rangeCurrency').value = x.currency || 'USD';
    $('#rangeStatus').value = x.status || 'active';
    $('#rangeRequestEnabled').value = String(Number((_x$request_enabled = x.request_enabled) !== null && _x$request_enabled !== void 0 ? _x$request_enabled : 1));
    $('#rangeMaxRequests').value = x.max_requests_per_agent === null || x.max_requests_per_agent === undefined || x.max_requests_per_agent === '' ? '' : x.max_requests_per_agent;
    $('#rangeMaxDaily').value = x.max_numbers_per_agent_daily === null || x.max_numbers_per_agent_daily === undefined || x.max_numbers_per_agent_daily === '' ? '' : x.max_numbers_per_agent_daily;
    $('#rangeTestNumber').value = x.test_number || '';
    $('#rangeP11').value = (_x$payout_1_ = x.payout_1_1) !== null && _x$payout_1_ !== void 0 ? _x$payout_1_ : '';
    $('#rangeP71').value = (_x$payout_7_ = x.payout_7_1) !== null && _x$payout_7_ !== void 0 ? _x$payout_7_ : '';
    $('#rangeP77').value = (_x$payout_7_2 = x.payout_7_7) !== null && _x$payout_7_2 !== void 0 ? _x$payout_7_2 : '';
    $('#rangeP3045').value = (_x$payout_30_ = x.payout_30_45) !== null && _x$payout_30_ !== void 0 ? _x$payout_30_ : '';
    $('#rangeP11Enabled').checked = Number((_x$payout_1_1_enabled = x.payout_1_1_enabled) !== null && _x$payout_1_1_enabled !== void 0 ? _x$payout_1_1_enabled : 1) === 1;
    $('#rangeP71Enabled').checked = Number((_x$payout_7_1_enabled = x.payout_7_1_enabled) !== null && _x$payout_7_1_enabled !== void 0 ? _x$payout_7_1_enabled : 1) === 1;
    $('#rangeP77Enabled').checked = Number((_x$payout_7_7_enabled = x.payout_7_7_enabled) !== null && _x$payout_7_7_enabled !== void 0 ? _x$payout_7_7_enabled : 1) === 1;
    $('#rangeP3045Enabled').checked = Number((_x$payout_30_45_enabl = x.payout_30_45_enabled) !== null && _x$payout_30_45_enabl !== void 0 ? _x$payout_30_45_enabl : 1) === 1;
    $('#rangeMemo').value = x.memo || '';
    $('#rangeNumbersFile').value = '';
    $('#rangeNumbersFile').required = false;
    $('#rangeFormTitle').textContent = 'Edit SMS Range';
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
  function loadRanges() {
    return _loadRanges.apply(this, arguments);
  }
  function _loadRanges() {
    _loadRanges = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee11() {
      var d, payoutCell;
      return _regenerator().w(function (_context11) {
        while (1) switch (_context11.n) {
          case 0:
            _context11.n = 1;
            return ensureRangeManagers();
          case 1:
            _context11.n = 2;
            return req('ranges', {
              params: {
                search: $('#rangeSearch').value || '',
                status: $('#rangeStatusFilter').value || '',
                limit: 400
              }
            });
          case 2:
            d = _context11.v;
            rangeRows = d.data || [];
            payoutCell = function payoutCell(val, enabledFlag) {
              if (val === null || val === '' || val === undefined) return '—';
              var off = Number(enabledFlag !== null && enabledFlag !== void 0 ? enabledFlag : 1) !== 1;
              return money(val) + (off ? ' ' + badge('off') : '');
            };
            $('#rangesBody').innerHTML = rangeRows.map(function (x) {
              var _ref3, _x$actual_total, _ref4, _x$actual_available, _x$request_enabled2;
              return "<tr><td><b>".concat(esc(x.range_name), "</b></td><td>").concat(esc(x.prefix), "</td><td>").concat(esc((_ref3 = (_x$actual_total = x.actual_total) !== null && _x$actual_total !== void 0 ? _x$actual_total : x.total_numbers) !== null && _ref3 !== void 0 ? _ref3 : 0), "</td><td>").concat(esc((_ref4 = (_x$actual_available = x.actual_available) !== null && _x$actual_available !== void 0 ? _x$actual_available : x.available_numbers) !== null && _ref4 !== void 0 ? _ref4 : 0), "</td><td>").concat(esc(x.test_number || '—'), "</td><td>").concat(esc(x.currency), "</td><td>").concat(payoutCell(x.payout_1_1, x.payout_1_1_enabled), "</td><td>").concat(payoutCell(x.payout_7_1, x.payout_7_1_enabled), "</td><td>").concat(payoutCell(x.payout_7_7, x.payout_7_7_enabled), "</td><td>").concat(payoutCell(x.payout_30_45, x.payout_30_45_enabled), "</td><td>").concat(Number((_x$request_enabled2 = x.request_enabled) !== null && _x$request_enabled2 !== void 0 ? _x$request_enabled2 : 1) ? badge('enabled') : badge('disabled'), "</td><td>").concat(x.max_requests_per_agent === null || x.max_requests_per_agent === undefined || Number(x.max_requests_per_agent) <= 0 ? 'Unlimited' : esc(x.max_requests_per_agent) + '/agent', "</td><td>").concat(badge(x.status), "</td><td><div class=\"action-row\"><button class=\"mini-btn\" data-range-edit=\"").concat(x.id, "\">Edit</button>").concat(Number(x.assigned_numbers || 0) > 0 ? "<button class=\"mini-btn warn\" data-range-return=\"".concat(x.id, "\">Return All</button>") : '', "<button class=\"mini-btn danger\" data-range-delete=\"").concat(x.id, "\" data-range-assigned=\"").concat(x.assigned_numbers || 0, "\">Delete</button></div></td></tr>");
            }).join('') || '<tr><td colspan="14" class="empty">No SMS ranges found</td></tr>';
            fillReturnRangeSelect(rangeRows);
          case 3:
            return _context11.a(2);
        }
      }, _callee11);
    }));
    return _loadRanges.apply(this, arguments);
  }
  function fillReturnRangeSelect(rows) {
    var e = $('#returnRangeSelect');
    if (!e) return;
    var keep = e.value;
    e.innerHTML = '<option value="">Select a range to return all its numbers…</option>' + (rows || []).map(function (x) {
      return "<option value=\"".concat(x.id, "\">").concat(esc(x.range_name), " \xB7 ").concat(esc(x.prefix), " (").concat(x.assigned_numbers || 0, " assigned)</option>");
    }).join('');
    if (keep && Array.from(e.options).some(function (o) {
      return o.value === String(keep);
    })) e.value = keep;
  }
  function returnRangeNumbers(_x8) {
    return _returnRangeNumbers.apply(this, arguments);
  }
  function _returnRangeNumbers() {
    _returnRangeNumbers = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee12(id) {
      var row, assigned, d;
      return _regenerator().w(function (_context12) {
        while (1) switch (_context12.n) {
          case 0:
            if (id) {
              _context12.n = 1;
              break;
            }
            toast('Select a range first', true);
            return _context12.a(2);
          case 1:
            row = (rangeRows || []).find(function (x) {
              return String(x.id) === String(id);
            });
            assigned = row ? Number(row.assigned_numbers || 0) : null;
            if (!(assigned === 0)) {
              _context12.n = 2;
              break;
            }
            toast('No assigned numbers in this range.', true);
            return _context12.a(2);
          case 2:
            if (confirm("Return all assigned numbers in \"".concat(row ? row.range_name : 'this range', "\" to the available pool? They will be removed from every Agent's/Manager's number list."))) {
              _context12.n = 3;
              break;
            }
            return _context12.a(2);
          case 3:
            _context12.n = 4;
            return req('range-return-numbers', {
              method: 'POST',
              body: {
                range_id: Number(id)
              }
            });
          case 4:
            d = _context12.v;
            toast(d.message || 'Numbers returned');
            _context12.n = 5;
            return Promise.all([loadRanges(), loadNumbers().catch(function () {}), loadDashboard()]);
          case 5:
            return _context12.a(2);
        }
      }, _callee12);
    }));
    return _returnRangeNumbers.apply(this, arguments);
  }
  function saveRange() {
    return _saveRange.apply(this, arguments);
  }
  function _saveRange() {
    _saveRange = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee13() {
      var _$$files;
      var f, fd, id, file, d;
      return _regenerator().w(function (_context13) {
        while (1) switch (_context13.n) {
          case 0:
            f = $('#rangeForm'), fd = new FormData(f), id = Number($('#rangeId').value || 0), file = (_$$files = $('#rangeNumbersFile').files) === null || _$$files === void 0 ? void 0 : _$$files[0];
            if (!(!id && !file)) {
              _context13.n = 1;
              break;
            }
            throw new Error('Upload a TXT or CSV numbers file for a new range');
          case 1:
            // Checkboxes are omitted from FormData when unchecked, so set each toggle explicitly.
            fd.set('payout_1_1_enabled', $('#rangeP11Enabled').checked ? '1' : '0');
            fd.set('payout_7_1_enabled', $('#rangeP71Enabled').checked ? '1' : '0');
            fd.set('payout_7_7_enabled', $('#rangeP77Enabled').checked ? '1' : '0');
            fd.set('payout_30_45_enabled', $('#rangeP3045Enabled').checked ? '1' : '0');
            fd.set('max_requests_per_agent', ($('#rangeMaxRequests').value || '').replace(/[^0-9]/g, ''));
            fd.set('max_numbers_per_agent_daily', ($('#rangeMaxDaily').value || '').replace(/[^0-9]/g, ''));
            _context13.n = 2;
            return reqForm('range-save', fd);
          case 2:
            d = _context13.v;
            toast("".concat(d.message || 'Range saved').concat(Number(d.inserted || 0) ? ' · ' + d.inserted + ' number(s) imported' : '').concat(Number(d.duplicates || 0) ? ' · ' + d.duplicates + ' duplicate(s) skipped' : ''));
            clearRangeForm();
            _context13.n = 3;
            return Promise.all([loadRanges(), loadDashboard()]);
          case 3:
            return _context13.a(2);
        }
      }, _callee13);
    }));
    return _saveRange.apply(this, arguments);
  }
  function deleteRange(_x9, _x0) {
    return _deleteRange.apply(this, arguments);
  }
  function _deleteRange() {
    _deleteRange = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee14(id, assigned) {
      var d;
      return _regenerator().w(function (_context14) {
        while (1) switch (_context14.n) {
          case 0:
            if (!(Number(assigned) > 0)) {
              _context14.n = 1;
              break;
            }
            toast('Unassign all numbers from this range before deleting it.', true);
            return _context14.a(2);
          case 1:
            if (confirm('Delete this SMS range and its unassigned number inventory?')) {
              _context14.n = 2;
              break;
            }
            return _context14.a(2);
          case 2:
            _context14.n = 3;
            return req('range-delete', {
              method: 'POST',
              body: {
                id: Number(id)
              }
            });
          case 3:
            d = _context14.v;
            toast(d.message || 'Range deleted');
            if (Number($('#rangeId').value) === Number(id)) clearRangeForm();
            _context14.n = 4;
            return Promise.all([loadRanges(), loadDashboard()]);
          case 4:
            return _context14.a(2);
        }
      }, _callee14);
    }));
    return _deleteRange.apply(this, arguments);
  }
  function loadNumbers() {
    return _loadNumbers.apply(this, arguments);
  }
  function _loadNumbers() {
    _loadNumbers = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee15() {
      var d;
      return _regenerator().w(function (_context15) {
        while (1) switch (_context15.n) {
          case 0:
            _context15.n = 1;
            return ensureGlobalDropdowns();
          case 1:
            _context15.n = 2;
            return req('numbers', {
              params: {
                search: $('#numberSearch').value || '',
                manager_id: $('#numberManager').value || '',
                status: $('#numberStatus').value || '',
                limit: 300
              }
            });
          case 2:
            d = _context15.v;
            $('#numbersTotal').textContent = (d.total || 0) + ' records';
            $('#numbersBody').innerHTML = (d.data || []).map(function (x) {
              return "<tr><td><b>".concat(esc(x.number), "</b>").concat(Number(x.is_test) ? ' ' + badge('test') : '', "</td><td>").concat(esc(x.range_name), "</td><td>").concat(esc(x.prefix), "</td><td>").concat(esc(x.manager_name || '—'), "</td><td>").concat(esc(x.assigned_username || '—'), "</td><td>").concat(esc(x.assigned_role || '—'), "</td><td>").concat(esc(x.pay_term || '—'), "</td><td>").concat(money(x.payout_rate), " ").concat(esc(x.currency), "</td><td>").concat(badge(x.status), "</td><td>").concat(x.status === 'assigned' ? "<button class=\"mini-btn warn\" data-number-unassign=\"".concat(x.id, "\">Unassign</button>") : '—', "</td></tr>");
            }).join('') || '<tr><td colspan="10" class="empty">No numbers found</td></tr>';
          case 3:
            return _context15.a(2);
        }
      }, _callee15);
    }));
    return _loadNumbers.apply(this, arguments);
  }
  function unassignNumber(_x1) {
    return _unassignNumber.apply(this, arguments);
  }
  function _unassignNumber() {
    _unassignNumber = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee16(id) {
      var d;
      return _regenerator().w(function (_context16) {
        while (1) switch (_context16.n) {
          case 0:
            if (confirm('Return this number to the available pool? It will be removed from the agent\'s account.')) {
              _context16.n = 1;
              break;
            }
            return _context16.a(2);
          case 1:
            _context16.n = 2;
            return req('number-unassign', {
              method: 'POST',
              body: {
                id: id
              }
            });
          case 2:
            d = _context16.v;
            toast(d.message);
            _context16.n = 3;
            return Promise.all([loadNumbers(), loadDashboard()]);
          case 3:
            return _context16.a(2);
        }
      }, _callee16);
    }));
    return _unassignNumber.apply(this, arguments);
  }
  function ensureGlobalDropdowns() {
    return _ensureGlobalDropdowns.apply(this, arguments);
  }
  function _ensureGlobalDropdowns() {
    _ensureGlobalDropdowns = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee17() {
      var _yield$Promise$all, _yield$Promise$all2, m, a;
      return _regenerator().w(function (_context17) {
        while (1) switch (_context17.n) {
          case 0:
            _context17.n = 1;
            return Promise.all([req('users', {
              params: {
                role: 'manager',
                status: 'active',
                limit: 500
              }
            }), req('users', {
              params: {
                role: 'agent',
                status: 'active',
                limit: 500
              }
            })]);
          case 1:
            _yield$Promise$all = _context17.v;
            _yield$Promise$all2 = _slicedToArray(_yield$Promise$all, 2);
            m = _yield$Promise$all2[0];
            a = _yield$Promise$all2[1];
            globalAgentRows = a.data || [];
            fillManagerSelects(m.data || []);
            fillAgentSelect(globalAgentRows);
          case 2:
            return _context17.a(2);
        }
      }, _callee17);
    }));
    return _ensureGlobalDropdowns.apply(this, arguments);
  }
  function localToSql(v) {
    var end = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : false;
    if (!v) return '';
    var s = v.replace('T', ' ');
    return s.length === 16 ? s + ':' + (end ? '59' : '00') : s;
  }
  function loadReports() {
    return _loadReports.apply(this, arguments);
  }
  function _loadReports() {
    _loadReports = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee18() {
      var _d$summary$sms, _d$summary, _d$summary$otp, _d$summary2, _d$summary3;
      var d;
      return _regenerator().w(function (_context18) {
        while (1) switch (_context18.n) {
          case 0:
            _context18.n = 1;
            return ensureGlobalDropdowns();
          case 1:
            _context18.n = 2;
            return req('reports', {
              params: {
                search: $('#reportSearch').value || '',
                from: localToSql($('#reportFrom').value),
                to: localToSql($('#reportTo').value, true),
                manager_id: $('#reportManager').value || '',
                agent_id: $('#reportAgent').value || '',
                otp_only: $('#reportOtpOnly').checked ? 1 : 0,
                limit: 300
              }
            });
          case 2:
            d = _context18.v;
            $('#rSms').textContent = (_d$summary$sms = (_d$summary = d.summary) === null || _d$summary === void 0 ? void 0 : _d$summary.sms) !== null && _d$summary$sms !== void 0 ? _d$summary$sms : 0;
            $('#rOtp').textContent = (_d$summary$otp = (_d$summary2 = d.summary) === null || _d$summary2 === void 0 ? void 0 : _d$summary2.otp) !== null && _d$summary$otp !== void 0 ? _d$summary$otp : 0;
            $('#rProfit').textContent = money(((_d$summary3 = d.summary) === null || _d$summary3 === void 0 ? void 0 : _d$summary3.profit) || 0);
            $('#reportsBody').innerHTML = (d.data || []).map(function (x) {
              return "<tr><td>".concat(dt(x.date_time), "</td><td>").concat(esc(x.manager_name || '—'), "</td><td>").concat(esc(x.agent_name || '—'), "</td><td>").concat(esc(x.client_name || '—'), "</td><td>").concat(esc(x.range_name || '—'), "</td><td><b>").concat(esc(x.number), "</b></td><td>").concat(esc(x.cli || '—'), "</td><td>").concat(esc(x.sms_count), "</td><td>").concat(Number(x.otp_detected) ? badge('OTP') : '—', "</td><td>").concat(esc(x.currency), "</td><td>").concat(badge(x.smpp_status || 'delivered'), "</td></tr>");
            }).join('') || '<tr><td colspan="11" class="empty">No report rows</td></tr>';
          case 3:
            return _context18.a(2);
        }
      }, _callee18);
    }));
    return _loadReports.apply(this, arguments);
  }
  function loadPayments() {
    return _loadPayments.apply(this, arguments);
  }
  function _loadPayments() {
    _loadPayments = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee19() {
      var d;
      return _regenerator().w(function (_context19) {
        while (1) switch (_context19.n) {
          case 0:
            _context19.n = 1;
            return req('payments', {
              params: {
                status: $('#paymentStatus').value || '',
                limit: 300
              }
            });
          case 1:
            d = _context19.v;
            $('#paymentsTotal').textContent = (d.total || 0) + ' records';
            $('#paymentsBody').innerHTML = (d.data || []).map(function (x) {
              return "<tr><td>".concat(dt(x.created_at), "</td><td><b>").concat(esc(x.username), "</b></td><td>").concat(esc(x.role), "</td><td>").concat(esc(x.parent_username || '—'), "</td><td>").concat(money(x.amount), " ").concat(esc(x.currency), "</td><td>").concat(esc(x.method || '—'), "</td><td>").concat(badge(x.status), "</td><td><div class=\"action-row\">").concat(x.status === 'pending' ? "<button class=\"mini-btn ok\" data-payment=\"".concat(x.id, "\" data-pay-status=\"approved\">Approve</button><button class=\"mini-btn danger\" data-payment=\"").concat(x.id, "\" data-pay-status=\"rejected\">Reject</button>") : '').concat(x.status === 'approved' ? "<button class=\"mini-btn ok\" data-payment=\"".concat(x.id, "\" data-pay-status=\"completed\">Complete</button>") : '', "</div></td></tr>");
            }).join('') || '<tr><td colspan="8" class="empty">No payment requests</td></tr>';
          case 2:
            return _context19.a(2);
        }
      }, _callee19);
    }));
    return _loadPayments.apply(this, arguments);
  }
  function smppStatusText(x) {
    return String(x || 'unknown').replace(/_/g, ' ');
  }
  function smppTableEmpty(cols) {
    var msg = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'No data';
    return "<tr><td colspan=\"".concat(cols, "\" class=\"empty\">").concat(esc(msg), "</td></tr>");
  }
  function loadSmppControl() {
    return _loadSmppControl.apply(this, arguments);
  }
  function _loadSmppControl() {
    _loadSmppControl = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee20() {
      var _d$stats$daily, _d$stats, _d$stats$hourly, _d$stats2;
      var d, a;
      return _regenerator().w(function (_context20) {
        while (1) switch (_context20.n) {
          case 0:
            _context20.n = 1;
            return req('smpp-control');
          case 1:
            d = _context20.v;
            $('#smppJasminStatus').textContent = d.jasmin_running ? 'Running' : 'Stopped / Unknown';
            $('#smppJasminMeta').textContent = d.jasmin_running ? 'Gateway process detected' : 'Process not detected';
            a = d.active_config || null;
            $('#smppActiveName').textContent = (a === null || a === void 0 ? void 0 : a.config_name) || 'None';
            $('#smppConfigStatus').textContent = (a === null || a === void 0 ? void 0 : a.status) || 'No active configuration';
            $('#smpp24h').textContent = (_d$stats$daily = (_d$stats = d.stats) === null || _d$stats === void 0 ? void 0 : _d$stats.daily) !== null && _d$stats$daily !== void 0 ? _d$stats$daily : 0;
            $('#smpp1h').textContent = (_d$stats$hourly = (_d$stats2 = d.stats) === null || _d$stats2 === void 0 ? void 0 : _d$stats2.hourly) !== null && _d$stats$hourly !== void 0 ? _d$stats$hourly : 0;
            $('#smppEndpoint').textContent = a ? "".concat(a.inbound_host, ":").concat(a.inbound_port) : '—';
            $('#smppCallback').textContent = location.origin + '/api/smpp.php?action=receive';
            if (a) editSmpp(a.id);else clearSmppForm();
          case 2:
            return _context20.a(2);
        }
      }, _callee20);
    }));
    return _loadSmppControl.apply(this, arguments);
  }
  function loadSmppAccounts() {
    return _loadSmppAccounts.apply(this, arguments);
  }
  function _loadSmppAccounts() {
    _loadSmppAccounts = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee21() {
      var d, rows;
      return _regenerator().w(function (_context21) {
        while (1) switch (_context21.n) {
          case 0:
            _context21.n = 1;
            return req('smpp-accounts');
          case 1:
            d = _context21.v;
            rows = d.accounts || [];
            $('#smppAccountTotal').textContent = rows.length + ' total';
            $('#smppAccountsBody').innerHTML = rows.map(function (x) {
              return "<tr>\n    <td><b>".concat(esc(x.username), "</b></td><td>").concat(esc(x.supplier_name || '—'), "</td>\n    <td>").concat(badge(x.bind_type), "</td><td>").concat(esc(x.max_connections), "</td>\n    <td>").concat(esc(x.allowed_ranges || '*'), "</td><td>").concat(badge(x.status), "</td>\n    <td>").concat(dt(x.last_connected_at), "</td>\n    <td><button class=\"mini-btn\" data-smpp-account-edit=\"").concat(x.id, "\">Edit</button></td>\n  </tr>");
            }).join('') || smppTableEmpty(8);
            window._smppAccounts = rows;
          case 2:
            return _context21.a(2);
        }
      }, _callee21);
    }));
    return _loadSmppAccounts.apply(this, arguments);
  }
  function editSmppAccount(id) {
    var x = (window._smppAccounts || []).find(function (v) {
      return Number(v.id) === Number(id);
    });
    if (!x) return;
    var f = $('#smppAccountForm');
    f.elements.id.value = x.id;
    f.elements.username.value = x.username || '';
    f.elements.supplier_name.value = x.supplier_name || '';
    f.elements.supplier_contact.value = x.supplier_contact || '';
    f.elements.bind_type.value = x.bind_type || 'TR';
    f.elements.max_connections.value = x.max_connections || 10;
    f.elements.status.value = x.status || 'active';
    f.elements.allowed_ranges.value = x.allowed_ranges || '';
    f.elements.password_hash.value = '';
  }
  function clearSmppAccountForm() {
    var f = $('#smppAccountForm');
    if (!f) return;
    f.reset();
    f.elements.id.value = '0';
    f.elements.max_connections.value = '10';
    f.elements.bind_type.value = 'TR';
    f.elements.status.value = 'active';
  }
  function saveSmppAccount() {
    return _saveSmppAccount.apply(this, arguments);
  }
  function _saveSmppAccount() {
    _saveSmppAccount = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee22() {
      var f, body, d;
      return _regenerator().w(function (_context22) {
        while (1) switch (_context22.n) {
          case 0:
            f = $('#smppAccountForm'), body = {};
            Array.from(f.elements).forEach(function (e) {
              if (e.name) body[e.name] = e.value;
            });
            _context22.n = 1;
            return req('smpp-account-save', {
              method: 'POST',
              body: body
            });
          case 1:
            d = _context22.v;
            toast(d.message || 'SMPP account saved', 'success');
            clearSmppAccountForm();
            _context22.n = 2;
            return loadSmppAccounts();
          case 2:
            return _context22.a(2);
        }
      }, _callee22);
    }));
    return _saveSmppAccount.apply(this, arguments);
  }
  function loadSmppSessions() {
    return _loadSmppSessions.apply(this, arguments);
  }
  function _loadSmppSessions() {
    _loadSmppSessions = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee23() {
      var d, rows;
      return _regenerator().w(function (_context23) {
        while (1) switch (_context23.n) {
          case 0:
            _context23.n = 1;
            return req('smpp-sessions');
          case 1:
            d = _context23.v;
            rows = d.sessions || [];
            $('#smppSessionsBody').innerHTML = rows.map(function (x) {
              return "<tr><td class=\"monospace\">".concat(esc(x.username || x.system_id || '—'), "</td><td>").concat(esc(x.ip || '—'), "</td><td>").concat(badge(x.bind_type || 'TR'), "</td><td>").concat(esc(x.messages || 0), "</td><td>").concat(dt(x.last_connected_at), "</td><td>").concat(badge(x.status || 'unknown'), "</td></tr>");
            }).join('') || smppTableEmpty(6, 'No live session telemetry is available.');
          case 2:
            return _context23.a(2);
        }
      }, _callee23);
    }));
    return _loadSmppSessions.apply(this, arguments);
  }
  function loadSmppClients() {
    return _loadSmppClients.apply(this, arguments);
  }
  function _loadSmppClients() {
    _loadSmppClients = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee24() {
      var d, rows;
      return _regenerator().w(function (_context24) {
        while (1) switch (_context24.n) {
          case 0:
            _context24.n = 1;
            return req('smpp-sessions');
          case 1:
            d = _context24.v;
            rows = d.sessions || [];
            $('#smppClientsBody').innerHTML = rows.map(function (x) {
              return "<tr><td><b>".concat(esc(x.username || '—'), "</b></td><td>").concat(esc(x.supplier_name || '—'), "</td><td>").concat(badge(x.bind_type || 'TR'), "</td><td>").concat(dt(x.last_connected_at), "</td><td>").concat(badge(x.status || 'unknown'), "</td></tr>");
            }).join('') || smppTableEmpty(5, 'No connected-client telemetry is available.');
          case 2:
            return _context24.a(2);
        }
      }, _callee24);
    }));
    return _loadSmppClients.apply(this, arguments);
  }
  function loadSmppDlr() {
    return _loadSmppDlr.apply(this, arguments);
  }
  function _loadSmppDlr() {
    _loadSmppDlr = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee25() {
      var d;
      return _regenerator().w(function (_context25) {
        while (1) switch (_context25.n) {
          case 0:
            _context25.n = 1;
            return req('smpp-dlr');
          case 1:
            d = _context25.v;
            $('#dlrDelivered').textContent = d.delivered || 0;
            $('#dlrPending').textContent = d.pending || 0;
            $('#dlrFailed').textContent = d.failed || 0;
            $('#dlrRate').textContent = (d.dlr_rate || 0) + '%';
            $('#dlrBody').innerHTML = (d.rows || []).map(function (x) {
              return "<tr><td class=\"monospace\">".concat(esc(x.message_id), "</td><td>").concat(esc(x.source_addr), "</td><td>").concat(esc(x.destination_addr), "</td><td>").concat(badge(x.message_status), "</td><td>").concat(dt(x.submit_date), "</td><td>").concat(esc(x.connector_id || '—'), "</td></tr>");
            }).join('') || smppTableEmpty(6);
          case 2:
            return _context25.a(2);
        }
      }, _callee25);
    }));
    return _loadSmppDlr.apply(this, arguments);
  }
  function loadSmppThroughput() {
    return _loadSmppThroughput.apply(this, arguments);
  }
  function _loadSmppThroughput() {
    _loadSmppThroughput = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee26() {
      var d;
      return _regenerator().w(function (_context26) {
        while (1) switch (_context26.n) {
          case 0:
            _context26.n = 1;
            return req('smpp-throughput');
          case 1:
            d = _context26.v;
            $('#tpCurrent').textContent = d.current_mps || 0;
            $('#tpPeak').textContent = d.peak_mps || 0;
            $('#tpTotal').textContent = d.total_24h || 0;
            $('#tpBody').innerHTML = (d.rows || []).map(function (x) {
              return "<tr><td>".concat(dt(x.minute), "</td><td>").concat(esc(x.messages), "</td><td>").concat(esc(x.mps), "</td></tr>");
            }).join('') || smppTableEmpty(3);
          case 2:
            return _context26.a(2);
        }
      }, _callee26);
    }));
    return _loadSmppThroughput.apply(this, arguments);
  }
  function loadSmppSecurity() {
    return _loadSmppSecurity.apply(this, arguments);
  }
  function _loadSmppSecurity() {
    _loadSmppSecurity = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee27() {
      var d;
      return _regenerator().w(function (_context27) {
        while (1) switch (_context27.n) {
          case 0:
            _context27.n = 1;
            return req('smpp-security');
          case 1:
            d = _context27.v;
            $('#smppSecurityBody').innerHTML = (d.events || []).map(function (x) {
              return "<tr><td>".concat(dt(x.time), "</td><td>").concat(esc(x.event), "</td><td>").concat(esc(x.details), "</td></tr>");
            }).join('') || smppTableEmpty(3);
          case 2:
            return _context27.a(2);
        }
      }, _callee27);
    }));
    return _loadSmppSecurity.apply(this, arguments);
  }
  function loadSmppLogs() {
    return _loadSmppLogs.apply(this, arguments);
  }
  function _loadSmppLogs() {
    _loadSmppLogs = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee28() {
      var d;
      return _regenerator().w(function (_context28) {
        while (1) switch (_context28.n) {
          case 0:
            _context28.n = 1;
            return req('smpp-logs');
          case 1:
            d = _context28.v;
            $('#smppLogsBody').innerHTML = (d.rows || []).map(function (x) {
              return "<tr><td>".concat(dt(x.time), "</td><td>").concat(esc(x.event), "</td><td>").concat(esc(x.account || '—'), "</td><td>").concat(esc(x.ip || '—'), "</td><td>").concat(badge(x.status || 'info'), "</td></tr>");
            }).join('') || smppTableEmpty(5);
          case 2:
            return _context28.a(2);
        }
      }, _callee28);
    }));
    return _loadSmppLogs.apply(this, arguments);
  }
  function clearSmppForm() {
    var f = $('#smppForm');
    f.reset();
    $('#smppId').value = '0';
    $('#smppPort').value = '2775';
    $('#smppHost').value = '0.0.0.0';
    $('#smppStatus').value = 'active';
    $('#smppPassword').required = true;
  }
  function editSmpp(id) {
    var x = smppProfiles.find(function (v) {
      return Number(v.id) === Number(id);
    });
    if (!x) return;
    $('#smppId').value = x.id;
    $('#smppConfigName').value = x.config_name || '';
    $('#smppHost').value = x.inbound_host || '0.0.0.0';
    $('#smppPort').value = x.inbound_port || 2775;
    $('#smppSystemId').value = x.inbound_system_id || '';
    $('#smppStatus').value = x.status || 'inactive';
    $('#smppPassword').value = '';
    $('#smppPassword').required = false;
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
  function loadSmpp() {
    return _loadSmpp.apply(this, arguments);
  }
  function _loadSmpp() {
    _loadSmpp = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee29() {
      var _d$connection_info, _d$stats$daily2, _d$stats3, _active$total_receive;
      var callbackUrl, d, active;
      return _regenerator().w(function (_context29) {
        while (1) switch (_context29.n) {
          case 0:
            callbackUrl = location.origin + '/api/smpp.php?action=receive';
            $('#smppWebhookUrl').textContent = callbackUrl;
            $('#jasminPanelUrl').textContent = location.origin;
            $('#jasminCallbackUrl').textContent = callbackUrl;
            _context29.n = 1;
            return req('smpp-config');
          case 1:
            d = _context29.v;
            $('#jasminApiPort').textContent = ((_d$connection_info = d.connection_info) === null || _d$connection_info === void 0 ? void 0 : _d$connection_info.api_port) || '1401';
            if (d.installed) {
              _context29.n = 2;
              break;
            }
            smppProfiles = [];
            $('#smppJasmin').textContent = 'Not Ready';
            $('#smppActiveConfig').textContent = 'Migration Required';
            $('#smppDaily').textContent = '0';
            $('#smppTotal').textContent = '0';
            $('#smppConfigCount').textContent = '0 profiles';
            $('#smppConfigsBody').innerHTML = '<tr><td colspan="8" class="empty">Run database/migrations/admin_smpp_news_upgrade.sql first.</td></tr>';
            return _context29.a(2);
          case 2:
            smppProfiles = d.configs || [];
            active = d.active_config || null;
            $('#smppJasmin').textContent = d.jasmin_running ? 'Running' : 'Stopped / Unknown';
            $('#smppActiveConfig').textContent = (active === null || active === void 0 ? void 0 : active.config_name) || 'None';
            $('#smppDaily').textContent = (_d$stats$daily2 = (_d$stats3 = d.stats) === null || _d$stats3 === void 0 ? void 0 : _d$stats3.daily) !== null && _d$stats$daily2 !== void 0 ? _d$stats$daily2 : 0;
            $('#smppTotal').textContent = (_active$total_receive = active === null || active === void 0 ? void 0 : active.total_received) !== null && _active$total_receive !== void 0 ? _active$total_receive : 0;
            $('#smppConfigCount').textContent = smppProfiles.length + ' profiles';
            $('#smppConfigsBody').innerHTML = smppProfiles.map(function (x) {
              return "<tr><td><b>".concat(esc(x.config_name), "</b></td><td>").concat(esc(x.inbound_host), "</td><td>").concat(esc(x.inbound_port), "</td><td>").concat(esc(x.inbound_system_id), "</td><td>").concat(badge(x.status), "</td><td>").concat(esc(x.total_received || 0), "</td><td>").concat(dt(x.last_received_at), "</td><td><button class=\"mini-btn\" data-smpp-edit=\"").concat(x.id, "\">Edit</button></td></tr>");
            }).join('') || '<tr><td colspan="8" class="empty">No SMPP profile configured</td></tr>';
            if (Number($('#smppId').value || 0) === 0) {
              if (active) editSmpp(active.id);else if (smppProfiles.length) editSmpp(smppProfiles[0].id);
            }
          case 3:
            return _context29.a(2);
        }
      }, _callee29);
    }));
    return _loadSmpp.apply(this, arguments);
  }
  function saveSmpp() {
    return _saveSmpp.apply(this, arguments);
  }
  function _saveSmpp() {
    _saveSmpp = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee30() {
      var f, body, d;
      return _regenerator().w(function (_context30) {
        while (1) switch (_context30.n) {
          case 0:
            f = $('#smppForm'), body = {
              id: Number(f.elements.id.value || 0),
              config_name: f.elements.config_name.value,
              inbound_host: f.elements.inbound_host.value,
              inbound_port: Number(f.elements.inbound_port.value || 0),
              inbound_system_id: f.elements.inbound_system_id.value,
              inbound_password: f.elements.inbound_password.value,
              status: f.elements.status.value
            };
            _context30.n = 1;
            return req('smpp-config', {
              method: 'POST',
              body: body
            });
          case 1:
            d = _context30.v;
            toast(d.message || 'SMPP config saved');
            $('#smppPassword').value = '';
            $('#smppPassword').required = false;
            _context30.n = 2;
            return loadSmpp();
          case 2:
            return _context30.a(2);
        }
      }, _callee30);
    }));
    return _saveSmpp.apply(this, arguments);
  }
  function integrationDefaults(type) {
    if (type === 'http') return {
      provider_name: '',
      status: 'active',
      url: '',
      method: 'POST',
      api_key: '',
      sender_id: '',
      timeout: '15',
      notes: ''
    };
    if (type === 'api') return {
      status: 'active',
      version: 'v1',
      base_url: location.origin + '/api',
      rate_limit: '60',
      scopes: 'numbers,sms,users,stats'
    };
    return {
      url: '',
      method: 'POST',
      secret: '',
      timeout: '10',
      retries: '3',
      events: 'otp_received,number_allocated,user_created'
    };
  }
  function fillIntegrationForm(type, data) {
    var f = $(type === 'http' ? '#httpProviderForm' : type === 'api' ? '#apiConfigForm' : '#webhookForm');
    if (!f) return;
    var d = Object.assign(integrationDefaults(type), data || {});
    Object.keys(d).forEach(function (k) {
      var _d$k;
      if (f.elements[k]) f.elements[k].value = (_d$k = d[k]) !== null && _d$k !== void 0 ? _d$k : '';
    });
  }
  function loadIntegrationSettings(_x10) {
    return _loadIntegrationSettings.apply(this, arguments);
  }
  function _loadIntegrationSettings() {
    _loadIntegrationSettings = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee31(type) {
      var d;
      return _regenerator().w(function (_context31) {
        while (1) switch (_context31.n) {
          case 0:
            _context31.n = 1;
            return req('integration-settings', {
              params: {
                type: type
              }
            });
          case 1:
            d = _context31.v;
            fillIntegrationForm(type, d.config || {});
            if (type === 'api' && $('#apiTokenOutput')) $('#apiTokenOutput').textContent = 'No new token generated.';
          case 2:
            return _context31.a(2);
        }
      }, _callee31);
    }));
    return _loadIntegrationSettings.apply(this, arguments);
  }
  function saveIntegrationSettings(_x11) {
    return _saveIntegrationSettings.apply(this, arguments);
  }
  function _saveIntegrationSettings() {
    _saveIntegrationSettings = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee32(type) {
      var f, body, d;
      return _regenerator().w(function (_context32) {
        while (1) switch (_context32.n) {
          case 0:
            f = $(type === 'http' ? '#httpProviderForm' : type === 'api' ? '#apiConfigForm' : '#webhookForm');
            body = {
              type: type,
              config: {}
            };
            Array.from(f.elements).forEach(function (e) {
              if (e.name) body.config[e.name] = e.value;
            });
            _context32.n = 1;
            return req('integration-settings', {
              method: 'POST',
              body: body
            });
          case 1:
            d = _context32.v;
            toast(d.message || 'Configuration saved');
            _context32.n = 2;
            return loadIntegrationSettings(type);
          case 2:
            return _context32.a(2);
        }
      }, _callee32);
    }));
    return _saveIntegrationSettings.apply(this, arguments);
  }
  function generateApiToken() {
    return _generateApiToken.apply(this, arguments);
  }
  function _generateApiToken() {
    _generateApiToken = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee33() {
      var d;
      return _regenerator().w(function (_context33) {
        while (1) switch (_context33.n) {
          case 0:
            _context33.n = 1;
            return req('integration-token', {
              method: 'POST',
              body: {
                name: 'Admin API Token'
              }
            });
          case 1:
            d = _context33.v;
            if ($('#apiTokenOutput')) $('#apiTokenOutput').textContent = d.token || 'Token generated.';
            toast('API token generated');
          case 2:
            return _context33.a(2);
        }
      }, _callee33);
    }));
    return _generateApiToken.apply(this, arguments);
  }
  function testWebhookConfig() {
    return _testWebhookConfig.apply(this, arguments);
  }
  function _testWebhookConfig() {
    _testWebhookConfig = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee34() {
      var _f$elements;
      var f, url;
      return _regenerator().w(function (_context34) {
        while (1) switch (_context34.n) {
          case 0:
            f = $('#webhookForm');
            url = (f === null || f === void 0 || (_f$elements = f.elements) === null || _f$elements === void 0 || (_f$elements = _f$elements.url) === null || _f$elements === void 0 ? void 0 : _f$elements.value) || '';
            if (/^https?:\/\//i.test(url)) {
              _context34.n = 1;
              break;
            }
            toast('Enter a valid HTTP/HTTPS webhook URL', true);
            return _context34.a(2);
          case 1:
            toast('Webhook configuration saved. Test delivery should be performed from the connected server.');
          case 2:
            return _context34.a(2);
        }
      }, _callee34);
    }));
    return _testWebhookConfig.apply(this, arguments);
  }
  function runApiPlayground() {
    return _runApiPlayground.apply(this, arguments);
  }
  function _runApiPlayground() {
    _runApiPlayground = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee35() {
      var f, out, path, body, opts, r, text, _t7, _t8;
      return _regenerator().w(function (_context35) {
        while (1) switch (_context35.p = _context35.n) {
          case 0:
            f = $('#apiPlaygroundForm'), out = $('#apiPlaygroundOutput');
            if (!(!f || !out)) {
              _context35.n = 1;
              break;
            }
            return _context35.a(2);
          case 1:
            path = f.elements.path.value.trim();
            if (!path.startsWith('/')) path = '/' + path;
            if (/^\/api\//.test(path)) {
              _context35.n = 2;
              break;
            }
            out.textContent = 'Blocked: endpoint must be under /api/';
            return _context35.a(2);
          case 2:
            body = f.elements.body.value.trim();
            opts = {
              method: f.elements.method.value,
              credentials: 'include',
              headers: {
                'Accept': 'application/json'
              }
            };
            if (!(body && opts.method !== 'GET')) {
              _context35.n = 5;
              break;
            }
            _context35.p = 3;
            JSON.parse(body);
            opts.headers['Content-Type'] = 'application/json';
            opts.body = body;
            _context35.n = 5;
            break;
          case 4:
            _context35.p = 4;
            _t7 = _context35.v;
            out.textContent = 'Invalid JSON request body.';
            return _context35.a(2);
          case 5:
            out.textContent = 'Running…';
            _context35.p = 6;
            _context35.n = 7;
            return fetch(path, opts);
          case 7:
            r = _context35.v;
            _context35.n = 8;
            return r.text();
          case 8:
            text = _context35.v;
            out.textContent = "HTTP ".concat(r.status, "\n\n").concat(text);
            _context35.n = 10;
            break;
          case 9:
            _context35.p = 9;
            _t8 = _context35.v;
            out.textContent = 'Request failed: ' + _t8.message;
          case 10:
            return _context35.a(2);
        }
      }, _callee35, null, [[6, 9], [3, 4]]);
    }));
    return _runApiPlayground.apply(this, arguments);
  }
  function clearAgentNewsForm() {
    var f = $('#agentNewsForm');
    f.reset();
    $('#agentNewsId').value = '0';
    $('#agentNewsStatus').value = 'published';
    $('#agentNewsFormTitle').textContent = 'Create Agent News';
  }
  function editAgentNews(id) {
    var x = agentNewsRows.find(function (v) {
      return Number(v.id) === Number(id);
    });
    if (!x) return;
    $('#agentNewsId').value = x.id;
    $('#agentNewsTitle').value = x.title || '';
    $('#agentNewsContent').value = x.content || '';
    $('#agentNewsStatus').value = x.status || 'draft';
    $('#agentNewsFormTitle').textContent = 'Edit Agent News';
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
  function loadAgentNews() {
    return _loadAgentNews.apply(this, arguments);
  }
  function _loadAgentNews() {
    _loadAgentNews = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee36() {
      var d;
      return _regenerator().w(function (_context36) {
        while (1) switch (_context36.n) {
          case 0:
            _context36.n = 1;
            return req('agent-news', {
              params: {
                search: $('#agentNewsSearch').value || '',
                status: $('#agentNewsFilterStatus').value || '',
                limit: 300
              }
            });
          case 1:
            d = _context36.v;
            agentNewsRows = d.data || [];
            $('#agentNewsBody').innerHTML = agentNewsRows.map(function (x) {
              return "<tr><td>".concat(dt(x.published_at || x.created_at), "</td><td><b>").concat(esc(x.title), "</b></td><td class=\"wrap-cell news-preview\">").concat(esc((x.content || '').slice(0, 150)), "</td><td>").concat(esc(x.author_name || '—'), " <small>").concat(esc(x.author_role || ''), "</small></td><td>").concat(badge(x.status), "</td><td><div class=\"action-row\"><button class=\"mini-btn\" data-agent-news-edit=\"").concat(x.id, "\">Edit</button><button class=\"mini-btn danger\" data-agent-news-delete=\"").concat(x.id, "\">Delete</button></div></td></tr>");
            }).join('') || '<tr><td colspan="6" class="empty">No Agent news found</td></tr>';
          case 2:
            return _context36.a(2);
        }
      }, _callee36);
    }));
    return _loadAgentNews.apply(this, arguments);
  }
  function saveAgentNews() {
    return _saveAgentNews.apply(this, arguments);
  }
  function _saveAgentNews() {
    _saveAgentNews = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee37() {
      var f, body, d;
      return _regenerator().w(function (_context37) {
        while (1) switch (_context37.n) {
          case 0:
            f = $('#agentNewsForm'), body = {
              id: Number(f.elements.id.value || 0),
              title: f.elements.title.value,
              content: f.elements.content.value,
              status: f.elements.status.value
            };
            _context37.n = 1;
            return req('agent-news-save', {
              method: 'POST',
              body: body
            });
          case 1:
            d = _context37.v;
            toast(d.message || 'News saved');
            clearAgentNewsForm();
            _context37.n = 2;
            return loadAgentNews();
          case 2:
            return _context37.a(2);
        }
      }, _callee37);
    }));
    return _saveAgentNews.apply(this, arguments);
  }
  function deleteAgentNews(_x12) {
    return _deleteAgentNews.apply(this, arguments);
  }
  function _deleteAgentNews() {
    _deleteAgentNews = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee38(id) {
      var d;
      return _regenerator().w(function (_context38) {
        while (1) switch (_context38.n) {
          case 0:
            if (confirm('Delete this Agent news?')) {
              _context38.n = 1;
              break;
            }
            return _context38.a(2);
          case 1:
            _context38.n = 2;
            return req('agent-news-delete', {
              method: 'POST',
              body: {
                id: Number(id)
              }
            });
          case 2:
            d = _context38.v;
            toast(d.message || 'News deleted');
            if (Number($('#agentNewsId').value) === Number(id)) clearAgentNewsForm();
            _context38.n = 3;
            return loadAgentNews();
          case 3:
            return _context38.a(2);
        }
      }, _callee38);
    }));
    return _deleteAgentNews.apply(this, arguments);
  }
  function loadSettings() {
    return _loadSettings.apply(this, arguments);
  }
  function _loadSettings() {
    _loadSettings = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee39() {
      var d, f;
      return _regenerator().w(function (_context39) {
        while (1) switch (_context39.n) {
          case 0:
            _context39.n = 1;
            return req('settings');
          case 1:
            d = _context39.v;
            f = $('#settingsForm');
            Object.entries(d.settings || {}).forEach(function (_ref5) {
              var _o$value;
              var _ref6 = _slicedToArray(_ref5, 2),
                k = _ref6[0],
                o = _ref6[1];
              var e = f.elements[k];
              if (!e) return;
              if (e.type === 'checkbox') e.checked = String(o.value) === '1';else e.value = (_o$value = o.value) !== null && _o$value !== void 0 ? _o$value : '';
            });
          case 2:
            return _context39.a(2);
        }
      }, _callee39);
    }));
    return _loadSettings.apply(this, arguments);
  }
  function saveSettings() {
    return _saveSettings.apply(this, arguments);
  }
  function _saveSettings() {
    _saveSettings = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee40() {
      var f, body, d;
      return _regenerator().w(function (_context40) {
        while (1) switch (_context40.n) {
          case 0:
            f = $('#settingsForm'), body = {};
            ['site_name', 'minimum_withdrawal_usd', 'minimum_withdrawal_eur', 'minimum_withdrawal_gbp', 'default_page_size', 'support_note'].forEach(function (k) {
              return body[k] = f.elements[k].value;
            });
            body.payment_requests_enabled = f.elements.payment_requests_enabled.checked ? 1 : 0;
            body.maintenance_mode = f.elements.maintenance_mode.checked ? 1 : 0;
            _context40.n = 1;
            return req('settings', {
              method: 'POST',
              body: body
            });
          case 1:
            d = _context40.v;
            toast(d.message || 'Settings saved');
          case 2:
            return _context40.a(2);
        }
      }, _callee40);
    }));
    return _saveSettings.apply(this, arguments);
  }
  function loadActivity() {
    return _loadActivity.apply(this, arguments);
  }
  function _loadActivity() {
    _loadActivity = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee41() {
      var d;
      return _regenerator().w(function (_context41) {
        while (1) switch (_context41.n) {
          case 0:
            _context41.n = 1;
            return req('activity', {
              params: {
                limit: 200
              }
            });
          case 1:
            d = _context41.v;
            $('#activityBody').innerHTML = (d.data || []).map(function (x) {
              return "<tr><td>".concat(dt(x.created_at), "</td><td>").concat(esc(x.username || 'system'), "</td><td>").concat(esc(x.role || '—'), "</td><td>").concat(esc(x.action), "</td><td class=\"wrap-cell\">").concat(esc(x.description || '—'), "</td><td>").concat(esc(x.ip_address || '—'), "</td></tr>");
            }).join('') || '<tr><td colspan="6" class="empty">No activity</td></tr>';
          case 2:
            return _context41.a(2);
        }
      }, _callee41);
    }));
    return _loadActivity.apply(this, arguments);
  }
  function userStatus(_x13, _x14, _x15) {
    return _userStatus.apply(this, arguments);
  }
  function _userStatus() {
    _userStatus = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee42(id, status, role) {
      var d;
      return _regenerator().w(function (_context42) {
        while (1) switch (_context42.n) {
          case 0:
            if (confirm("Set this ".concat(role, " to ").concat(status, "?"))) {
              _context42.n = 1;
              break;
            }
            return _context42.a(2);
          case 1:
            _context42.n = 2;
            return req('user-status', {
              method: 'POST',
              body: {
                id: id,
                status: status
              }
            });
          case 2:
            d = _context42.v;
            toast(d.message);
            _context42.n = 3;
            return Promise.all([loadUsers(role), loadDashboard()]);
          case 3:
            return _context42.a(2);
        }
      }, _callee42);
    }));
    return _userStatus.apply(this, arguments);
  }
  function userDelete(_x16, _x17) {
    return _userDelete.apply(this, arguments);
  }
  function _userDelete() {
    _userDelete = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee43(id, role) {
      var d;
      return _regenerator().w(function (_context43) {
        while (1) switch (_context43.n) {
          case 0:
            if (confirm("Delete this ".concat(role, "? Accounts with children/ranges/numbers cannot be deleted."))) {
              _context43.n = 1;
              break;
            }
            return _context43.a(2);
          case 1:
            _context43.n = 2;
            return req('user-delete', {
              method: 'POST',
              body: {
                id: id
              }
            });
          case 2:
            d = _context43.v;
            toast(d.message);
            _context43.n = 3;
            return Promise.all([loadUsers(role), loadDashboard()]);
          case 3:
            return _context43.a(2);
        }
      }, _callee43);
    }));
    return _userDelete.apply(this, arguments);
  }
  function paymentStatus(_x18, _x19) {
    return _paymentStatus.apply(this, arguments);
  }
  function _paymentStatus() {
    _paymentStatus = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee44(id, status) {
      var d;
      return _regenerator().w(function (_context44) {
        while (1) switch (_context44.n) {
          case 0:
            if (confirm("Set payment request to ".concat(status, "?"))) {
              _context44.n = 1;
              break;
            }
            return _context44.a(2);
          case 1:
            _context44.n = 2;
            return req('payment-status', {
              method: 'POST',
              body: {
                id: id,
                status: status
              }
            });
          case 2:
            d = _context44.v;
            toast(d.message);
            _context44.n = 3;
            return Promise.all([loadPayments(), loadDashboard()]);
          case 3:
            return _context44.a(2);
        }
      }, _callee44);
    }));
    return _paymentStatus.apply(this, arguments);
  }
  function bind() {
    $$('#mainNav .nav-item').forEach(function (b) {
      return b.addEventListener('click', function () {
        return show(b.dataset.view);
      });
    });
    $('#menuBtn').addEventListener('click', function () {
      return $('#sidebar').classList.toggle('open');
    });
    $('#logoutBtn').addEventListener('click', function () {
      return location.href = '/ints/logout';
    });
    if ($('#refreshDashboardBtn')) $('#refreshDashboardBtn').addEventListener('click', function () {
      return loadDashboard().catch(function (e) {
        return toast(e.message, true);
      });
    });
    if ($('#reportManager')) $('#reportManager').addEventListener('change', function () {
      return fillAgentSelect(globalAgentRows);
    });
    $$('[data-jump]').forEach(function (b) {
      return b.addEventListener('click', function () {
        return show(b.dataset.jump);
      });
    });
    $$('[data-create-role]').forEach(function (b) {
      return b.addEventListener('click', function () {
        return openCreate(b.dataset.createRole).catch(function (e) {
          return toast(e.message, true);
        });
      });
    });
    $('#closeModalBtn').onclick = $('#cancelModalBtn').onclick = closeCreate;
    $('#userModal').addEventListener('click', function (e) {
      if (e.target === $('#userModal')) closeCreate();
    });
    $$('[data-load-users]').forEach(function (b) {
      return b.addEventListener('click', function () {
        return loadUsers(b.dataset.loadUsers).catch(function (e) {
          return toast(e.message, true);
        });
      });
    });
    $('#rangeSearchBtn').onclick = function () {
      return loadRanges().catch(function (e) {
        return toast(e.message, true);
      });
    };
    $('#newRangeBtn').onclick = function () {
      clearRangeForm();
      $('#rangeName').focus();
    };
    $('#clearRangeBtn').onclick = clearRangeForm;
    $('#dbUpgradeBtn').onclick = /*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
      var btn, orig, d, _t;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.p = _context.n) {
          case 0:
            btn = $('#dbUpgradeBtn');
            btn.disabled = true;
            orig = btn.textContent;
            btn.textContent = 'Upgrading…';
            _context.p = 1;
            _context.n = 2;
            return req('db-upgrade', {
              method: 'POST',
              body: {}
            });
          case 2:
            d = _context.v;
            toast(d.message || 'Database upgraded');
            _context.n = 4;
            break;
          case 3:
            _context.p = 3;
            _t = _context.v;
            toast(_t.message, true);
          case 4:
            _context.p = 4;
            btn.disabled = false;
            btn.textContent = orig;
            return _context.f(4);
          case 5:
            return _context.a(2);
        }
      }, _callee, null, [[1, 3, 4, 5]]);
    }));
    $('#rangeForm').addEventListener('submit', function (e) {
      e.preventDefault();
      saveRange().catch(function (x) {
        return toast(x.message, true);
      });
    });
    $('#numberSearchBtn').onclick = function () {
      return loadNumbers().catch(function (e) {
        return toast(e.message, true);
      });
    };
    $('#reportSearchBtn').onclick = function () {
      return loadReports().catch(function (e) {
        return toast(e.message, true);
      });
    };
    $('#paymentSearchBtn').onclick = function () {
      return loadPayments().catch(function (e) {
        return toast(e.message, true);
      });
    };
    if ($('#httpProviderForm')) $('#httpProviderForm').addEventListener('submit', function (e) {
      e.preventDefault();
      saveIntegrationSettings('http').catch(function (x) {
        return toast(x.message, true);
      });
    });
    if ($('#apiConfigForm')) $('#apiConfigForm').addEventListener('submit', function (e) {
      e.preventDefault();
      saveIntegrationSettings('api').catch(function (x) {
        return toast(x.message, true);
      });
    });
    if ($('#webhookForm')) $('#webhookForm').addEventListener('submit', function (e) {
      e.preventDefault();
      saveIntegrationSettings('webhook').catch(function (x) {
        return toast(x.message, true);
      });
    });
    if ($('#generateApiTokenBtn')) $('#generateApiTokenBtn').onclick = function () {
      return generateApiToken().catch(function (e) {
        return toast(e.message, true);
      });
    };
    if ($('#testWebhookBtn')) $('#testWebhookBtn').onclick = function () {
      return testWebhookConfig().catch(function (e) {
        return toast(e.message, true);
      });
    };
    if ($('#apiPlaygroundForm')) $('#apiPlaygroundForm').addEventListener('submit', function (e) {
      e.preventDefault();
      runApiPlayground().catch(function (x) {
        return toast(x.message, true);
      });
    });
    if ($('#testSmsForm')) $('#testSmsForm').addEventListener('submit', function (e) {
      e.preventDefault();
      var out = $('#testSmsOutput');
      var number = $('#testSmsNumber').value.trim();
      var source = $('#testSmsSource').value.trim();
      var message = $('#testSmsMessage').value.trim();
      if (!number || !message) {
        return toast('Number and message are required', true);
      }
      out.textContent = 'Sending…';
      req('test-sms-send', {
        method: 'POST',
        body: { number: number, source: source, message: message }
      }).then(function (data) {
        out.textContent = JSON.stringify(data, null, 2);
        toast(data.message || 'Test SMS sent');
      }).catch(function (e2) {
        out.textContent = 'Error: ' + e2.message;
        toast(e2.message, true);
      });
    });
    $('#newAgentNewsBtn').onclick = function () {
      clearAgentNewsForm();
      $('#agentNewsTitle').focus();
    };
    $('#cancelAgentNewsEditBtn').onclick = clearAgentNewsForm;
    $('#agentNewsSearchBtn').onclick = function () {
      return loadAgentNews().catch(function (e) {
        return toast(e.message, true);
      });
    };
    $('#agentNewsForm').addEventListener('submit', function (e) {
      e.preventDefault();
      saveAgentNews().catch(function (x) {
        return toast(x.message, true);
      });
    });
    $('#saveSettingsBtn').onclick = function () {
      return saveSettings().catch(function (e) {
        return toast(e.message, true);
      });
    };
    $('#refreshActivityBtn').onclick = function () {
      return loadActivity().catch(function (e) {
        return toast(e.message, true);
      });
    };
    $('#createUserForm').addEventListener('submit', /*#__PURE__*/function () {
      var _ref2 = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2(e) {
        var body, d, _t2;
        return _regenerator().w(function (_context2) {
          while (1) switch (_context2.p = _context2.n) {
            case 0:
              e.preventDefault();
              body = Object.fromEntries(new FormData(e.currentTarget).entries());
              _context2.p = 1;
              _context2.n = 2;
              return req('user-create', {
                method: 'POST',
                body: body
              });
            case 2:
              d = _context2.v;
              toast(d.message);
              closeCreate();
              show(body.role + 's');
              _context2.n = 4;
              break;
            case 3:
              _context2.p = 3;
              _t2 = _context2.v;
              toast(_t2.message, true);
            case 4:
              return _context2.a(2);
          }
        }, _callee2, null, [[1, 3]]);
      }));
      return function (_x20) {
        return _ref2.apply(this, arguments);
      };
    }());
    document.addEventListener('click', function (e) {
      var s = e.target.closest('[data-user-status]');
      if (s) userStatus(s.dataset.userStatus, s.dataset.next, s.dataset.role).catch(function (x) {
        return toast(x.message, true);
      });
      var d = e.target.closest('[data-user-delete]');
      if (d) userDelete(d.dataset.userDelete, d.dataset.role).catch(function (x) {
        return toast(x.message, true);
      });
      var p = e.target.closest('[data-payment]');
      if (p) paymentStatus(p.dataset.payment, p.dataset.payStatus).catch(function (x) {
        return toast(x.message, true);
      });
      var se = e.target.closest('[data-smpp-edit]');
      if (se) editSmpp(se.dataset.smppEdit);
      var sae = e.target.closest('[data-smpp-account-edit]');
      if (sae) editSmppAccount(sae.dataset.smppAccountEdit);
      var ne = e.target.closest('[data-agent-news-edit]');
      if (ne) editAgentNews(ne.dataset.agentNewsEdit);
      var nd = e.target.closest('[data-agent-news-delete]');
      if (nd) deleteAgentNews(nd.dataset.agentNewsDelete).catch(function (x) {
        return toast(x.message, true);
      });
      var re = e.target.closest('[data-range-edit]');
      if (re) editRange(re.dataset.rangeEdit);
      var rd = e.target.closest('[data-range-delete]');
      if (rd) deleteRange(rd.dataset.rangeDelete, rd.dataset.rangeAssigned).catch(function (x) {
        return toast(x.message, true);
      });
      var nu = e.target.closest('[data-number-unassign]');
      if (nu) unassignNumber(nu.dataset.numberUnassign).catch(function (x) {
        return toast(x.message, true);
      });
      var rr = e.target.closest('[data-range-return]');
      if (rr) returnRangeNumbers(rr.dataset.rangeReturn).catch(function (x) {
        return toast(x.message, true);
      });
    });
    $('#returnRangeBtn').onclick = function () {
      return returnRangeNumbers($('#returnRangeSelect').value).catch(function (e) {
        return toast(e.message, true);
      });
    };
    var sf = $('#smppForm');
    if (sf) sf.onsubmit = function (e) {
      e.preventDefault();
      saveSmpp().catch(function (x) {
        return toast(x.message, true);
      });
    };
    var saf = $('#smppAccountForm');
    if (saf) saf.onsubmit = function (e) {
      e.preventDefault();
      saveSmppAccount().catch(function (x) {
        return toast(x.message, true);
      });
    };
    var nsa = $('#newSmppAccountBtn');
    if (nsa) nsa.onclick = clearSmppAccountForm;
    var csa = $('#clearSmppAccountBtn');
    if (csa) csa.onclick = clearSmppAccountForm;
    ['smppRefreshBtn', 'smppSessionsRefreshBtn', 'dlrRefreshBtn', 'throughputRefreshBtn', 'smppLogsRefreshBtn'].forEach(function (id) {
      var b = $('#' + id);
      if (b) b.onclick = function () {
        return loadView(location.hash.replace('#', '') || 'smpp-dashboard').catch(function (x) {
          return toast(x.message, true);
        });
      };
    });
  }
  (function () {
    var _init = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee3() {
      var h;
      return _regenerator().w(function (_context3) {
        while (1) switch (_context3.n) {
          case 0:
            bind();
            clearRangeForm();
            _context3.n = 1;
            return verifySession();
          case 1:
            if (_context3.v) {
              _context3.n = 2;
              break;
            }
            return _context3.a(2);
          case 2:
            h = location.hash.replace('#', '');
            show(titles[h] ? h : 'dashboard');
          case 3:
            return _context3.a(2);
        }
      }, _callee3);
    }));
    function init() {
      return _init.apply(this, arguments);
    }
    return init;
  })()();
})();