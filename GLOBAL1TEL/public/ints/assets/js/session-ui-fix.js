function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i.return) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); } r ? i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n : (o("next", 0), o("throw", 1), o("return", 2)); }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
(function () {
  'use strict';

  function roleFromPath() {
    var p = window.location.pathname.toLowerCase();
    if (p.indexOf('/ints/manager/') !== -1) return 'manager';
    if (p.indexOf('/ints/agent/') !== -1) return 'agent';
    if (p.indexOf('/ints/client/') !== -1) return 'client';
    if (p.indexOf('/ints/test/') !== -1) return 'test';
    return '';
  }
  function dashboardFor(role) {
    if (role === 'admin') return '/ints/admin/AdminDashboard.html';
    if (role === 'manager') return '/ints/manager/SMSDashboard.html';
    if (role === 'agent') return '/ints/agent/SMSDashboard.html';
    if (role === 'client') return '/ints/client/SMSDashboard.html';
    if (role === 'test') return '/ints/test/SMSDashboard.html';
    return '/ints/login';
  }
  function setNavUsername(username) {
    var existing = document.getElementById('nav-username');
    if (existing) {
      existing.textContent = username;
      return;
    }
    var link = document.querySelector('.top-nav .nav.pull-right a.dropdown-toggle');
    if (!link) return;
    var span = document.createElement('span');
    span.id = 'nav-username';
    span.textContent = username;

    // Remove only the old leading username text; preserve notification/user icons.
    for (var i = 0; i < link.childNodes.length; i++) {
      var n = link.childNodes[i];
      if (n.nodeType === Node.TEXT_NODE && n.nodeValue.trim()) {
        n.nodeValue = ' ';
        break;
      }
    }
    link.insertBefore(span, link.firstChild);
    link.insertBefore(document.createTextNode(' '), span.nextSibling);
  }
  function setSidebarUsername(username) {
    var existing = document.getElementById('sidebar-username');
    if (existing) {
      existing.textContent = username;
      return;
    }
    var box = document.querySelector('#sidebar .lgxx');
    if (!box) return;
    var walker = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
    var node;
    while (node = walker.nextNode()) {
      if (/\bWelcome\s+\S+/i.test(node.nodeValue)) {
        node.nodeValue = node.nodeValue.replace(/\bWelcome\s+\S+/i, 'Welcome ' + username);
        break;
      }
    }
  }
  function updateSidebarClock() {
    var box = document.querySelector('#sidebar .lgxx');
    if (!box) return;
    var text = new Date().toLocaleString();
    var existing = document.getElementById('sidebar-datetime');
    if (existing) {
      existing.textContent = text;
      return;
    }
    var walker = document.createTreeWalker(box, NodeFilter.SHOW_TEXT);
    var node;
    while (node = walker.nextNode()) {
      if (/\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}/.test(node.nodeValue)) {
        node.nodeValue = node.nodeValue.replace(/\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}/, text);
        return;
      }
    }
  }
  function cleanLegacyAgentOptions() {
    document.querySelectorAll('select option').forEach(function (opt) {
      if (/^ShaziPero$/i.test(opt.textContent.trim())) opt.remove();
    });
  }
  function populateLegacySelect(_x, _x2) {
    return _populateLegacySelect.apply(this, arguments);
  }
  function _populateLegacySelect() {
    _populateLegacySelect = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee(select, endpoint) {
      var response, data, _t;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.p = _context.n) {
          case 0:
            if (!(!select || select.dataset.g1tPopulated === '1')) {
              _context.n = 1;
              break;
            }
            return _context.a(2);
          case 1:
            select.dataset.g1tPopulated = '1';
            _context.p = 2;
            _context.n = 3;
            return fetch(endpoint + '?q=&max=100&page=1', {
              credentials: 'include',
              cache: 'no-store'
            });
          case 3:
            response = _context.v;
            if (response.ok) {
              _context.n = 4;
              break;
            }
            return _context.a(2);
          case 4:
            _context.n = 5;
            return response.json();
          case 5:
            data = _context.v;
            (data.results || []).forEach(function (item) {
              if (select.querySelector('option[value="' + String(item.id).replace(/"/g, '\\"') + '"]')) return;
              var opt = document.createElement('option');
              opt.value = item.id;
              opt.textContent = item.title || item.text || item.username || item.id;
              select.appendChild(opt);
            });
            _context.n = 7;
            break;
          case 6:
            _context.p = 6;
            _t = _context.v;
            console.error('GLOBAL1TEL dropdown load error:', _t);
          case 7:
            return _context.a(2);
        }
      }, _callee, null, [[2, 6]]);
    }));
    return _populateLegacySelect.apply(this, arguments);
  }
  function populateLegacyFilters() {
    cleanLegacyAgentOptions();
    var role = roleFromPath();
    document.querySelectorAll('select[name="fagent"]').forEach(function (s) {
      populateLegacySelect(s, 'res/aj_agents.php');
    });
    document.querySelectorAll('select[name="fclient"]').forEach(function (s) {
      populateLegacySelect(s, 'res/aj_clients.php');
    });
    document.querySelectorAll('select[name="frange"], select#drange').forEach(function (s) {
      populateLegacySelect(s, 'res/aj_smsranges.php');
    });
    document.querySelectorAll('select#xclient').forEach(function (s) {
      populateLegacySelect(s, role === 'manager' ? 'res/aj_agents.php' : 'res/aj_clients.php');
    });
  }
  function populateProfilePage() {
    return _populateProfilePage.apply(this, arguments);
  }
  function _populateProfilePage() {
    _populateProfilePage = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee2() {
      var response, data, profile, values, _t2;
      return _regenerator().w(function (_context2) {
        while (1) switch (_context2.p = _context2.n) {
          case 0:
            if (/\/Profile(?:\.html)?$/i.test(window.location.pathname)) {
              _context2.n = 1;
              break;
            }
            return _context2.a(2);
          case 1:
            _context2.p = 1;
            _context2.n = 2;
            return fetch('/api/profile.php?action=get', {
              credentials: 'include',
              cache: 'no-store'
            });
          case 2:
            response = _context2.v;
            if (response.ok) {
              _context2.n = 3;
              break;
            }
            return _context2.a(2);
          case 3:
            _context2.n = 4;
            return response.json();
          case 4:
            data = _context2.v;
            profile = data.profile || {};
            values = {
              name: profile.full_name || '',
              email: profile.email || '',
              contact: profile.phone || '',
              company: profile.company || '',
              address: profile.address || ''
            };
            Object.keys(values).forEach(function (name) {
              var el = document.querySelector('form input[name="' + name + '"], form textarea[name="' + name + '"]');
              if (el) el.value = values[name];
            });
            _context2.n = 6;
            break;
          case 5:
            _context2.p = 5;
            _t2 = _context2.v;
            console.error('GLOBAL1TEL profile load error:', _t2);
          case 6:
            return _context2.a(2);
        }
      }, _callee2, null, [[1, 5]]);
    }));
    return _populateProfilePage.apply(this, arguments);
  }
  function pad2(n) {
    return String(n).padStart(2, '0');
  }
  function fmtDate(d, withTime, endOfDay) {
    var base = d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate());
    if (!withTime) return base;
    return base + (endOfDay ? ' 23:59:59' : ' 00:00:00');
  }
  function refreshLegacyDateDefaults() {
    var now = new Date();
    var start = new Date(now.getTime());
    start.setDate(start.getDate() - 30);
    document.querySelectorAll('input[name="fdate1"], input[name="fdate2"]').forEach(function (el) {
      var old = String(el.value || '');
      if (!/^2026-(04|05)-/.test(old)) return;
      var withTime = /\d{2}:\d{2}:\d{2}/.test(old);
      if (el.name === 'fdate1') el.value = fmtDate(start, withTime, false);
      if (el.name === 'fdate2') el.value = fmtDate(now, withTime, true);
    });
  }
  function enableLegacyFilters() {
    document.addEventListener('submit', function (event) {
      var form = event.target;
      if (!form || form.id !== 'fform' || !window.jQuery || !jQuery.fn.dataTable) return;
      var tableEl = jQuery('#dt');
      if (!tableEl.length || !jQuery.fn.dataTable.isDataTable(tableEl[0])) return;
      event.preventDefault();
      var table = tableEl.dataTable();
      var settings = table.fnSettings();
      if (!settings || !settings.sAjaxSource) return;
      var current = settings.sAjaxSource;
      var base = current.split('?')[0];
      var keep = [];
      var match = current.match(/[?&](view=[^&]+)/);
      if (match) keep.push(match[1]);
      var params = jQuery(form).serialize();
      settings.sAjaxSource = base + '?' + [params].concat(keep).filter(Boolean).join('&');
      table.fnDraw();
    }, true);
  }
  function getCachedUsername() {
    try {
      return window.localStorage && localStorage.getItem('global1tel_username') || '';
    } catch (e) {
      return '';
    }
  }
  function cacheUsername(username) {
    try {
      if (window.localStorage && username) localStorage.setItem('global1tel_username', username);
    } catch (e) {}
  }
  function loadSession() {
    return _loadSession.apply(this, arguments);
  }
  function _loadSession() {
    _loadSession = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee3() {
      var cachedUsername, response, data, user, expected, actual, usdBalance, usd, panelUrl, callbackUrl, configPanelUrl, configPanelPort, _t3;
      return _regenerator().w(function (_context3) {
        while (1) switch (_context3.p = _context3.n) {
          case 0:
            // Use the last known username immediately so there is no Loading flash.
            cachedUsername = getCachedUsername();
            if (cachedUsername) {
              setNavUsername(cachedUsername);
              setSidebarUsername(cachedUsername);
            }
            _context3.p = 1;
            _context3.n = 2;
            return fetch('/api/session.php', {
              credentials: 'include',
              cache: 'no-store'
            });
          case 2:
            response = _context3.v;
            if (response.ok) {
              _context3.n = 3;
              break;
            }
            window.location.replace('/ints/login');
            return _context3.a(2);
          case 3:
            _context3.n = 4;
            return response.json();
          case 4:
            data = _context3.v;
            if (!(!data.authenticated && !data.logged_in)) {
              _context3.n = 5;
              break;
            }
            window.location.replace('/ints/login');
            return _context3.a(2);
          case 5:
            user = data.user || data;
            if (!(!user || !user.username)) {
              _context3.n = 6;
              break;
            }
            window.location.replace('/ints/login');
            return _context3.a(2);
          case 6:
            expected = roleFromPath();
            actual = String(user.role || '').toLowerCase();
            if (
              (expected === 'test' && (actual === 'test' || actual === 'client' || actual === 'manager' || actual === 'admin')) ||
              (expected === 'client' && (actual === 'client' || actual === 'test')) ||
              !(expected && actual && expected !== actual)
            ) {
              _context3.n = 7;
              break;
            }
            window.location.replace(dashboardFor(actual));
            return _context3.a(2);
          case 7:
            cacheUsername(user.username);
            setNavUsername(user.username);
            setSidebarUsername(user.username);
            updateSidebarClock();
            usdBalance = document.getElementById('usd-balance');
            if (usdBalance && user.balances) {
              usd = Number(user.balances.USD || 0);
              usdBalance.textContent = usd.toFixed(3);
            }
            panelUrl = document.getElementById('panelurl');
            callbackUrl = document.getElementById('callbackurl');
            configPanelUrl = document.getElementById('configpanelurl');
            configPanelPort = document.getElementById('configpanelport');
            if (panelUrl) panelUrl.textContent = window.location.origin;
            if (callbackUrl) callbackUrl.textContent = window.location.origin + '/api/smpp?action=receive';
            if (configPanelUrl && !configPanelUrl.value) configPanelUrl.value = window.location.protocol + '//' + window.location.hostname;
            if (configPanelPort && !configPanelPort.value) configPanelPort.value = window.location.port || (window.location.protocol === 'https:' ? '443' : '80');
            populateLegacyFilters();
            populateProfilePage();
            _context3.n = 9;
            break;
          case 8:
            _context3.p = 8;
            _t3 = _context3.v;
            console.error('GLOBAL1TEL session UI error:', _t3);
          case 9:
            return _context3.a(2);
        }
      }, _callee3, null, [[1, 8]]);
    }));
    return _loadSession.apply(this, arguments);
  }
  function logout() {
    window.location.href = '/ints/logout';
  }

  /*
   * Reliable mobile top navigation.
   * The legacy Bootstrap data-api can miss taps after the responsive header
   * is repositioned. Handle only the two top-bar controls directly while
   * leaving every page action and backend flow untouched.
   */
  /*
   * Role-isolated mobile main menu.
   * Some legacy pages contain a stale Client menu inside .nav-collapse even
   * when the page itself belongs to Agent/Manager. Rebuild that mobile menu
   * from the current role's sidebar so one panel can never display another
   * panel's navigation options.
   */
  function isolateRoleMobileMenu() {
    var role = roleFromPath();
    if (!role) return;
    var navbar = document.querySelector('.navbar.navbar-fixed-top');
    var navCollapse = navbar ? navbar.querySelector('.nav-collapse') : null;
    var sidebar = document.querySelector('#sidebar ul.side-nav');
    if (!navbar || !navCollapse || !sidebar) return;
    var mobileList = document.createElement('ul');
    mobileList.className = 'nav g1t-role-mobile-nav';
    mobileList.setAttribute('data-g1t-role', role);
    Array.prototype.forEach.call(sidebar.children, function (item) {
      if (!item || String(item.tagName).toLowerCase() !== 'li') return;
      var clone = item.cloneNode(true);

      // Avoid duplicate DOM ids after cloning sidebar items.
      if (clone.removeAttribute) clone.removeAttribute('id');
      Array.prototype.forEach.call(clone.querySelectorAll('[id]'), function (node) {
        node.removeAttribute('id');
      });
      mobileList.appendChild(clone);
    });
    if (!mobileList.children.length) return;
    while (navCollapse.firstChild) navCollapse.removeChild(navCollapse.firstChild);
    navCollapse.appendChild(mobileList);
    navCollapse.setAttribute('data-g1t-role', role);
    navbar.setAttribute('data-g1t-role', role);
  }
  function installTopNavClickFix() {
    var navbar = document.querySelector('.navbar.navbar-fixed-top');
    if (!navbar || navbar.dataset.g1tTopNavFixed === '1') return;
    navbar.dataset.g1tTopNavFixed = '1';
    var menuButton = navbar.querySelector('.btn.btn-navbar[data-toggle="collapse"]');
    var navCollapse = navbar.querySelector('.nav-collapse');
    var userItem = navbar.querySelector('ul.nav.pull-right > li.dropdown');
    var userToggle = userItem ? userItem.querySelector(':scope > a.dropdown-toggle') : null;
    function closeUserMenu() {
      if (!userItem) return;
      userItem.classList.remove('open');
      if (userToggle) userToggle.setAttribute('aria-expanded', 'false');
    }
    function closeMainMenu() {
      if (!navCollapse) return;
      navCollapse.classList.remove('in');
      if (menuButton) {
        menuButton.classList.remove('active');
        menuButton.setAttribute('aria-expanded', 'false');
      }
    }
    if (menuButton && navCollapse) {
      menuButton.setAttribute('aria-expanded', navCollapse.classList.contains('in') ? 'true' : 'false');
      menuButton.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (typeof event.stopImmediatePropagation === 'function') {
          event.stopImmediatePropagation();
        }
        var opening = !navCollapse.classList.contains('in');
        navCollapse.classList.toggle('in', opening);
        menuButton.classList.toggle('active', opening);
        menuButton.setAttribute('aria-expanded', opening ? 'true' : 'false');
        if (opening) closeUserMenu();
      }, true);
    }
    if (userToggle && userItem) {
      userToggle.setAttribute('aria-expanded', userItem.classList.contains('open') ? 'true' : 'false');

      /* GLOBAL1TEL: plain click no longer opens the user menu — it's
         press-and-hold only (see custom-script.js). A click here
         still closes it if it happens to be open, and still
         prevents the default '#' link navigation. */
      userToggle.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        if (typeof event.stopImmediatePropagation === 'function') {
          event.stopImmediatePropagation();
        }
        if (userItem.classList.contains('open')) {
          closeUserMenu();
        }
      }, true);
    }
    document.addEventListener('click', function (event) {
      if (userItem && userItem.classList.contains('open') && !userItem.contains(event.target)) {
        closeUserMenu();
      }
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' || event.keyCode === 27) {
        closeUserMenu();
        closeMainMenu();
      }
    });
  }
  document.addEventListener('click', function (event) {
    var a = event.target.closest('a');
    if (!a || !/\bLogout\b/i.test(a.textContent || '')) return;
    event.preventDefault();
    logout();
  });
  document.addEventListener('DOMContentLoaded', function () {
    isolateRoleMobileMenu();
    installTopNavClickFix();
    refreshLegacyDateDefaults();
    enableLegacyFilters();
    loadSession();
    updateSidebarClock();
    setInterval(updateSidebarClock, 1000);
  });
})();

