// Extension registry for the Cut-Out Suite: small, separate modules add actions, fx kinds, prop cards and join
// kinds without rewriting the shared solver / renderer. A scene names the modules it needs in `extensions`
// (paths relative to shots/suite/), and the page imports them before it solves.
//
//   EXT.fx[kind](g, base, fx, F, cv, helpers)          draw a set piece / code layer (called from drawFx)
//   EXT.joins[kind](g, base, j, s, F, cv, probe, helpers) draw a WEAVE join kind (called from drawJoin)
//   EXT.props[kind](g, p, s, F) -> true if drawn       a held prop card (called from drawProps, at the hand)
//   EXT.frame.push(fn(tr, t, B) -> {lean, headPitch, drop, card} | null)   per-frame action channels (solver);
//        card: a replacement-card id to show while standing (a 'pose' beat), used by pickCard; alpha: multiplies the puppet's alpha
//   EXT.preload.push(async fn(scene, set, ctx, A))     load images before the first frame
export const EXT = { fx: {}, joins: {}, props: {}, frame: [], preload: [], loaded: new Set() };

export async function loadExtensions(list) {
  for (const m of list || []) {
    if (EXT.loaded.has(m)) continue;
    await import(new URL('../' + m.replace(/^\.?\//, ''), import.meta.url).href);
    EXT.loaded.add(m);
  }
}

// summed per-frame modifiers from every registered action channel
export function extFrame(tr, t, B) {
  let out = null;
  for (const fn of EXT.frame) {
    const m = fn(tr, t, B); if (!m) continue;
    out = out || { lean: 0, headPitch: 0, drop: 0, card: null, alpha: 1 };
    out.lean += m.lean || 0; out.headPitch += m.headPitch || 0; out.drop += m.drop || 0; if (m.card) out.card = m.card; if (m.alpha != null) out.alpha *= m.alpha;
  }
  return out;
}
