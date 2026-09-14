// 探索：在 Node 中模拟浏览器环境加载 _bdms.js，查看 window.bdms 暴露的 API
const fs = require("fs");
const path = require("path");
const vm = require("vm");

// ---- 最小浏览器环境 shim ----
const fakeFn = function () {};
fakeFn.toString = () => "function () { [native code] }";

function makeLocation() {
  const loc = {
    href: "https://www.shidianguji.com/book/NA11023",
    origin: "https://www.shidianguji.com",
    protocol: "https:",
    host: "www.shidianguji.com",
    hostname: "www.shidianguji.com",
    port: "",
    pathname: "/book/NA11023",
    search: "",
    hash: "",
    ancestorOrigins: {},
    assign: fakeFn, replace: fakeFn, reload: fakeFn,
    toString: () => loc.href,
  };
  return loc;
}

function makeNavigator() {
  const nav = {
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    platform: "Win32",
    language: "zh-CN",
    languages: ["zh-CN", "zh", "en"],
    vendor: "Google Inc.",
    appVersion: "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    cookieEnabled: true,
    onLine: true,
    webdriver: false,
    hardwareConcurrency: 16,
    maxTouchPoints: 0,
    deviceMemory: 8,
    plugins: { length: 0 },
    mimeTypes: { length: 0 },
    geolocation: {},
    connection: { effectiveType: "4g", downlink: 10, rtt: 50, saveData: false },
    sendBeacon: fakeFn,
    webkitGetUserMedia: fakeFn,
  };
  nav.toString = () => nav.userAgent;
  return nav;
}

const sandbox = {
  console,
  setTimeout, clearTimeout, setInterval, clearInterval,
  // performance
  performance: typeof performance !== "undefined" ? performance : {
    now: () => Date.now(), timeOrigin: Date.now(),
    getEntriesByType: () => [], mark: fakeFn, measure: fakeFn,
    getEntries: () => [],
  },
  // URL / URLSearchParams from Node
  URL, URLSearchParams,
  TextEncoder, TextDecoder,
  // crypto: Node webcrypto + randomBytes
  crypto: require("crypto").webcrypto,
  // Buffer/typed arrays
  Uint8Array, Uint16Array, Uint32Array, Int8Array, Int16Array, Int32Array,
  Float32Array, Float64Array, ArrayBuffer, DataView, BigInt, Symbol, Map, Set, WeakMap, WeakSet, Proxy, Reflect,
  // date/locale
  Date, Math, JSON, Object, Array, String, Number, Boolean, RegExp, Error, TypeError, RangeError,
  Promise, QueueMicrotask: (fn) => queueMicrotask(fn),
  parseInt, parseFloat, isNaN, isFinite, encodeURIComponent, decodeURIComponent, encodeURI, decodeURI,
  escape, unescape,
};

// window 与 globalThis 关联
const context = vm.createContext(sandbox);
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.self = sandbox;
sandbox.top = sandbox;
sandbox.parent = sandbox;
sandbox.frames = sandbox;
sandbox.window.window = sandbox.window;
sandbox.navigator = makeNavigator();
sandbox.location = makeLocation();
sandbox.document = {
  documentElement: { clientWidth: 1920, clientHeight: 937, getBoundingClientRect: () => ({ left: 0, top: 0, width: 1920, height: 937 }) },
  body: {},
  head: { appendChild: fakeFn },
  createElement: () => ({ style: {}, setAttribute: fakeFn, appendChild: fakeFn, remove: fakeFn, addEventListener: fakeFn }),
  createTextNode: (t) => ({ nodeType: 3, textContent: t, nodeName: "#text" }),
  createDocumentFragment: () => ({ nodeType: 11, appendChild: fakeFn, childNodes: [] }),
  createComment: (t) => ({ nodeType: 8, textContent: t }),
  createAttribute: (n) => ({ name: n, value: "" }),
  getElementById: () => null,
  getElementsByTagName: () => [],
  getElementsByClassName: () => [],
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener: fakeFn,
  removeEventListener: fakeFn,
  readyState: "complete",
  cookie: "",
  referrer: "",
  title: "",
  visibilityState: "visible",
  hidden: false,
  onvisibilitychange: null,
};

// XMLHttpRequest 假实现（避免真实网络调用）
class FakeXHR {
  constructor() { this.readyState = 0; this.status = 0; this.responseText = ""; this.response = ""; this._finalUrl = null; this._headers = {}; }
  open(method, url) { this.readyState = 1; this._method = method; this._finalUrl = url; this._url = url; }
  setRequestHeader(k, v) { this._headers[k] = v; }
  send() { this.readyState = 4; this.status = 200; if (this.onreadystatechange) this.onreadystatechange(); if (this.onload) this.onload(); }
  addEventListener() {}
  getResponseHeader() { return null; }
  getAllResponseHeaders() { return ""; }
  abort() {}
  static DONE = 4; static HEADERS_RECEIVED = 2; static LOADING = 3; static OPENED = 1; static UNSENT = 0;
}
sandbox.XMLHttpRequest = FakeXHR;

