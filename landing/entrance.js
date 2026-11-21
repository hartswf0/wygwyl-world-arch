(function () {
  'use strict';
  var list = document.getElementById('tools');
  var input = document.getElementById('toolSearch');
  var count = document.getElementById('toolCount');
  var empty = document.getElementById('toolEmpty');
  var rows = Array.from(list.children);
  function filterTools() {
    var query = input.value.toLocaleLowerCase().trim();
    var shown = 0;
    rows.forEach(function (row) {
      row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
      if (!row.hidden) shown++;
    });
    count.textContent = shown + ' of ' + rows.length + ' tools';
    empty.hidden = shown !== 0;
  }
  input.addEventListener('input', filterTools);
  filterTools();

  // Open the directory for direct URLs and for the always-visible navigation link.
  function revealDirectory() {
    document.getElementById('toolDirectory').open = true;
  }
  document.querySelectorAll('a[href="#directory"]').forEach(function (link) {
    link.addEventListener('click', revealDirectory);
  });
  if (location.hash === '#directory') revealDirectory();

  var poemButtons = Array.from(document.querySelectorAll('.wag-pbtn'));
  poemButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      poemButtons.forEach(function (other) {
        other.setAttribute('aria-pressed', String(other === button));
      });
    });
  });
  document.getElementById('wagReset').addEventListener('click', function () {
    poemButtons.forEach(function (button) { button.setAttribute('aria-pressed', 'false'); button.style.outline = ''; });
    document.getElementById('wagActivePoemLabel').textContent = 'All 14 Poems (00:00–24:00)';
    document.querySelectorAll('a.wag-ctx').forEach(function (a) {
      var original = a.getAttribute('data-base-href');
      if (original) a.setAttribute('href', original);
    });
    document.dispatchEvent(new Event('wygwyl:poem-reset'));
  });

  // Keep keyboard focus inside the existing modal surfaces while they are open.
  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Tab') return;
    var modal = document.querySelector('.exp-modal.on, .sheet.on');
    if (!modal) return;
    var controls = Array.from(modal.querySelectorAll('a[href],button,input,[tabindex="0"]')).filter(function (node) { return node.getClientRects().length && !node.disabled; });
    if (!controls.length) return;
    var first = controls[0], last = controls[controls.length - 1];
    if (event.shiftKey && (document.activeElement === first || !modal.contains(document.activeElement))) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && (document.activeElement === last || !modal.contains(document.activeElement))) { event.preventDefault(); first.focus(); }
  });
})();
