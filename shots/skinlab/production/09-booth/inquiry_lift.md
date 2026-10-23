# Inquiry: why the lift is not a lift (v5, f88–f125)

## Observed (critic, v5 frames; confirmed here frame by frame)
- f93→f94: in one drawn step the handset goes from the cradle side of the face to behind the ear; the arm changes shape (forearm forward → upper arm horizontal, forearm up behind the head); the cord disappears.
- Three apparently different side heads: f78–93, f94–115, f116–125.
- The torso grows by about 13% at f93→94.
- f115→116: the handset jumps again, from the back of the head to the front of the face, and the cord reappears.
- This is the second time the hand-to-ear has failed (the lab proof had the phone hand behind the head too).

## The explanation guiding the work so far
The lift is a timing problem. If it is retimed so the hand lands on "I call", the in-between is short but acceptable on twos.

**Assumption under it:** the drawn figure between two poses is the in-between of the two skeletons. The cards are rigid and are only moved by the solve, so cards, scale, stack and prop placement stay continuous.

## Alternative explanation (implies a different repair)
The figure is not continuous: several separate code paths switch at segment boundaries.
1. **Card scale.** In fit mode a card's scale is recomputed every frame from the 3D length of its bone. My pose edits change those lengths: the 'reach' upright blend (75% of a straight trunk lerped into a bowed one), the neck clamp, the blends and the held-to-head joints. So one card is drawn at different sizes, which reads as different drawings.
2. **Handset placement.** 'lift lands' uses hold_to_head without an aimed hand. 'turn out' and 'in tears' use an aimed hand with an over-the-head stack. So the handset lands in two different places.
3. **Cord.** The cord is drawn behind the poet until a segment declares cord_over, then in front. When the handset is at the near ear, the cord's end is behind the body, so it disappears.
4. **In-between count.** The 4-frame blend on twos gives only two drawn in-betweens, and the second is already 65% of the way.

If this is right, retiming cannot fix it. The repair is to make each of these paths continuous.

## Test that separates them
Log, per frame for f84–f120 of v5: the head card id and scale, the torso scale, the phone hand's role and card, the pelvis screen x, and the handset state.

**Result (v5):**
- The head is one card throughout (`master/left`), but its scale moves 0.879 → 0.970 → 1.003 → 0.988 → 0.902 across f92, f94, f96, f116 and f120. That is 14%: the "three heads" are one card at three sizes.
- The torso scale moves 0.363 → 0.369.
- The hand role is near in every frame. The hand card swaps once, at the grab (open → grip, which is intended).
- The pelvis screen x does not jump at f94 (837 → 836).

So the alternative holds:
- The pops are scale pops from fit mode under pose edits.
- The handset jumps where the hold code path changes (f94: blend done; f116: segment with an aimed hand and over-head stack).
- The cord disappears when it is drawn behind the body.
- Timing is not the cause.

## Staging perspective
**Question:** is a profile lift from a wall hook the right action, or should the receiver be lifted from a cradle at chest height toward the ear on the camera side?

**Profile from the hook (kept):** in v5 f84–f93 the profile reach reads. The hand meets the handset in front of the face, in silhouette, against the lit back panel, and the near hand carries it. Turning the body toward the camera for the lift would bring back the foreshortening problem: a forward reach cannot be drawn with rigid cards, as v1–v2 showed. The camera-side ear in profile is the near ear, so the handset can stay in front of the head the whole time. That needs the stack override (arm, hand and handset over the head) from the grab on, not only after the turn.

## Repairs made (v6)
- **Rigid card scale.** Every card is drawn at one scale for the whole passage: its bone's length in the contract's proportions, read once from the neutral pose. Heads are matched across views by their painted height, so all three heads have the same painted height. Blends, clamps and held hands can no longer resize a card.
- **One hand pose from the grab to the end.** The same head-relative hold (the hand at the cheek, aimed at the ear) is used in 'lift lands', 'turn out' and 'in tears', with arm, hand and handset over the head in every one. The lift blend is 6 frames, so on twos there are three drawn positions between contact and the ear.
- **Cord in front from the grab on.** The cord is drawn over the figure from the grab to the end, so it runs continuously from the phone body to the handset.
- **Trunk straightening without shrinking.** The 'reach' upright is applied at full weight to the trunk, so its lengths are exact. The look-down is a head-only nod with the head's offsets renormalised.
