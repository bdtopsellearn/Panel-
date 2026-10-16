function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i.return) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); } r ? i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n : (o("next", 0), o("throw", 1), o("return", 2)); }, _regeneratorDefine2(e, r, n, t); }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
(function () {
  'use strict';

  function roleFromPath() {
    var p = location.pathname.toLowerCase();
    if (p.indexOf('/ints/manager/') !== -1) return 'manager';
    if (p.indexOf('/ints/agent/') !== -1) return 'agent';
    if (p.indexOf('/ints/client/') !== -1 || p.indexOf('/ints/test/') !== -1) return 'client';
    return '';
  }
  function esc(value) {
    var div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
  }
  function setStat(label, value) {
    document.querySelectorAll('.stat-block').forEach(function (block) {
      var spans = block.querySelectorAll('.stat-count span');
      if (spans.length >= 2 && spans[0].textContent.trim() === label) {
        spans[1].textContent = Number(value || 0).toLocaleString();
      }
    });
  }
  function setSummary(label, value) {
    document.querySelectorAll('.summary li').forEach(function (li) {
      var title = li.querySelector('.summary-title');
      var count = li.querySelector('.count');
      if (title && count && title.textContent.trim() === label) {
        count.textContent = Number(value || 0).toLocaleString();
      }
    });
  }
  function replaceTable(id, rows) {
    var selector = '#' + id;
    try {
      // isDataTable() is a pure check - it never creates or touches an
      // instance. Only call .dataTable() (which DOES initialize on a bare
      // table) once we know the page's own script already set it up.
      // Calling it before that point is what used to cause DataTables'
      // "Cannot reinitialize" warning later, when the page's own init ran
      // on a table this function had already touched - on some old
      // WebViews that warning dialog never surfaces and never dismisses,
      // silently freezing the whole page.
      if (window.jQuery && jQuery.fn && jQuery.fn.dataTable &&
          jQuery.fn.dataTable.isDataTable && jQuery.fn.dataTable.isDataTable(selector)) {
        var table = jQuery(selector).dataTable();
        if (table && typeof table.fnClearTable === 'function') {
          table.fnClearTable();
          if (rows.length && typeof table.fnAddData === 'function') table.fnAddData(rows);
          return;
        }
      }
    } catch (e) {
      console.warn('GLOBAL1TEL table refresh fallback:', e);
    }
    var tbody = document.querySelector(selector + ' tbody');
    if (tbody) {
      tbody.innerHTML = rows.map(function (row) {
        return '<tr>' + row.map(function (cell) {
          return '<td>' + cell + '</td>';
        }).join('') + '</tr>';
      }).join('');
    }
  }
  function updateChart(rows) {
    if (!window.jQuery || typeof jQuery.jqplot === 'undefined') return;
    var data = (rows || []).map(function (row) {
      return [row.date, parseInt(row.count, 10) || 0];
    });
    // jqplot's DateAxisRenderer divides by the axis span when auto-scaling
    // ticks. A single data point (or all-identical dates) makes that span
    // zero and sends it into an infinite loop that freezes the tab with no
    // exception thrown. The backend now always zero-fills the full range,
    // but this stays as a second line of defense regardless of source.
    var uniqueDates = {};
    for (var i = 0; i < data.length; i++) { uniqueDates[data[i][0]] = true; }
    if (Object.keys(uniqueDates).length < 2) {
      data = [];
      for (var j = 6; j >= 0; j--) {
        var d = new Date();
        d.setDate(d.getDate() - j);
        var key = d.toISOString().slice(0, 10);
        data.push([key, uniqueDates[key] ? (parseInt((rows || []).filter(function (r) { return r.date === key; })[0].count, 10) || 0) : 0]);
      }
    }
    if (!data.length) {
      for (var i = 6; i >= 0; i--) {
        var d = new Date();
        d.setDate(d.getDate() - i);
        data.push([d.toISOString().slice(0, 10), 0]);
      }
    }
    jQuery('#chart1').empty();
    jQuery.jqplot('chart1', [data], {
      title: 'SMS LAST 7 DAYS',
      axes: {
        xaxis: {
          renderer: jQuery.jqplot.DateAxisRenderer,
          tickOptions: {
            formatString: '%b&nbsp;%#d'
          }
        },
        yaxis: {
          tickOptions: {
            formatString: '%.0f'
          }
        }
      },
      seriesDefaults: {
        show: true,
        xaxis: 'xaxis',
        yaxis: 'yaxis',
        lineWidth: 3,
        shadow: false
      },
      highlighter: {
        show: true,
        sizeAdjust: 7.5
      },
      grid: {
        background: '#fff',
        drawBorder: false,
        shadow: false,
        gridLineColor: '#ccc',
        gridLineWidth: 1
      },
      cursor: {
        show: false
      }
    });
  }
  function updateNews(news) {
    var rows = (news || []).slice(0, 5).map(function (item) {
      var date = item.created_at ? new Date(item.created_at.replace(' ', 'T')).toLocaleString() : '-';
      return [esc(date), esc(item.title || '-'), esc(item.content || '-')];
    });
    replaceTable('dbdt', rows);
  }
  function updateRecent(role, stats) {
    if (role === 'agent') {
      var rows = (stats.recent_clients || []).slice(0, 5).map(function (u) {
        var status = String(u.status || '') === 'active' ? "<span class='label label-success'>Active</span>" : "<span class='label label-important'>Inactive</span>";
        var id = parseInt(u.id, 10) || 0;
        var actions = "<a href='#' id='viewuser' info='" + id + "' class='btn btn-mini btn-info'><i class='icon-eye-open'></i></a> " + "<a href='#' id='edituser' info='" + id + "' class='btn btn-mini btn-warning'><i class='icon-edit'></i></a>";
        return [esc(u.username || '-'), esc(u.email || '-'), esc(u.phone || '-'), status, actions];
      });
      replaceTable('dbdt1', rows);
    } else if (role === 'client') {
      var ranges = (stats.recent_ranges || []).slice(0, 20).map(function (r) {
        return [esc(r.range_name || '-'), esc(r.test_number || '-')];
      });
      replaceTable('dbdt1', ranges);
    }
  }
  function applyStats(role, stats) {
    if (role === 'agent') {
      setStat('Today SMS', stats.today_sms_total != null ? stats.today_sms_total : stats.today_sms);
      setStat('SMS Yesterday', stats.yesterday_sms);
      setStat('SMS This Week', stats.last_7_days_sms);
      setStat('SMS This Month', stats.month_sms_total != null ? stats.month_sms_total : stats.month_sms);
      setSummary('Total Clients', stats.total_clients);
      setSummary('Assigned Numbers', stats.assigned_numbers);
      setSummary('Today SMS', stats.today_sms_total != null ? stats.today_sms_total : stats.today_sms);
    } else if (role === 'client') {
      setStat('Today SMS', stats.today_sms);
      setStat('Last 7 Day SMS', stats.last_7_days_sms);
      setStat('Last 30 Day SMS', stats.last_30_days_sms);
      setSummary('Assigned Numbers', stats.assigned_numbers);
      setSummary('SMS This Month', stats.month_sms);
    }
    updateNews(stats.news || []);
    updateRecent(role, stats);
  }
  function load() {
    return _load.apply(this, arguments);
  }
  function _load() {
    _load = _asyncToGenerator(/*#__PURE__*/_regenerator().m(function _callee() {
      var role, statsResponse, statsJson, chartResponse, chartJson, _t;
      return _regenerator().w(function (_context) {
        while (1) switch (_context.p = _context.n) {
          case 0:
            role = roleFromPath();
            if (!(role !== 'agent' && role !== 'client')) {
              _context.n = 1;
              break;
            }
            return _context.a(2);
          case 1:
            _context.p = 1;
            _context.n = 2;
            return fetch('/api/dashboard?action=stats', {
              credentials: 'include',
              cache: 'no-store'
            });
          case 2:
            statsResponse = _context.v;
            _context.n = 3;
            return statsResponse.json();
          case 3:
            statsJson = _context.v;
            if (statsResponse.ok && statsJson.success && statsJson.stats) applyStats(role, statsJson.stats);
            _context.n = 4;
            return fetch('/api/dashboard?action=chart&type=sms&period=7days', {
              credentials: 'include',
              cache: 'no-store'
            });
          case 4:
            chartResponse = _context.v;
            _context.n = 5;
            return chartResponse.json();
          case 5:
            chartJson = _context.v;
            if (chartResponse.ok && chartJson.success) updateChart(chartJson.data || []);
            _context.n = 7;
            break;
          case 6:
            _context.p = 6;
            _t = _context.v;
            console.error('GLOBAL1TEL dashboard refresh failed:', _t);
          case 7:
            return _context.a(2);
        }
      }, _callee, null, [[1, 6]]);
    }));
    return _load.apply(this, arguments);
  }
  document.addEventListener('DOMContentLoaded', function () {
    window.setTimeout(load, 250);
  });
})();