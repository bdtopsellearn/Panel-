/*==========================================================
CLIENT ERROR REPORTER — catches any JS error or rejected
promise in the browser and sends it to the server, which
prints it straight to the terminal running `python run.py`.
No devtools needed: whatever breaks shows up in the terminal,
ready to copy and paste.
==========================================================*/
(function () {
  var already = {};

  function send(payload) {
    // De-dupe identical errors firing repeatedly (e.g. inside a loop)
    // so one bug doesn't flood the terminal.
    var key = payload.kind + '|' + payload.message + '|' + payload.source + '|' + payload.line;
    if (already[key]) { return; }
    already[key] = true;

    payload.url = window.location.href;
    try {
      if (window.fetch) {
        fetch('/api/client-error', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } else if (window.jQuery) {
        jQuery.ajax({
          url: '/api/client-error',
          type: 'POST',
          contentType: 'application/json',
          data: JSON.stringify(payload)
        });
      }
    } catch (e) {
      // Reporting itself must never throw.
    }
  }

  window.onerror = function (message, source, lineno, colno, error) {
    send({
      kind: 'js-error',
      message: String(message || ''),
      source: String(source || ''),
      line: lineno || 0,
      col: colno || 0,
      stack: error && error.stack ? String(error.stack) : ''
    });
    return false;
  };

  window.addEventListener('unhandledrejection', function (event) {
    var reason = event && event.reason;
    var message = reason && reason.message ? reason.message : String(reason);
    var stack = reason && reason.stack ? String(reason.stack) : '';
    send({
      kind: 'unhandled-promise-rejection',
      message: message,
      source: '',
      line: 0,
      col: 0,
      stack: stack
    });
  });
})();

/*==========================
TOUCHY SCROLL FOR SIDEBAR
==========================*/
$('.accordion_mnu').initMenu();
$("#sidebar").niceScroll({
  cursorcolor: "#2f2e2e",
  cursoropacitymax: 0.7,
  boxzoom: false,
  touchbehavior: true
});
$("#sidebar").mouseover(function () {
  $("#sidebar").niceScroll().resize();
});
/*==========================================================
GLOBAL1TEL — user menu opens ONLY via press-and-hold on the
username/avatar element (top-right). A normal tap/click there,
or any click/tap anywhere else in the navbar (including the
logo area), will NOT open it.
==========================================================*/
(function () {
  var $toggle = $('.navbar .nav.pull-right li.dropdown > a.dropdown-toggle');
  if (!$toggle.length) {
    return;
  }

  // Stop Bootstrap's built-in click-to-open behavior for this toggle only.
  $toggle.removeAttr('data-toggle');

  // Stop the browser's own long-press "link" menu (Open in new tab, Copy
  // link address, etc.) from popping up while the user holds this element.
  $toggle.attr('href', 'javascript:void(0)');
  $toggle.css({
    '-webkit-touch-callout': 'none',
    '-webkit-user-select': 'none',
    'user-select': 'none',
    'touch-action': 'manipulation'
  });
  $toggle.on('contextmenu', function (e) {
    e.preventDefault();
    return false;
  });
  var HOLD_MS = 500;
  var pressTimer = null;
  var lastTouchAt = 0;
  var $menuLi = $toggle.closest('li.dropdown');
  function openMenu() {
    $('.navbar .nav.pull-right li.dropdown.open').not($menuLi).removeClass('open');
    $menuLi.addClass('open');
  }
  function closeMenu() {
    $menuLi.removeClass('open');
  }
  function cancelPress() {
    clearTimeout(pressTimer);
    pressTimer = null;
    $toggle.removeClass('g1t-pressed');
  }
  function startPress() {
    cancelPress();
    $toggle.addClass('g1t-pressed');
    pressTimer = setTimeout(function () {
      openMenu();
      pressTimer = null;
    }, HOLD_MS);
  }

  // Real touch starts/stops the press timer directly.
  $toggle.on('touchstart', function () {
    lastTouchAt = Date.now();
    startPress();
  });
  $toggle.on('touchend touchcancel', cancelPress);

  // Some older WebViews replay every tap as a synthetic mousedown/click
  // ~300ms after the real touchend. If that synthetic mousedown is
  // allowed to re-arm the timer, it fires later while the finger (and
  // attention) has already moved elsewhere, making the menu pop open
  // seemingly at random / "beside" the icon. Ignore mousedown that
  // arrives shortly after a real touch we already handled.
  $toggle.on('mousedown', function () {
    if (Date.now() - lastTouchAt < 800) {
      return;
    }
    startPress();
  });
  $toggle.on('mouseup mouseleave', cancelPress);

  // A plain click never opens/navigates.
  $toggle.on('click', function (e) {
    e.preventDefault();
    e.stopPropagation();
  });

  // Clicking/tapping anywhere outside the menu closes it.
  $(document).on('click touchstart', function (e) {
    if (!$(e.target).closest('li.dropdown').length) {
      closeMenu();
    }
  });
})();