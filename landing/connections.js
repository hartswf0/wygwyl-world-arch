(function () {
  'use strict';

  function initConnections() {
    var worlds = document.getElementById('worlds');
    var tabList = document.getElementById('routeTabs');
    var tabs = tabList ? Array.from(tabList.querySelectorAll('[data-route-tab]')) : [];
    var panels = worlds ? Array.from(worlds.querySelectorAll('[data-route-panel]')) : [];
    var showAllButton = document.getElementById('routeShowAll');
    var poemSelect = document.getElementById('routePoem');
    var contextNote = document.getElementById('routeContextNote');
    var reading = document.getElementById('worldReading');
    var readingStatus = document.getElementById('readingStatus');
    var film = document.getElementById('vid');
    var poemButtons = Array.from(document.querySelectorAll('.wag-pbtn'));
    var resetButton = document.getElementById('wagReset');
    var routeLinks = Array.from(document.querySelectorAll('a[data-poem-route]'));
    var activeRoute = 'build';
    var showAllRoutes = false;
    var syncingStrip = false;
    var readingLabel = 'Poem 01 · published original reading';
    var routeNames = tabs.map(function (tab) { return tab.getAttribute('data-route-tab'); });

    function pauseReading() {
      if (reading && !reading.paused) reading.pause();
    }

    function setReadingStatus(message) {
      if (readingStatus) readingStatus.textContent = message;
    }

    function replaceAddress(url) {
      try {
        var address = url.pathname + url.search + url.hash;
        if (address !== location.pathname + location.search + location.hash) {
          history.replaceState(history.state, '', address);
        }
      } catch (error) {
        // Navigation and controls still work in previews without history access.
      }
    }

    function panelFor(name) {
      return panels.find(function (panel) {
        return panel.getAttribute('data-route-panel') === name;
      });
    }

    function hashTarget() {
      if (!location.hash) return null;
      var id;
      try { id = decodeURIComponent(location.hash.slice(1)); }
      catch (error) { return null; }
      var target = document.getElementById(id);
      if (!target || !worlds || !worlds.contains(target)) return null;
      var panel = target.closest('[data-route-panel]');
      if (!panel || panels.indexOf(panel) === -1) return null;
      var name = panel.getAttribute('data-route-panel');
      return routeNames.indexOf(name) === -1 ? null : {name: name, target: target};
    }

    function renderRoutes() {
      if (!tabList || !panels.length) return;
      worlds.setAttribute('data-route-mode', showAllRoutes ? 'all' : 'tabs');
      // The all-routes view is ordinary navigation, not a tablist with several
      // simultaneously visible tabpanels. Restore tab semantics on selection.
      if (showAllRoutes) tabList.removeAttribute('role');
      else tabList.setAttribute('role', 'tablist');
      if (showAllRoutes) tabList.removeAttribute('aria-orientation');
      else tabList.setAttribute('aria-orientation', 'horizontal');
      tabs.forEach(function (tab) {
        var name = tab.getAttribute('data-route-tab');
        var selected = name === activeRoute;
        var panel = panelFor(name);
        if (!tab.id) tab.id = 'route-tab-' + name;
        if (panel) tab.setAttribute('aria-controls', panel.id);
        if (showAllRoutes) {
          tab.removeAttribute('role');
          tab.removeAttribute('aria-selected');
        } else {
          tab.setAttribute('role', 'tab');
          tab.setAttribute('aria-selected', String(selected));
        }
        tab.tabIndex = showAllRoutes || selected ? 0 : -1;
        tab.classList.toggle('is-active', !showAllRoutes && selected);
      });
      panels.forEach(function (panel) {
        var name = panel.getAttribute('data-route-panel');
        var tab = tabs.find(function (item) { return item.getAttribute('data-route-tab') === name; });
        panel.hidden = !showAllRoutes && name !== activeRoute;
        panel.setAttribute('role', showAllRoutes ? 'region' : 'tabpanel');
        if (tab) panel.setAttribute('aria-labelledby', tab.id);
      });
      if (showAllButton) {
        showAllButton.setAttribute('aria-pressed', String(showAllRoutes));
        showAllButton.setAttribute('aria-expanded', String(showAllRoutes));
        showAllButton.textContent = showAllRoutes ? 'Show selected route' : 'Show all routes';
      }
      if (!showAllRoutes && activeRoute !== 'listen') pauseReading();
    }

    function selectRoute(name, focusTab, updateHash) {
      if (routeNames.indexOf(name) === -1 || !panelFor(name)) return;
      activeRoute = name;
      showAllRoutes = false;
      renderRoutes();
      if (updateHash) {
        var url = new URL(location.href);
        url.hash = 'route-' + name;
        replaceAddress(url);
      }
      if (focusTab) {
        var tab = tabs.find(function (item) { return item.getAttribute('data-route-tab') === name; });
        if (tab) tab.focus();
      }
    }

    function revealHash(scroll) {
      var match = hashTarget();
      if (!match) return false;
      selectRoute(match.name, false, false);
      if (scroll && typeof match.target.scrollIntoView === 'function') {
        match.target.scrollIntoView({block: 'start'});
      }
      return true;
    }

    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function (event) {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button > 0) return;
        event.preventDefault();
        selectRoute(tab.getAttribute('data-route-tab'), false, true);
      });
      tab.addEventListener('keydown', function (event) {
        var next = index;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
        else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index + tabs.length - 1) % tabs.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = tabs.length - 1;
        else if (event.key !== ' ' && event.key !== 'Enter') return;
        event.preventDefault();
        selectRoute(tabs[next].getAttribute('data-route-tab'), true, true);
      });
    });

    if (showAllButton) {
      showAllButton.hidden = false;
      showAllButton.setAttribute('aria-controls', panels.map(function (panel) { return panel.id; }).join(' '));
      showAllButton.addEventListener('click', function () {
        showAllRoutes = !showAllRoutes;
        renderRoutes();
      });
    }
    window.addEventListener('hashchange', function () { revealHash(true); });

    function normalizePoem(value) {
      var text = String(value || '');
      return /^(0?[1-9]|1[0-4])$/.test(text) ? String(Number(text)).padStart(2, '0') : '';
    }

    routeLinks.forEach(function (link) {
      if (!link.hasAttribute('data-route-base')) {
        link.setAttribute('data-route-base', link.getAttribute('href') || '');
      }
    });

    function contextualHref(base, type, poem) {
      if (!poem) return base;
      var hashIndex = base.indexOf('#');
      var hash = hashIndex < 0 ? '' : base.slice(hashIndex);
      var beforeHash = hashIndex < 0 ? base : base.slice(0, hashIndex);
      var queryIndex = beforeHash.indexOf('?');
      var path = queryIndex < 0 ? beforeHash : beforeHash.slice(0, queryIndex);
      var query = new URLSearchParams(queryIndex < 0 ? '' : beforeHash.slice(queryIndex + 1));
      if (type === 'dossier') {
        var prefix = path.match(/^(.*shots\/poems\/)[^/]*$/);
        return (prefix ? prefix[1] : 'shots/poems/') + poem + '.html';
      }
      if (type === 'wag') {
        // A global time overrides the poem in WAG. Only a matching line stays.
        query.delete('t');
        var line = query.get('line');
        if (line && !new RegExp('^' + poem + '_L[0-9]+$').test(line)) query.delete('line');
      } else if (type === 'shots') {
        ['world', 'kind', 'q'].forEach(function (key) { query.delete(key); });
        hash = '';
      } else if (type === 'moviemap') {
        ['e', 'i', 'd', 'v'].forEach(function (key) { query.delete(key); });
      } else {
        return base;
      }
      query.set('poem', poem);
      return path + '?' + query.toString() + hash;
    }

    function setPoem(value, syncStrip, updateURL) {
      var poem = normalizePoem(value);
      if (poemSelect) poemSelect.value = poem;
      if (syncStrip && !syncingStrip) {
        var button = poem ? poemButtons.find(function (item) {
          return normalizePoem(item.getAttribute('data-p')) === poem;
        }) : resetButton;
        if (button) {
          syncingStrip = true;
          try { button.click(); }
          finally { syncingStrip = false; }
        }
      }
      routeLinks.forEach(function (link) {
        link.setAttribute('href', contextualHref(link.getAttribute('data-route-base'), link.getAttribute('data-poem-route'), poem));
      });
      if (contextNote) {
        contextNote.textContent = poem
          ? 'Poem ' + poem + ' · score, shots, street view and production brief.'
          : 'All poems · original study views.';
      }
      if (updateURL) {
        var url = new URL(location.href);
        if (poem) url.searchParams.set('poem', poem);
        else url.searchParams.delete('poem');
        replaceAddress(url);
      }
    }

    if (poemSelect) poemSelect.addEventListener('change', function () { setPoem(poemSelect.value, true, true); });
    poemButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        if (!syncingStrip) setPoem(button.getAttribute('data-p'), false, true);
      });
    });
    function resetContext() { if (!syncingStrip) setPoem('', false, true); }
    if (resetButton) resetButton.addEventListener('click', resetContext);
    document.addEventListener('wygwyl:poem-reset', resetContext);
    window.addEventListener('popstate', function () {
      setPoem(new URLSearchParams(location.search).get('poem'), true, false);
      revealHash(true);
    });

    if (reading) {
      reading.preload = 'none';
      reading.autoplay = false;
      reading.loop = false;
      setReadingStatus(readingLabel);
      reading.addEventListener('playing', function () {
        if (film && !film.paused) film.pause();
        setReadingStatus('Playing · ' + readingLabel);
      });
      reading.addEventListener('pause', function () {
        setReadingStatus((reading.ended ? 'Finished · ' : 'Paused · ') + readingLabel);
      });
      reading.addEventListener('ended', function () { setReadingStatus('Finished · ' + readingLabel); });
      reading.addEventListener('error', function () {
        setReadingStatus('The reading could not load. Use the source recording link.');
      });
      if (film) film.addEventListener('play', pauseReading);
      window.addEventListener('pagehide', pauseReading);
    }

    if (panels.length && tabs.length) {
      if (routeNames.indexOf(activeRoute) === -1) activeRoute = routeNames[0];
      if (!revealHash(true)) renderRoutes();
    }
    var requestedPoem = normalizePoem(new URLSearchParams(location.search).get('poem'));
    var pressed = poemButtons.find(function (button) { return button.getAttribute('aria-pressed') === 'true'; });
    var initialPoem = requestedPoem || normalizePoem(poemSelect && poemSelect.value) || normalizePoem(pressed && pressed.getAttribute('data-p'));
    setPoem(initialPoem, Boolean(initialPoem), Boolean(requestedPoem));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initConnections, {once: true});
  else initConnections();
})();
