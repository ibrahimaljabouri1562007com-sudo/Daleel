/* ===========================================================
   مركز الدليل — home page behavior
   Mobile menu · sticky header · about accordion · scroll reveal
   =========================================================== */
(function () {
  'use strict';

  /* ---- Mobile navigation ---- */
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('mainNav');
  function closeNav() {
    nav.classList.remove('open');
    toggle.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.querySelectorAll('a:not(.disabled)').forEach(function (a) { a.addEventListener('click', closeNav); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeNav(); });
  }

  /* ---- Moving gold underline indicator (desktop nav) ---- */
  if (nav) {
    var indicator = document.createElement('span');
    indicator.className = 'nav-indicator';
    nav.appendChild(indicator);
    var current = nav.querySelector('a.active') || nav.querySelector('a:not(.disabled)');
    var moveIndicator = function (el) {
      if (!el || window.innerWidth <= 860) { indicator.style.opacity = '0'; return; }
      var nr = nav.getBoundingClientRect();
      var er = el.getBoundingClientRect();
      var inset = 10;
      indicator.style.opacity = '1';
      indicator.style.right = (nr.right - er.right + inset) + 'px';
      indicator.style.width = Math.max(0, er.width - inset * 2) + 'px';
    };
    nav.querySelectorAll(':scope > a, .nav-dd > .dd-top').forEach(function (item) {
      if (item.classList.contains('disabled')) return;
      item.addEventListener('click', function () { current = item; moveIndicator(item); });
    });
    nav.querySelectorAll('.dd-panel a').forEach(function (sub) {
      sub.addEventListener('click', function () {
        var top = sub.closest('.nav-dd').querySelector('.dd-top');
        if (top) { current = top; moveIndicator(top); }
      });
    });
    var reposition = function () { moveIndicator(current); };
    window.addEventListener('resize', reposition, { passive: true });
    window.addEventListener('load', reposition);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(reposition);
    reposition();
  }

  /* ---- Sticky header shadow ---- */
  var header = document.getElementById('siteHeader');
  function onScroll() { if (header) header.classList.toggle('scrolled', window.scrollY > 10); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- About accordion ---- */
  document.querySelectorAll('.acc-head').forEach(function (head) {
    head.addEventListener('click', function () {
      var item = head.parentElement;
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.acc-item').forEach(function (i) {
        i.classList.remove('open');
        var h = i.querySelector('.acc-head'); var ic = i.querySelector('.acc-ic');
        if (h) h.setAttribute('aria-expanded', 'false');
        if (ic) ic.textContent = '+';
      });
      if (!isOpen) {
        item.classList.add('open');
        head.setAttribute('aria-expanded', 'true');
        var ic = head.querySelector('.acc-ic'); if (ic) ic.textContent = '−';
      }
    });
  });

  /* ---- Copy-to-clipboard (contact email fallback) ---- */
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.dataset.label = btn.textContent;
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy') || '';
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(text); }
        else { fallbackCopy(text); }
      } catch (e) { fallbackCopy(text); }
      btn.textContent = btn.getAttribute('data-copied') || 'تم النسخ ✓';
      btn.classList.add('copied');
      clearTimeout(btn._t);
      btn._t = setTimeout(function () { btn.textContent = btn.dataset.label; btn.classList.remove('copied'); }, 1600);
    });
  });
  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  /* ---- Scroll reveal ---- */
  var revealEls = document.querySelectorAll('.section');
  revealEls.forEach(function (el) { el.setAttribute('data-reveal', ''); });
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }
})();

/* ============================================================
   Generalized edit-mode engine — wires EVERY [data-editable]
   section on the page (books, videos, lessons, and any future
   section) with: admin toggle, add button, delete, premium
   drag-reorder. Controls appear only in that section's edit mode.
   ============================================================ */
