/*
 * Minimal browser API polyfill
 *
 * To simplify cross-browser support, this script assigns the Chrome
 * `chrome` namespace to `browser` if `browser` is undefined. It does
 * not implement promise-based APIs; instead it reuses the callback-
 * based API from Chrome/Edge on browsers that support both. For full
 * WebExtension promise support across Chrome, Edge, Firefox, Opera and
 * Safari, consider including the official `webextension-polyfill`
 * library instead【585914544341444†L211-L268】. However, this lightweight
 * stub is sufficient for the functionality of this extension, which
 * does not rely on advanced asynchronous APIs.
 */
(function () {
  if (typeof window !== 'undefined' && typeof window.browser === 'undefined' && typeof window.chrome !== 'undefined') {
    window.browser = window.chrome;
  }
})();