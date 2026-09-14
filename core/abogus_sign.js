// abogus_sign.js —— 调用识典古籍安全 SDK（bdms.js）为指定 URL 生成 a_bogus 签名
// 用法: node abogus_sign.js "<目标URL>"   （URL 为签名前的完整查询串）
// 输出: {"a_bogus":"..."} 到 stdout
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");

// 与 Python 端保持一致的用户代理（a_bogus 与 UA 哈希绑定）
// 可通过第二个参数指定 UA（PowerShell 引号注意），默认 Chrome/128
const UA = process.argv[3] || "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36";

const fakeFn = function () {};
fakeFn.toString = () => "function () { [native code] }";

function makeLocation() {
  const loc = {
    href: "https://www.shidianguji.com/",
    origin: "https://www.shidianguji.com",
    protocol: "https:",
    host: "www.shidianguji.com",
    hostname: "www.shidianguji.com",
    port: "",
    pathname: "/",
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
    userAgent: UA,
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
  performance: {
    now: () => Date.now(), timeOrigin: Date.now(),
    getEntriesByType: () => [], mark: fakeFn, measure: fakeFn, getEntries: () => [],
  },
  URL, URLSearchParams,
  TextEncoder, TextDecoder,
  crypto: require("crypto").webcrypto,
  Uint8Array, Uint16Array, Uint32Array, Int8Array, Int16Array, Int32Array,
  Float32Array, Float64Array, ArrayBuffer, DataView, BigInt, Symbol, Map, Set, WeakMap, WeakSet, Proxy, Reflect,
  Date, Math, JSON, Object, Array, String, Number, Boolean, RegExp, Error, TypeError, RangeError,
  Promise,
  parseInt, parseFloat, isNaN, isFinite, encodeURIComponent, decodeURIComponent, encodeURI, decodeURI,
  escape, unescape,
};

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

class FakeXHR {
  constructor() {
    this.readyState = 0; this.status = 0; this.responseText = ""; this.response = "";
    this._finalUrl = null; this._headers = {};
  }
  open(method, url) { this.readyState = 1; this._method = method; this._finalUrl = url; this._url = url; }
  setRequestHeader(k, v) { this._headers[k] = v; }
  send() {
    this.readyState = 4; this.status = 200;
    if (this.onreadystatechange) this.onreadystatechange();
    if (this.onload) this.onload();
  }
  addEventListener() {}
  getResponseHeader() { return null; }
  getAllResponseHeaders() { return ""; }
  abort() {}
  static DONE = 4; static HEADERS_RECEIVED = 2; static LOADING = 3; static OPENED = 1; static UNSENT = 0;
}
sandbox.XMLHttpRequest = FakeXHR;

sandbox.fetch = async () => { throw new Error("fetch not available in shim"); };
sandbox.Headers = class { constructor(){} append(){} has(){return false} get(){return null} };
sandbox.Request = class { constructor(url){ this.url = url; } };
sandbox.Response = class { constructor(){} static redirect(){ return {}; } };
sandbox.FormData = class { constructor(){} append(){} };
sandbox.Blob = class { constructor(parts){ this.parts = parts; } };
sandbox.FileReader = class {};
sandbox.Image = class { constructor(){ this.style = {}; this.setAttribute = fakeFn; this.addEventListener = fakeFn; } };
sandbox.Audio = class { constructor(){ this.play = fakeFn; } };
sandbox.HTMLElement = class {};
sandbox.Element = class {};
sandbox.Node = class {};
sandbox.Event = class { constructor(type){ this.type = type; } };
sandbox.CustomEvent = class {};
sandbox.MouseEvent = class {};
sandbox.KeyboardEvent = class {};
sandbox.PointerEvent = class {};
sandbox.TouchEvent = class {};
sandbox.Storage = class {};
sandbox.localStorage = { getItem: () => null, setItem: fakeFn, removeItem: fakeFn, clear: fakeFn, key: () => null, length: 0 };
sandbox.sessionStorage = { getItem: () => null, setItem: fakeFn, removeItem: fakeFn, clear: fakeFn, key: () => null, length: 0 };
sandbox.screen = { width: 1920, height: 1080, availWidth: 1920, availHeight: 1040, colorDepth: 24, pixelDepth: 24, orientation: { type: "landscape-primary" } };
sandbox.history = { length: 1, state: null, pushState: fakeFn, replaceState: fakeFn, back: fakeFn, forward: fakeFn, go: fakeFn };
sandbox.devicePixelRatio = 1;
sandbox.innerWidth = 1920;
sandbox.innerHeight = 937;
sandbox.outerWidth = 1920;
sandbox.outerHeight = 1040;
sandbox.screenX = 0;
sandbox.screenY = 0;
sandbox.screenLeft = 0;
sandbox.screenTop = 0;
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
sandbox.StyleSheet = class {};
sandbox.CSSStyleSheet = class {};
sandbox.NodeList = Array;
sandbox.HTMLCollection = Array;
sandbox.MessageChannel = class { constructor(){ this.port1 = { postMessage: fakeFn, addEventListener: fakeFn, start: fakeFn }; this.port2 = { postMessage: fakeFn, addEventListener: fakeFn, start: fakeFn }; } };
sandbox.MessageEvent = class {};
sandbox.Worker = class { constructor(){ this.postMessage = fakeFn; this.terminate = fakeFn; this.addEventListener = fakeFn; } };
sandbox.SharedWorker = class {};
sandbox.Notification = class {};
sandbox.Permission = class {};
sandbox.Geolocation = class {};
sandbox.ResizeObserver = class { constructor(){} observe(){} unobserve(){} disconnect(){} };
sandbox.IntersectionObserver = class { constructor(){} observe(){} unobserve(){} disconnect(){} };
sandbox.MutationObserver = class { constructor(){} observe(){} disconnect(){} takeRecords(){ return []; } };
sandbox.atob = (s) => Buffer.from(s, "base64").toString("binary");
sandbox.btoa = (s) => Buffer.from(s, "binary").toString("base64");

// ---------- 主逻辑 ----------
function sign(url) {
  const code = fs.readFileSync(path.join(__dirname, "bdms.js"), "utf-8");
  vm.runInContext(code, context, { filename: "bdms.js" });
  const bdms = sandbox.window.bdms;
  if (!bdms || typeof bdms.init !== "function") {
    throw new Error("bdms init 不可用");
  }
  bdms.init({ aid: 361265, pageId: 1, paths: ["/api/ancientlib/read/"] });

  const xhr = new FakeXHR();
  xhr.open("GET", url, true);
  xhr.setRequestHeader("Content-type", "application/json");
  xhr.send(null);
  if (!xhr._finalUrl) throw new Error("SDK 未返回最终 URL");
  const finalUrl = new URL(xhr._finalUrl, url);
  const bogus = finalUrl.searchParams.get("a_bogus");
  if (!bogus) throw new Error("未生成 a_bogus");
  return bogus;
}

let input = "";
if (process.argv[2]) {
  input = process.argv[2];
} else {
  // 支持从 stdin 读取一行 JSON
  input = fs.readFileSync(0, "utf-8").trim();
}
let url = input;
try {
  const obj = JSON.parse(input);
  if (obj && obj.url) url = obj.url;
} catch (e) { /* 视为纯 URL */ }

try {
  const bogus = sign(url);
  process.stdout.write(JSON.stringify({ a_bogus: bogus }));
  process.exit(0);
} catch (e) {
  process.stdout.write(JSON.stringify({ error: String(e && e.message || e) }));
  process.exit(1);
}