(function () {
  var sections = [].slice.call(document.querySelectorAll('[data-editable]'));
  if (!sections.length) return;                            // only on pages that have them

  var editingCount = 0;

  /* ---------- shared toast ---------- */
  var toastEl;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { toastEl.classList.remove('show'); }, 1800);
  }

  function refreshBar() { document.body.classList.toggle('edit-on', editingCount > 0); }

  /* ---------- wire one section ---------- */
  function initSection(section) {
    var toggle = section.querySelector('.js-edit-toggle');
    var grid = section.querySelector('.js-grid');
    if (!toggle) return;                                    // toggle wires even with 0 items
    var STORE = 'daleel_edit_' + section.id;
    var cards = function () { return grid ? [].slice.call(grid.querySelectorAll('.js-card')) : []; };
    var isOn = function () { return section.classList.contains('editing'); };

    function setEdit(on) {
      var was = isOn();
      if (on === was) { /* still sync UI on restore */ }
      section.classList.toggle('editing', on);
      toggle.setAttribute('aria-pressed', on ? 'true' : 'false');
      var lbl = toggle.querySelector('.edit-label'); if (lbl) lbl.textContent = on ? 'تم' : 'تعديل';
      var ic = toggle.querySelector('.edit-ic'); if (ic) ic.textContent = on ? '✓' : '✎';
      if (on && !was) editingCount++;
      if (!on && was) editingCount--;
      refreshBar();
      try { localStorage.setItem(STORE, on ? '1' : '0'); } catch (e) {}
    }
    toggle.addEventListener('click', function () { setEdit(!isOn()); });
    section._exit = function () { setEdit(false); };

    /* ----- premium pointer drag, scoped to THIS grid ----- */
    var drag = null, ph = null, offX = 0, offY = 0;
    var curX = 0, curY = 0, tgtX = 0, tgtY = 0, raf = 0, lastTrail = 0, tilt = 0;

    function flip(mutate) {
      var first = {};
      cards().forEach(function (el) { if (el !== drag) first[el.dataset.id] = el.getBoundingClientRect(); });
      mutate();
      cards().forEach(function (el) {
        if (el === drag) return;
        var f = first[el.dataset.id]; if (!f) return;
        var l = el.getBoundingClientRect();
        var dx = f.left - l.left, dy = f.top - l.top;
        if (dx || dy) {
          el.style.transition = 'none';
          el.style.transform = 'translate(' + dx + 'px,' + dy + 'px)';
          el.offsetWidth;
          el.style.transition = 'transform .28s cubic-bezier(.2,.7,.3,1)';
          el.style.transform = '';
        }
      });
    }

    if (grid) grid.addEventListener('pointerdown', function (e) {
      if (!isOn() || (e.button != null && e.button !== 0)) return;
      var card = e.target.closest('.js-card');
      // don't start a drag from interactive bits (delete/links) or media players
      if (!card || e.target.closest('form, a, button, video, iframe, .video-holder')) return;
      e.preventDefault();
      drag = card;
      var r = card.getBoundingClientRect();
      offX = e.clientX - r.left; offY = e.clientY - r.top;
      curX = tgtX = r.left; curY = tgtY = r.top; tilt = 0;

      ph = document.createElement('div');
      ph.className = 'book-ph';
      ph.style.width = r.width + 'px'; ph.style.height = r.height + 'px';
      grid.insertBefore(ph, card);

      card.classList.add('grabbing');
      card.style.width = r.width + 'px'; card.style.height = r.height + 'px';
      card.style.position = 'fixed'; card.style.left = '0'; card.style.top = '0';
      document.body.classList.add('dragging-active');
      try { card.setPointerCapture(e.pointerId); } catch (x) {}
      window.addEventListener('pointermove', onMove);
      window.addEventListener('pointerup', onUp, { once: true });
      loop();
    });

    var vertical = grid && grid.getAttribute('data-axis') === 'y';  // column vs row layout
    function onMove(e) {
      tgtX = e.clientX - offX; tgtY = e.clientY - offY;
      var p = vertical ? e.clientY : e.clientX, nearest = null, nd = Infinity, before = true;
      cards().forEach(function (el) {
        if (el === drag) return;
        var b = el.getBoundingClientRect();
        var c = vertical ? (b.top + b.height / 2) : (b.left + b.width / 2);
        var d = Math.abs(p - c);
        // vertical: above-center = earlier | RTL row: right-of-center = earlier
        if (d < nd) { nd = d; nearest = el; before = vertical ? (p < c) : (p > c); }
      });
      if (!nearest) return;
      var ref = before ? nearest : nearest.nextSibling;
      if (ref === ph || (ref && ref.previousSibling === ph)) return;
      if (!ref && ph === grid.lastElementChild) return;
      flip(function () { grid.insertBefore(ph, ref); });
    }

    function loop() {
      curX += (tgtX - curX) * 0.3;
      curY += (tgtY - curY) * 0.3;
      var vx = tgtX - curX;
      var tTilt = Math.max(-7, Math.min(7, vx * 0.11));
      tilt += (tTilt - tilt) * 0.18;
      if (Math.abs(tilt) < 0.04) tilt = 0;
      drag.style.transform =
        'translate3d(' + curX.toFixed(2) + 'px,' + curY.toFixed(2) + 'px,0) rotate(' +
        tilt.toFixed(2) + 'deg) scale(1.045)';

      var now = performance.now();
      if (Math.abs(vx) > 7 && now - lastTrail > 60) {
        lastTrail = now;
        var g = document.createElement('div');
        g.className = 'drag-trail';
        g.style.width = drag.offsetWidth + 'px'; g.style.height = drag.offsetHeight + 'px';
        g.style.transform = 'translate3d(' + curX.toFixed(2) + 'px,' + curY.toFixed(2) + 'px,0) scale(1.045)';
        document.body.appendChild(g);
        requestAnimationFrame(function () { g.style.opacity = '0'; });
        setTimeout(function () { g.remove(); }, 300);
      }
      raf = requestAnimationFrame(loop);
    }

    function onUp() {
      window.removeEventListener('pointermove', onMove);
      cancelAnimationFrame(raf);
      var d = drag, p = ph; drag = null;
      var pr = p.getBoundingClientRect();
      d.style.transition = 'transform .2s cubic-bezier(.2,.7,.3,1)';
      d.style.transform = 'translate(' + pr.left + 'px,' + pr.top + 'px) rotate(0deg) scale(1)';
      setTimeout(function () {
        d.classList.remove('grabbing');
        d.style.cssText = '';
        p.parentNode.insertBefore(d, p);
        p.parentNode.removeChild(p);
        document.body.classList.remove('dragging-active');
        saveOrder();
      }, 200);
    }

    function saveOrder() {
      var ids = cards().map(function (c) { return c.getAttribute('data-id'); });
      fetch(grid.getAttribute('data-reorder-url'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order: ids })
      }).then(function (r) { return r.json(); })
        .then(function (j) { toast(j && j.ok ? 'تم حفظ الترتيب' : 'تعذّر حفظ الترتيب'); })
        .catch(function () { toast('تعذّر حفظ الترتيب'); });
    }

    // restore this section's edit state (survives refresh while working)
    try { setEdit(localStorage.getItem(STORE) === '1'); } catch (e) {}
  }

  sections.forEach(initSection);

  /* ---------- global exit (top bar button + Esc) closes all ---------- */
  function exitAll() { sections.forEach(function (s) { if (s._exit) s._exit(); }); }
  var exitBtn = document.getElementById('editExit');
  if (exitBtn) exitBtn.addEventListener('click', exitAll);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && editingCount > 0) exitAll();
  });
})();