// fetch 假实现
sandbox.fetch = async () => { throw new Error("fetch not available in shim"); };
sandbox.Headers = class { constructor(){ } append(){} has(){return false} get(){return null} };
sandbox.Request = class { constructor(url){ this.url = url; } };
sandbox.Response = class { constructor(){ } static redirect(){ return {}; } };
sandbox.FormData = class { constructor(){ } append(){} };
sandbox.Blob = class { constructor(parts){ this.parts = parts; } };
sandbox.FileReader = class { };
sandbox.Image = class { constructor(){ this.style = {}; this.setAttribute = fakeFn; this.addEventListener = fakeFn; } };
sandbox.Audio = class { constructor(){ this.play = fakeFn; } };
sandbox.HTMLElement = class { };
sandbox.Element = class { };
sandbox.Node = class { };
sandbox.Event = class { constructor(type){ this.type = type; } };
sandbox.CustomEvent = class { };
sandbox.MouseEvent = class { };
sandbox.KeyboardEvent = class { };
sandbox.PointerEvent = class { };
sandbox.TouchEvent = class { };
sandbox.Storage = class { };
sandbox.localStorage = { getItem: () => null, setItem: fakeFn, removeItem: fakeFn, clear: fakeFn, key: () => null, length: 0 };
sandbox.sessionStorage = { getItem: () => null, setItem: fakeFn, removeItem: fakeFn, clear: fakeFn, key: () => null, length: 0 };
sandbox.screen = { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24, orientation: { type: "landscape-primary" } };
sandbox.history = { length: 1, state: null, pushState: fakeFn, replaceState: fakeFn, back: fakeFn, forward: fakeFn, go: fakeFn };
sandbox.devicePixelRatio = 1;
sandbox.open = fakeFn;
sandbox.close = fakeFn;
sandbox.postMessage = fakeFn;
sandbox.addEventListener = fakeFn;
sandbox.removeEventListener = fakeFn;
sandbox.matchMedia = () => ({ matches: false, addListener: fakeFn, removeListener: fakeFn, addEventListener: fakeFn, removeEventListener: fakeFn });
sandbox.getComputedStyle = () => ({});
sandbox.requestAnimationFrame = (cb) => setTimeout(cb, 16);
sandbox.cancelAnimationFrame = (id) => clearTimeout(id);
sandbox.requestIdleCallback = (cb) => setTimeout(() => cb({ didTimeout: false, timeRemaining: () => 50 }), 1);
sandbox.cancelIdleCallback = (id) => clearTimeout(id);
sandbox.StyleSheet = class { };
sandbox.CSSStyleSheet = class { };
sandbox.NodeList = Array;
sandbox.HTMLCollection = Array;
sandbox.MessageChannel = class { constructor(){ this.port1 = { postMessage: fakeFn, addEventListener: fakeFn, start: fakeFn }; this.port2 = { postMessage: fakeFn, addEventListener: fakeFn, start: fakeFn }; } };
sandbox.MessageEvent = class { };
sandbox.Worker = class { constructor(){ this.postMessage = fakeFn; this.terminate = fakeFn; this.addEventListener = fakeFn; } };
sandbox.SharedWorker = class { };
sandbox.Notification = class { };
sandbox.Permission = class { };
sandbox.Geolocation = class { };
sandbox.ResizeObserver = class { constructor(){ } observe(){} unobserve(){} disconnect(){} };
sandbox.IntersectionObserver = class { constructor(){ } observe(){} unobserve(){} disconnect(){} };
sandbox.MutationObserver = class { constructor(){ } observe(){} disconnect(){} takeRecords(){ return []; } };
sandbox.Promise.prototype.finally = Promise.prototype.finally || sandbox.Promise.prototype.finally;
// 兼容浏览器 API
if (!sandbox.String.prototype.trimStart) sandbox.String.prototype.trimStart = sandbox.String.prototype.trimLeft;
if (!sandbox.String.prototype.trimEnd) sandbox.String.prototype.trimEnd = sandbox.String.prototype.trimRight;
if (!sandbox.Array.prototype.flat) sandbox.Array.prototype.flat = function (d) { return [].concat(...this); };
if (!sandbox.Array.prototype.flatMap) sandbox.Array.prototype.flatMap = function (fn) { return this.map(fn).flat(); };

// atob/btoa (Node 18+ 有)
sandbox.atob = (s) => Buffer.from(s, "base64").toString("binary");
sandbox.btoa = (s) => Buffer.from(s, "binary").toString("base64");

// ---------- 加载 bdms ----------
const code = fs.readFileSync(path.join(__dirname, "_bdms.js"), "utf-8");
try {
  vm.runInContext(code, context, { filename: "_bdms.js" });
  console.log("LOAD OK");
} catch (e) {
  console.log("LOAD FAIL:", e && e.stack ? e.stack.split("\n").slice(0, 8).join("\n") : e);
  process.exit(1);
}

const bdms = sandbox.window.bdms;
console.log("typeof window.bdms =", typeof bdms);
console.log("keys:", Object.keys(bdms));

// 带真实配置初始化
try {
  const r = bdms.init({
    aid: 361265,
    pageId: 1,
    paths: ["/api/ancientlib/read/"],
  });
  console.log("init(config) ->", r);
} catch (e) {
  console.log("init threw:", e && e.message);
}

console.log("window.bdms keys after init:", Object.keys(bdms));

// 通过 shim XHR 发起目标请求，观察 interceptor 是否附加 a_bogus
const targetUrl = "https://www.shidianguji.com/api/ancientlib/read/reader-book/get/?bookId=NA11023&version=0&needCheckVersion=false&isWebpSupported=true&verifyFp=verify_abc&fp=abc&msToken=abc";
const xhr = new FakeXHR();
xhr.open("GET", targetUrl, true);
xhr.setRequestHeader("Content-type", "application/json");
xhr.send(null);
console.log("XHR final URL:", xhr._finalUrl || "(no capture)");
console.log("XHR status:", xhr.status, "readyState:", xhr.readyState);

// 也试试 fetch
(async () => {
  try {
    const resp = await sandbox.fetch(targetUrl);
    console.log("fetch ok");
  } catch (e) {
    console.log("fetch err:", e && e.message);
  }
  console.log("--- done ---");
  process.exit(0);
})();
setTimeout(() => { console.log("--- timeout done ---"); process.exit(0); }, 5000);