/* GLOBAL1TEL: profile dropdown click fallback only.
   Keeps every other page/control untouched. */
(function () {
  'use strict';

  function getProfileParts() {
    var item = document.querySelector('.navbar.navbar-fixed-top ul.nav.pull-right > li.dropdown');
    if (!item) return null;
    var toggle = item.querySelector('a.dropdown-toggle');
    var menu = item.querySelector('ul.dropdown-menu');
    if (!toggle || !menu) return null;
    return {
      item: item,
      toggle: toggle,
      menu: menu
    };
  }
  function isOpen(parts) {
    if (!parts) return false;
    return parts.item.classList.contains('open') || parts.menu.style.getPropertyValue('display') === 'block';
  }
  function openMenu(parts) {
    if (!parts) return;
    parts.item.classList.add('open');
    parts.toggle.setAttribute('aria-expanded', 'true');
    parts.menu.style.setProperty('display', 'block', 'important');
    parts.menu.style.setProperty('visibility', 'visible', 'important');
    parts.menu.style.setProperty('opacity', '1', 'important');
    parts.menu.style.setProperty('pointer-events', 'auto', 'important');
  }
  function closeMenu(parts) {
    if (!parts) return;
    parts.item.classList.remove('open');
    parts.toggle.setAttribute('aria-expanded', 'false');
    parts.menu.style.removeProperty('display');
    parts.menu.style.removeProperty('visibility');
    parts.menu.style.removeProperty('opacity');
    parts.menu.style.removeProperty('pointer-events');
  }

  /* GLOBAL1TEL: click-to-open fallback disabled on purpose — the menu is
     press-and-hold only now (see custom-script.js). Only the close
     handlers below stay active. */

  document.addEventListener('click', function (event) {
    var parts = getProfileParts();
    if (!parts || !isOpen(parts)) return;
    if (!parts.item.contains(event.target)) closeMenu(parts);
  }, false);
  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape' && event.keyCode !== 27) return;
    closeMenu(getProfileParts());
  }, false);
})();