/* ============================================================
   Video poster -> click-to-play (works for file AND embed)
   ============================================================ */
(function () {
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.js-play');
    if (!btn) return;
    // slot is the poster's sibling — works in library (.video-holder) AND news (.news-media)
    var slot = btn.parentNode && btn.parentNode.querySelector('.video-slot');
    if (!slot) return;
    var type = btn.getAttribute('data-type');
    var src = btn.getAttribute('data-src');
    if (type === 'embed') {
      var sep = src.indexOf('?') > -1 ? '&' : '?';
      slot.innerHTML = '<div class="video-frame"><iframe src="' + src + sep +
        'autoplay=1" title="video" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>';
    } else {
      var v = document.createElement('video');
      v.className = 'lib-video-el'; v.controls = true; v.autoplay = true; v.src = src;
      slot.appendChild(v);
    }
    btn.remove();                                          // reveal the player
  });
})();

/* ============================================================
   Publish-video form: require a link OR a file (gentle, client-side)
   ============================================================ */
(function () {
  var form = document.querySelector('form[data-need-source]');
  if (!form) return;
  form.addEventListener('submit', function (e) {
    var url = form.querySelector('[name="url"]');
    var file = form.querySelector('[name="video"]');
    var hasUrl = url && url.value.trim() !== '';
    var hasFile = file && file.files && file.files.length > 0;
    if (!hasUrl && !hasFile) {
      e.preventDefault();
      var note = form.querySelector('.inline-err');
      if (!note) {
        note = document.createElement('div');
        note.className = 'flash flash-error inline-err';
        form.insertBefore(note, form.firstChild);
      }
      note.textContent = 'أدخل رابط فيديو أو ارفع ملفًا (أحدهما مطلوب).';
      (url || file).focus();
    }
  });
})();

