/* Interactive documents.
   Explorer ([data-explorer]: the constitution, the guidelines): search, agreement-level and party filters, source panels, map.
   Tracker ([data-tracker]: the decisions in the disputes document): filter by status, search, ?show=open|done.
   Both: opening the item a link points to, copying an item's link. */
(function () {
  "use strict";
  function all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function norm(s) { return s.replace(/[׳’‘`]/g, "'").replace(/[״“”]/g, '"').toLowerCase(); }

  // text that is not part of what a reader searches: buttons, agreement tags, status pills
  var SKIP = ".src-toggle, .tag, .pill, .permalink";

  function plainText(el) {
    var c = el.cloneNode(true);
    all(SKIP, c).forEach(function (x) { x.remove(); });
    return norm(c.textContent);
  }

  function unmark(el) {
    all("mark", el).forEach(function (m) { m.replaceWith(document.createTextNode(m.textContent)); });
    el.normalize();
  }

  function mark(el, q) {
    unmark(el);
    if (!q) return;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) { return n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; }
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

  function hidden(el) { return el.classList.contains("filtered-out"); }

  function onSearch(input, fn) {
    var t;
    input.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () {
        var v = norm(input.value.trim());
        fn(v.length >= 2 ? v : "");
      }, 140);
    });
  }

  function railItem(id) {
    var a = document.querySelector('.rail a[href="#' + id + '"]');
    return a ? a.parentNode : null;
  }

  function toggle(btn, force) {
    var panel = document.getElementById(btn.getAttribute("aria-controls"));
    var open = force !== undefined ? force : btn.getAttribute("aria-expanded") !== "true";
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    if (panel) panel.hidden = !open;
  }

  /* ---------- explorer ---------- */
  function Explorer(root) {
    var items = all("[data-item]", root);
    var box = root.querySelector(".explorer");
    if (!items.length || !box) return null;
    var plain = new Map();
    items.forEach(function (p) { plain.set(p, plainText(p)); });
    var state = { q: "", lvl: null, party: null };
    var input = box.querySelector('input[type="search"]');
    var statusEl = box.querySelector(".ex-status");
    var statusDefault = statusEl ? statusEl.textContent : "";
    var clearBtn = box.querySelector(".ex-clear");
    var cells = {};
    all(".cell[data-target]", box).forEach(function (c) { cells[c.dataset.target] = c; });
    var fold = box.querySelector(".map-fold");
    if (fold && window.matchMedia && matchMedia("(max-width: 640px)").matches) fold.open = false;

    // headings, with the items under each; everything else is context, set aside while filtering
    var kids = Array.prototype.slice.call(root.children), heads = [], context = [];
    kids.forEach(function (el, i) {
      var m = /^H([23])$/.exec(el.tagName);
      if (m) {
        var own = [];
        for (var j = i + 1; j < kids.length; j++) {
          var k = /^H([23])$/.exec(kids[j].tagName);
          if (k && +k[1] <= +m[1]) break;
          if (kids[j].hasAttribute("data-item")) own.push(kids[j]);
        }
        heads.push({ el: el, items: own, li: railItem(el.id) });
      } else if (!el.hasAttribute("data-item") && !el.matches(".src, .explorer, details.toc")) {
        context.push(el);
      }
    });

    function panelOf(p) {
      var b = p.querySelector(".src-toggle");
      return b ? document.getElementById(b.getAttribute("aria-controls")) : null;
    }

    function matches(p) {
      if (state.lvl && (" " + p.dataset.lvls + " ").indexOf(" " + state.lvl + " ") < 0) return false;
      if (state.party && (" " + p.dataset.parties + " ").indexOf(" " + state.party + " ") < 0) return false;
      if (state.q && plain.get(p).indexOf(state.q) < 0) return false;
      return true;
    }

    function apply() {
      var active = !!(state.q || state.lvl || state.party), shown = 0;
      items.forEach(function (p) {
        var ok = !active || matches(p);
        mark(p, ok ? state.q : "");
        p.classList.toggle("filtered-out", !ok);
        var panel = panelOf(p);
        if (panel) panel.classList.toggle("filtered-out", !ok);
        if (cells[p.id]) cells[p.id].classList.toggle("off", !ok);
        if (ok) shown++;
      });
      heads.forEach(function (h) {
        var any = !active || h.items.some(function (p) { return !hidden(p); });
        h.el.classList.toggle("filtered-out", !any);
        if (h.li) h.li.classList.toggle("filtered-out", !any);
      });
      context.forEach(function (el) { el.classList.toggle("filtered-out", active); });
      if (statusEl) {
        statusEl.textContent = active
          ? (shown ? "מוצגים " + shown + " מתוך " + items.length + " סעיפים." : "אין סעיפים שמתאימים לסינון.")
          : statusDefault;
      }
      if (clearBtn) clearBtn.hidden = !active;
    }

    function setChips(attr) {
      all(".chip[data-" + attr + "]", box).forEach(function (b) {
        b.setAttribute("aria-pressed", b.dataset[attr] === state[attr] ? "true" : "false");
      });
    }

    function clear() {
      state = { q: "", lvl: null, party: null };
      if (input) input.value = "";
      setChips("lvl"); setChips("party");
      apply();
    }

    root.addEventListener("click", function (e) {
      var t = e.target.closest(".src-toggle");
      if (t) { toggle(t); return; }
      var chip = e.target.closest(".explorer .chip");
      if (chip) {
        var attr = chip.dataset.lvl !== undefined ? "lvl" : "party";
        state[attr] = state[attr] === chip.dataset[attr] ? null : chip.dataset[attr];
        setChips(attr);
        apply();
        return;
      }
      if (e.target.closest(".ex-clear")) { clear(); if (input) input.focus(); return; }
      var cell = e.target.closest(".cell[data-target]");
      if (cell) {
        e.preventDefault();
        go(cell.dataset.target);
      }
    });
    if (input) onSearch(input, function (q) { state.q = q; apply(); });

    return {
      root: root,
      // the element a link points to: bring it back if the filter set it aside, and open an item's sources
      reveal: function (el) {
        if (!root.contains(el)) return false;
        if (hidden(el)) {
          clear();
          if (statusEl) statusEl.textContent = "הסינון נוקה כדי להציג את הסעיף המבוקש.";
        }
        if (el.hasAttribute("data-item")) {
          var b = el.querySelector(".src-toggle");
          if (b) toggle(b, true);
          return true;
        }
        return false;
      }
    };
  }

  /* ---------- decisions tracker ---------- */
  function Tracker(root) {
    var lis = all("li[data-status]", root);
    if (!lis.length) return null;
    var plain = new Map();
    lis.forEach(function (li) { plain.set(li, plainText(li)); });
    var chips = all(".chip[data-show]", root);
    var input = root.querySelector('input[type="search"]');
    var statusEl = root.querySelector(".ex-status");
    var m = /[?&]show=(open|done)(?:&|$)/.exec(location.search);
    var state = { show: m ? m[1] : "all", q: "" };
    var LABEL = { all: "", open: " פתוחות", done: " שהוכרעו" };

    function apply(updateUrl) {
      var shown = 0;
      lis.forEach(function (li) {
        var ok = (state.show === "all" || li.dataset.status === state.show) && (!state.q || plain.get(li).indexOf(state.q) >= 0);
        mark(li, ok ? state.q : "");
        li.classList.toggle("filtered-out", !ok);
        if (ok) shown++;
      });
      chips.forEach(function (c) { c.setAttribute("aria-pressed", c.dataset.show === state.show ? "true" : "false"); });
      if (statusEl) {
        statusEl.textContent = shown
          ? "מוצגות " + shown + " נקודות" + LABEL[state.show] + " מתוך " + lis.length + "."
          : "אין נקודות שמתאימות לסינון.";
      }
      if (updateUrl && window.history && history.replaceState) {
        history.replaceState(null, "", location.pathname + (state.show === "all" ? "" : "?show=" + state.show) + location.hash);
      }
    }

    root.addEventListener("click", function (e) {
      var chip = e.target.closest(".chip[data-show]");
      if (chip) { state.show = chip.dataset.show; apply(true); }
    });
    if (input) onSearch(input, function (q) { state.q = q; apply(false); });
    apply(false);

    return {
      root: root,
      reveal: function (el) {
        if (!root.contains(el)) return false;
        if (hidden(el)) {
          state = { show: "all", q: "" };
          if (input) input.value = "";
          apply(true);
          if (statusEl) statusEl.textContent = "הסינון נוקה כדי להציג את הנקודה המבוקשת.";
        }
        return el.hasAttribute("data-status");
      }
    };
  }

  var parts = all("[data-explorer]").map(Explorer).concat(all("[data-tracker]").map(Tracker)).filter(Boolean);

  /* ---------- links to items ---------- */
  function flash(el) {
    el.classList.add("flash");
    setTimeout(function () { el.classList.remove("flash"); }, 1600);
  }

  function openFromHash() {
    var id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) { return; }
    var el = id && document.getElementById(id);
    if (!el) return;
    var item = false;
    parts.forEach(function (x) { if (x.reveal(el)) item = true; });
    if (hidden(el)) return;
    el.scrollIntoView({ block: "start" });
    if (item) flash(el);
  }

  function go(id) {
    if (decodeURIComponent(location.hash.slice(1)) === id) openFromHash();
    else location.hash = id;
  }

  /* ---------- copy an item's link ---------- */
  var toastEl = document.getElementById("toast"), toastTimer;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.textContent = ""; }, 2400);
  }

  function copyLink(btn) {
    var label = btn.dataset.label || "";
    var url = location.origin + location.pathname + "#" + btn.dataset.target;
    var done = function () { toast("הקישור " + label + " הועתק"); };
    var fallback = function () {
      var box = btn.parentNode.querySelector(".copy-fallback");
      if (!box) {
        box = document.createElement("input");
        box.className = "copy-fallback";
        box.readOnly = true;
        box.setAttribute("aria-label", "קישור " + label);
        btn.parentNode.appendChild(box);
      }
      box.value = url;
      box.focus();
      box.select();
      var st = btn.parentNode.querySelector(".copy-status");
      if (st) st.textContent = "סמנו והעתיקו";
    };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(done, fallback);
      else fallback();
    } catch (e) { fallback(); }
  }

  document.addEventListener("click", function (e) {
    var copy = e.target.closest(".copy-link[data-target]");
    if (copy) copyLink(copy);
  });

  window.addEventListener("hashchange", openFromHash);
  if (location.hash) openFromHash();
})();