/* G1T_HAMBURGER_MAIN_MENU_PRIORITY_FIX_START
 * Scope: white three-line top button only.
 * Gives the hamburger tap priority over the profile control and opens the
 * existing dark main navigation. No page/backend/style logic is changed.
 */
(function () {
  'use strict';

  var lastPointerToggle = 0;
  function parts() {
    var navbar = document.querySelector('.navbar.navbar-fixed-top');
    if (!navbar) return null;
    var button = navbar.querySelector('.btn.btn-navbar[data-toggle="collapse"]');
    var menu = navbar.querySelector('.nav-collapse');
    if (!button || !menu) return null;
    return {
      navbar: navbar,
      button: button,
      menu: menu,
      profileItem: navbar.querySelector('ul.nav.pull-right > li.dropdown')
    };
  }
  function closeProfile(p) {
    var item = p && p.profileItem;
    if (!item) return;
    item.classList.remove('open');
    item.classList.remove('g1t-profile-open');
    var toggle = item.querySelector('a.dropdown-toggle');
    var dropdown = item.querySelector('ul.dropdown-menu');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
    if (dropdown) {
      dropdown.style.removeProperty('display');
      dropdown.style.removeProperty('visibility');
      dropdown.style.removeProperty('opacity');
      dropdown.style.removeProperty('pointer-events');
    }
  }
  function setSubmenus(menu, open) {
    menu.querySelectorAll('ul.acitem').forEach(function (sub) {
      if (open) {
        if (!Object.prototype.hasOwnProperty.call(sub.dataset, 'g1tHamburgerOldDisplay')) {
          sub.dataset.g1tHamburgerOldDisplay = sub.style.display || '';
        }
        sub.style.setProperty('display', 'block', 'important');
      } else {
        var old = sub.dataset.g1tHamburgerOldDisplay;
        sub.style.removeProperty('display');
        if (old) sub.style.display = old;
        delete sub.dataset.g1tHamburgerOldDisplay;
      }
    });
  }
  function setMenu(p, open) {
    closeProfile(p);
    p.button.classList.remove('active');
    p.button.setAttribute('aria-expanded', open ? 'true' : 'false');
    p.menu.classList.toggle('in', open);
    if (open) {
      setSubmenus(p.menu, true);
      p.menu.style.setProperty('display', 'block', 'important');
      p.menu.style.setProperty('height', 'auto', 'important');
      p.menu.style.setProperty('overflow', 'visible', 'important');
    } else {
      setSubmenus(p.menu, false);
      p.menu.style.removeProperty('display');
      p.menu.style.removeProperty('height');
      p.menu.style.removeProperty('overflow');
    }
  }
  function isButtonTarget(target, p) {
    return !!(target && p && (target === p.button || p.button.contains(target)));
  }
  function handle(event, kind) {
    var p = parts();
    if (!isButtonTarget(event.target, p)) return;
    var now = Date.now();
    if (kind === 'click' && now - lastPointerToggle < 700) {
      event.preventDefault();
      event.stopPropagation();
      if (event.stopImmediatePropagation) event.stopImmediatePropagation();
      return;
    }
    if (kind === 'pointer') lastPointerToggle = now;
    event.preventDefault();
    event.stopPropagation();
    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
    setMenu(p, !p.menu.classList.contains('in'));
  }
  function prioritizeButton() {
    var p = parts();
    if (!p) return;
    /* The profile control previously had the higher z-index. */
    p.button.style.setProperty('z-index', '30060', 'important');
    p.button.setAttribute('aria-expanded', p.menu.classList.contains('in') ? 'true' : 'false');
  }
  document.addEventListener('pointerup', function (event) {
    handle(event, 'pointer');
  }, true);
  document.addEventListener('click', function (event) {
    handle(event, 'click');
  }, true);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', prioritizeButton, {
      once: true
    });
  } else {
    prioritizeButton();
  }
})();
/* G1T_HAMBURGER_MAIN_MENU_PRIORITY_FIX_END */

