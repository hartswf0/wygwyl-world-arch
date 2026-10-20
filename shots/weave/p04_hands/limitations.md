# Limitations · p04_hands

What this passage does not do, or does badly. Measured where it can be.

## Picture

- **The 1969 sky is muddy.** It is a per-pixel median of the clip's sky pixels. Where few frames show sky, it is a smooth blur. Only its top part reads as sky; the rest is masked off by the plate's sky mask. It is tagged SKY ASSEMBLED FROM ITS FRAMES because it is not a frame of the film.
- **The citizen's cut has a straight left edge.** One fixed scissor cut (the union of his per-row masks between the sky gaps) holds all 49 frames. The left side, where the ship's rail ran out of frame, is a straight line, not a silhouette. It reads as a card cut, but a better cut would follow his shoulder.
- **The citizen is partly off screen in the close shots.** The camera goes in on her hands at 1.42x; his card is cropped at the right edge then. His tag is moved onto the screen each frame (`label_fit`), so it stays wholly readable (930 of 933 tag-frames), but it is not always directly over him.
- **The plate is upscaled 1.875x** from the poem_04 keyframe, and it is held still. It is soft beside the cardboard.
- **Hand B is small and dark** while it is carried. It hangs behind hand A from A's fingertip; it can be seen, but it is not a strong silhouette at 1920 wide.
- **Her upper arm crosses her neck and hair** in the deep bows (1,358 px at the press and 1,590 px at the pinch, by raster count). Her face is not covered (hands over head: 0 px), but the bow is a stack of cards rather than a clean silhouette.
- **The far leg is rigid.** It cannot bend at the knee, so the far foot lifts and replants once during the kneel (3.69–4.84 s). Outside that step it is planted (0 px). The worst gap between the far leg's knee and the skirt's knee is 7.9 px (0.95% of her height), just under the 1% line.
- **The pats sit just short of the hands** because her arm is nearly vertical at the bottom of the bow (vertical reach 0.98 of the arm). The hands were placed a stub-width further on to keep the failure on bare ground; the staging is tight.

## Motion

- Motion is keyed by hand to her words and solved by IK. There is no physics; the dust follows a simple ballistic arc and lands.
- The camera eases between keys. It does not follow a subject automatically.

## Sound

- Every sound except her voice is synthesised (`build_sound.py`): room tone, thuds, pats, ticks, snaps, taps, a stick slide. They are placed from the logged contacts, not recorded.
- No archive audio: the clip is silent in the library.

## Process

- **The critic is scripted** (`critic.py`). It measures; it has not watched the film. No independent model or person reviewed it in this pass.
- The measured values in the clip are computed from the same display list the page draws, not from the rendered pixels (except the frame-step check and the head-visibility raster in the critic).
- The passage is proved alone. It has not been cut against p07 or any other passage.
