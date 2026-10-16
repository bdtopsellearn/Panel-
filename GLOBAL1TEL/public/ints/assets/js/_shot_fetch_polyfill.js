/* Temporary shim used only for generating panel preview screenshots.
   The renderer's engine has no window.fetch, so panel pages showed
   "Loading..." forever. This maps fetch() onto XMLHttpRequest.
   Not shipped with the panel. */
(function () {
  if (window.fetch) return;
  window.fetch = function (url, opts) {
    opts = opts || {};
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open(opts.method || 'GET', url, true);
      xhr.withCredentials = true;
      var headers = opts.headers || {};
      for (var k in headers) {
        if (Object.prototype.hasOwnProperty.call(headers, k)) {
          try { xhr.setRequestHeader(k, headers[k]); } catch (e) {}
        }
      }
      xhr.onload = function () {
        var body = xhr.responseText;
        resolve({
          ok: xhr.status >= 200 && xhr.status < 300,
          status: xhr.status,
          statusText: xhr.statusText,
          url: url,
          headers: {
            get: function (n) { return xhr.getResponseHeader(n); }
          },
          text: function () { return Promise.resolve(body); },
          json: function () {
            try { return Promise.resolve(JSON.parse(body)); }
            catch (e) { return Promise.reject(e); }
          }
        });
      };
      xhr.onerror = function () { reject(new TypeError('Network request failed')); };
      xhr.send(opts.body || null);
    });
  };
})();