/* G1T_MOBILE_MAIN_MENU_PUSH_CONTENT_V1_START
 * Scope: mobile hamburger/main-navigation vertical push behavior only.
 * When the existing dark .nav-collapse opens, increase the outer navbar's
 * normal-flow height so the page content moves down. On close, restore the
 * original height. No page actions, profile menu, table, or backend logic is changed.
 */
(function () {
  'use strict';

  function mobileOnly() {
    return !window.matchMedia || window.matchMedia('(max-width: 979px)').matches;
  }
  function getParts() {
    var navbar = document.querySelector('.navbar.navbar-fixed-top');
    if (!navbar) return null;
    var header = navbar.querySelector('.navbar-inner.top-nav');
    var menu = navbar.querySelector('.nav-collapse');
    if (!header || !menu) return null;
    return {
      navbar: navbar,
      header: header,
      menu: menu
    };
  }
  function clearPush(p) {
    if (!p) return;
    p.navbar.style.removeProperty('height');
    p.navbar.style.removeProperty('min-height');
  }
  function syncPush() {
    var p = getParts();
    if (!p) return;
    if (!mobileOnly() || !p.menu.classList.contains('in')) {
      clearPush(p);
      return;
    }

    /* Measure after the existing hamburger code has made the menu visible
       and expanded its legacy submenus. */
    window.requestAnimationFrame(function () {
      if (!p.menu.classList.contains('in')) {
        clearPush(p);
        return;
      }
      var headerHeight = Math.ceil(p.header.getBoundingClientRect().height || 74);
      var menuHeight = Math.ceil(Math.max(p.menu.scrollHeight || 0, p.menu.getBoundingClientRect().height || 0));
      var total = Math.max(headerHeight, headerHeight + menuHeight);
      p.navbar.style.setProperty('height', total + 'px', 'important');
      p.navbar.style.setProperty('min-height', total + 'px', 'important');
    });
  }
  function install() {
    var p = getParts();
    if (!p || p.navbar.dataset.g1tPushMenuInstalled === '1') return;
    p.navbar.dataset.g1tPushMenuInstalled = '1';
    var observer = new MutationObserver(function () {
      syncPush();
    });
    observer.observe(p.menu, {
      attributes: true,
      attributeFilter: ['class', 'style'],
      subtree: true
    });
    if (window.ResizeObserver) {
      var resizeObserver = new ResizeObserver(function () {
        if (p.menu.classList.contains('in')) syncPush();
      });
      resizeObserver.observe(p.menu);
    }
    window.addEventListener('resize', syncPush, {
      passive: true
    });
    window.addEventListener('orientationchange', syncPush, {
      passive: true
    });
    syncPush();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install, {
      once: true
    });
  } else {
    install();
  }
})();
/* G1T_MOBILE_MAIN_MENU_PUSH_CONTENT_V1_END */