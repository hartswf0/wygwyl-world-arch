/* One source scene, one presentation owner across the entrance and design room.
 * Crops, grades, posters and separated layers keep the same source identity.
 * Add a new source or use text when a scene is already allocated. Never recycle it.
 */
(function (root) {
  'use strict';
  var plan = [
    { owner: 'entrance', scene: 'arcade', kind: 'stage', page: 'index.html' },
    { owner: 'construction', scene: 'cortex', kind: 'layers', page: 'index.html' },
    { owner: 'route-weave', scene: 'commons', kind: 'poster', page: 'index.html' },
    { owner: 'route-foundry', scene: 'temple', kind: 'poster', page: 'index.html' },
    { owner: 'route-worldtext', scene: 'haze', kind: 'poster', page: 'index.html' },
    { owner: 'chapter-foundry', scene: 'overseer', kind: 'chapter', tool: 'worldfoundry', page: 'index.html' },
    { owner: 'chapter-weave', scene: 'hive', kind: 'chapter', tool: 'weave', page: 'index.html' },
    { owner: 'chapter-score', scene: 'cenotaph', kind: 'chapter', tool: 'wagstack', page: 'index.html' },
    { owner: 'design-cover', scene: 'moon', kind: 'poster', page: 'design-prompts.html' }
  ];

  function validatePlan(entries, manifest) {
    var owners = Object.create(null), scenes = Object.create(null), assets = Object.create(null), errors = [];
    entries.forEach(function (entry) {
      if (owners[entry.owner]) errors.push('Repeated owner: ' + entry.owner);
      owners[entry.owner] = true;
      var scene = manifest[entry.scene];
      if (!scene || !scene.sid || !scene.poster) { errors.push('Missing source for ' + entry.owner); return; }
      var identity = scene.sourceSid || scene.sid;
      if (scenes[identity]) errors.push('Scene ' + identity + ' belongs to both ' + scenes[identity] + ' and ' + entry.owner);
      else scenes[identity] = entry.owner;
      [scene.poster].concat((scene.planes || []).map(function (plane) { return plane.src; })).forEach(function (src) {
        var url = new URL(src, 'https://hartswf0.github.io/wygwyl-world-arch/');
        url.search = ''; url.hash = '';
        var canonical = url.href;
        if (assets[canonical] && assets[canonical] !== entry.owner) errors.push('Image ' + canonical + ' belongs to both ' + assets[canonical] + ' and ' + entry.owner);
        else assets[canonical] = entry.owner;
      });
    });
    return errors;
  }

  var manifest = root.LANDING || {}, errors = validatePlan(plan, manifest), claimed = Object.create(null);
  function entryFor(owner) { return plan.find(function (entry) { return entry.owner === owner; }); }
  function refuse(element, message) {
    if (element) element.hidden = true;
    if (root.console) root.console.error('[WYGWYL visual integrity] ' + message);
    return null;
  }
  function claim(owner, element) {
    if (errors.length) return refuse(element, errors.join('; '));
    var entry = entryFor(owner);
    if (!entry || !element) return refuse(element, 'Unallocated presentation: ' + owner);
    var scene = manifest[entry.scene], identity = scene.sourceSid || scene.sid, previous = claimed[identity];
    if (previous && previous.element !== element) return refuse(element, 'Repeated presentation of ' + identity + ' at ' + owner);
    claimed[identity] = { owner: owner, element: element };
    element.dataset.sceneOwner = owner;
    element.dataset.sceneId = identity;
    element.dataset.sceneKey = entry.scene;
    return scene;
  }
  function mountPosters(scope) {
    Array.from(scope.querySelectorAll('img[data-scene-owner]')).forEach(function (image) {
      var scene = claim(image.dataset.sceneOwner, image);
      if (scene) image.src = scene.poster;
    });
  }
  root.LANDING_MEDIA = Object.freeze({
    plan: Object.freeze(plan.map(function (entry) { return Object.freeze(entry); })),
    validatePlan: validatePlan,
    entry: entryFor,
    claim: claim,
    mountPosters: mountPosters
  });
})(window);