/* ============================================================
   Article formatting toolbar — inserts simple markup into the
   body textarea (wraps selection for bold/highlight; prefixes
   the line for heading/quote/list). Rendered server-side.
   ============================================================ */
(function () {
  var bar = document.querySelector('.fmt-toolbar');
  if (!bar) return;
  var ta = document.getElementById(bar.getAttribute('data-target'));
  if (!ta) return;

  var WRAP = { bold: ['**', '**', 'نص عريض'], hl: ['==', '==', 'نقطة مهمّة'] };
  var PREFIX = { h: '### ', quote: '> ', list: '- ' };

  bar.addEventListener('click', function (e) {
    var btn = e.target.closest('.fmt-btn');
    if (!btn) return;
    e.preventDefault();
    var kind = btn.getAttribute('data-fmt');
    var s = ta.selectionStart, en = ta.selectionEnd, v = ta.value, sel = v.slice(s, en);

    if (WRAP[kind]) {
      var w = WRAP[kind], text = sel || w[2];
      ta.value = v.slice(0, s) + w[0] + text + w[1] + v.slice(en);
      ta.focus();
      ta.selectionStart = s + w[0].length;
      ta.selectionEnd = s + w[0].length + text.length;
    } else if (PREFIX[kind]) {
      var lineStart = v.lastIndexOf('\n', s - 1) + 1;
      // avoid doubling an existing prefix
      if (v.slice(lineStart).indexOf(PREFIX[kind]) !== 0) {
        ta.value = v.slice(0, lineStart) + PREFIX[kind] + v.slice(lineStart);
        en += PREFIX[kind].length;
      }
      ta.focus();
      ta.selectionStart = ta.selectionEnd = en;
    }
  });
})();

/* ============================================================
   Auto-grow textareas — expand downward as text is typed so all
   lines (and Arabic dots) stay visible; Enter/Shift+Enter work.
   ============================================================ */
(function () {
  function grow(ta) { ta.style.height = 'auto'; ta.style.height = (ta.scrollHeight + 4) + 'px'; }
  var tas = document.querySelectorAll('.book-form textarea');
  if (!tas.length) return;
  tas.forEach(function (ta) {
    grow(ta);
    ta.addEventListener('input', function () { grow(ta); });
  });
  // recalc once fonts settle (Arabic metrics)
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { tas.forEach(grow); });
})();

/* ============================================================
   Forms: pressing Enter in a single-line field must NOT submit
   (prevents accidental submit / error page). Textareas keep
   Enter & Shift+Enter for new lines.
   ============================================================ */
(function () {
  document.querySelectorAll('.book-form').forEach(function (form) {
    form.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter') return;
      var t = e.target;
      if (t.tagName === 'INPUT' && t.type !== 'submit' && t.type !== 'button') {
        e.preventDefault();           // don't submit from a single-line input
      }
    });
  });
})();
