/* Constitution page: source panels, level/party filters, search, agreement map, copy link. */
(function () {
  "use strict";
  var secs = Array.prototype.slice.call(document.querySelectorAll("p.sec"));
  if (!secs.length) return;

  var state = { q: "", lvl: null, party: null };
  var original = new Map();
  var plain = new Map();

  function norm(s) {
    return s.replace(/[׳’‘`]/g, "'").replace(/[״“”]/g, '"').toLowerCase();
  }

  secs.forEach(function (p) {
    original.set(p, p.innerHTML);
    var clone = p.cloneNode(true);
    var pill = clone.querySelector(".lvl-pill");
    if (pill) pill.remove();
    plain.set(p, norm(clone.textContent));
  });

  // chapter groups: each h2#ch-* followed by its sections (and panels)
  var groups = [];
  Array.prototype.forEach.call(document.querySelectorAll('.legal h2[id^="ch-"]'), function (h) {
    var g = { head: h, secs: [] };
    var el = h.nextElementSibling;
    while (el && el.tagName !== "H2" && el.tagName !== "SECTION") {
      if (el.matches("p.sec")) g.secs.push(el);
      el = el.nextElementSibling;
    }
    groups.push(g);
  });
  var preambleHead = document.getElementById("preamble");
  var preambleText = preambleHead ? preambleHead.nextElementSibling : null;
  var appendix = document.getElementById("appendix-wrap");
  var cells = Array.prototype.slice.call(document.querySelectorAll(".explorer .cell"));
  var cellBySec = {};
  cells.forEach(function (c) { cellBySec[c.dataset.sec] = c; });
  var statusEl = document.getElementById("ex-status");
  var statusDefault = statusEl ? statusEl.textContent : "";
  var clearBtn = document.getElementById("ex-clear");
  var qInput = document.getElementById("q");

  function panelOf(p) { return document.getElementById("src-" + p.id.slice(2)); }
  function pillOf(p) { return p.querySelector(".lvl-pill"); }

  function highlight(p, q) {
    p.innerHTML = original.get(p);
    if (!q) return;
    var walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) { return n.parentElement.closest(".lvl-pill") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; }
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var text = node.nodeValue, low = norm(text), i = low.indexOf(q);
      if (i < 0) return;
      var frag = document.createDocumentFragment(), last = 0;
      while (i >= 0) {
        frag.appendChild(document.createTextNode(text.slice(last, i)));
        var m = document.createElement("mark");
        m.textContent = text.slice(i, i + q.length);
        frag.appendChild(m);
        last = i + q.length;
        i = low.indexOf(q, last);
      }
      frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  function matches(p) {
    if (state.lvl && (" " + p.dataset.lvls + " ").indexOf(" " + state.lvl + " ") < 0) return false;
    if (state.party && (" " + p.dataset.parties + " ").indexOf(" " + state.party + " ") < 0) return false;
    if (state.q && plain.get(p).indexOf(state.q) < 0) return false;
    return true;
  }

  function apply() {
    var active = !!(state.q || state.lvl || state.party);
    var shown = 0;
    secs.forEach(function (p) {
      var open = pillOf(p) && pillOf(p).getAttribute("aria-expanded") === "true";
      var ok = matches(p);
      var wasOpen = open;
      highlight(p, ok ? state.q : "");
      // innerHTML reset recreated the pill: restore its state
      if (wasOpen) pillOf(p).setAttribute("aria-expanded", "true");
      p.hidden = !ok;
      var panel = panelOf(p);
      if (panel) panel.hidden = !ok || !wasOpen;
      if (cellBySec[p.id.slice(2)]) cellBySec[p.id.slice(2)].classList.toggle("off", !ok);
      if (ok) shown++;
    });
    groups.forEach(function (g) {
      var any = g.secs.some(function (p) { return !p.hidden; });
      g.head.hidden = !any;
      var li = document.querySelector('.rail li[data-ch="' + g.head.id + '"]');
      if (li) li.hidden = !any;
    });
    if (preambleHead) { preambleHead.hidden = active; if (preambleText) preambleText.hidden = active; }
    if (appendix) appendix.hidden = active;
    if (statusEl) {
      statusEl.textContent = active
        ? (shown ? "מוצגים " + shown + " מתוך " + secs.length + " סעיפים." : "אין סעיפים שמתאימים לסינון.")
        : statusDefault;
    }
    if (clearBtn) clearBtn.hidden = !active;
  }

  function setChip(attr, value) {
    Array.prototype.forEach.call(document.querySelectorAll(".explorer .chip[data-" + attr + "]"), function (b) {
      b.setAttribute("aria-pressed", b.dataset[attr] === value ? "true" : "false");
    });
  }

  function clearAll() {
    state = { q: "", lvl: null, party: null };
    if (qInput) qInput.value = "";
    setChip("lvl", null); setChip("party", null);
    apply();
  }

  function togglePanel(p, force) {
    var pill = pillOf(p), panel = panelOf(p);
    if (!pill || !panel) return;
    var open = force !== undefined ? force : pill.getAttribute("aria-expanded") !== "true";
    pill.setAttribute("aria-expanded", open ? "true" : "false");
    panel.hidden = !open || p.hidden;
  }

  function flash(p) {
    p.classList.add("flash");
    setTimeout(function () { p.classList.remove("flash"); }, 1600);
  }

  function openFromHash() {
    var m = /^#s-(\d{1,3})$/.exec(location.hash);
    if (!m) return;
    var p = document.getElementById("s-" + m[1]);
    if (!p) return;
    if (p.hidden) clearAll();
    togglePanel(p, true);
    p.scrollIntoView({ block: "start" });
    flash(p);
  }

  var toastEl = document.getElementById("toast"), toastTimer;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.hidden = true; }, 2200);
  }

  function copyLink(btn) {
    var n = btn.dataset.sec;
    var url = location.origin + location.pathname + "#s-" + n;
    var done = function () { toast("הקישור לסעיף " + n + " הועתק"); };
    var fallback = function () {
      var box = btn.parentNode.querySelector(".copy-fallback");
      if (!box) {
        box = document.createElement("input");
        box.className = "copy-fallback";
        box.readOnly = true;
        box.setAttribute("aria-label", "קישור לסעיף " + n);
        btn.parentNode.appendChild(box);
      }
      box.value = url;
      box.focus();
      box.select();
      var st = btn.parentNode.querySelector(".copy-status");
      if (st) st.textContent = "סמנו והעתיקו";
    };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, fallback);
      } else { fallback(); }
    } catch (e) { fallback(); }
  }

  // events (delegated: section HTML is re-rendered by search highlighting)
  document.addEventListener("click", function (e) {
    var pill = e.target.closest(".lvl-pill");
    if (pill) { togglePanel(pill.closest("p.sec")); return; }
    var copy = e.target.closest(".copy-link");
    if (copy) { copyLink(copy); return; }
    var chip = e.target.closest(".explorer .chip");
    if (chip) {
      var attr = chip.dataset.lvl !== undefined ? "lvl" : "party";
      var val = chip.dataset[attr];
      state[attr] = state[attr] === val ? null : val;
      setChip(attr, state[attr]);
      apply();
      return;
    }
    if (e.target.closest("#ex-clear")) { clearAll(); return; }
    var cell = e.target.closest(".explorer .cell");
    if (cell) {
      e.preventDefault();
      var target = "#s-" + cell.dataset.sec;
      if (location.hash === target) openFromHash();
      else location.hash = target;
    }
  });

  var t;
  if (qInput) {
    qInput.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () {
        var v = norm(qInput.value.trim());
        state.q = v.length >= 2 ? v : "";
        apply();
      }, 140);
    });
  }

  window.addEventListener("hashchange", openFromHash);
  if (location.hash) openFromHash();
})();
