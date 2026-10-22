"""Scene recipes: per scene, a camera, 2-4 ensembles placed by depth (k: 1 = the subject's distance), the cast
(one focal action), extras as a group, props the scene uses, and where the one archive still hangs.
Composition rules: STAGING.md. Poses are 'sheet:slug' references into the cut catalog."""

SCENES = {
    # ───────── 09 Yet, Heard ─────────
    '09.0': dict(   # The EX in the crowd: he reaches through the crowd, the EX's back under the pink door
        shot='MWS', cam=150,
        ens=[('ens.street.club_sidewalk', dict(k=1.55, x=860)),
             ('ens.crowd.club', dict(k=1.8, x=1330, skip=['dancer 1']))],
        cast=[dict(who='poet', pose='poet.09.main-poses:falter-at-shoulder-contact', x=430, k=1.0, focal=True),
              dict(who='ex', role='ex', pose='poet.08.main-poses:08-ex-strictly-walks-back-away-with-both-hands-p', x=805, k=1.85)],
        archive='ens.street.club_sidewalk:archive', action='ACT-001__man'),
    '09.1': dict(   # Walking toward the moon: two backs side by side, the quay lip converging on the paper moon
        shot='WS', cam=165,
        ens=[('ens.sky.harbour_night', {}),
             ('ens.harbour.quay', dict(k=1.75, x=760)),
             ('ens.props.notice_board', dict(k=1.25, x=250))],
        cast=[dict(who='poet', pose='poet.14.exit:1-stand', x=1050, k=1.18, focal=True),
              dict(who='ex', role='ex', pose='poet.08.main-poses:08-ex-strictly-walks-back-away-with-both-hands-p', x=1150, k=1.12)],
        archive='ens.props.notice_board:archive', action='ACT-001__man'),
    '09.2': dict(   # Suitcases at the booth: camera at suitcase height, the EX zips the case, the booth glows behind
        shot='WS', cam=45,
        ens=[('ens.sky.harbour_night', {}),
             ('ens.harbour.quay', dict(k=2.6, x=700, skip=['ladder', 'lamp R'])),
             ('ens.phone_booth.quay', dict(k=1.55, x=1260))],
        cast=[dict(who='poet', pose='poet.09.main-poses:hang-up-2', x=1100, k=1.45),
              dict(who='ex', role='ex', pose='poet.09.main-poses:ex-zips', x=600, k=1.0, f=.6, focal=True)],
        props=[dict(ref='09.props.suitcases-notice:closed-card', x=380, k=.82, h_cm=72, label='black hard case')],
        archive=None, action='ACT-024__man'),
    '09.3': dict(   # The call to Mother: her lamplit room, the corded phone on the side table; through her window the lit booth where he calls
        shot='MWS', cam=150,
        ens=[('ens.room.mother', dict(k=1.25, x=620))],
        cast=[dict(who='poet', pose='poet.09.main-poses:phone-palm', portal=('ens.room.mother', 'window wall', (.7, .9, .26)), label='poet in the booth, seen through her window'),
              dict(who='woman', role='woman', pose='woman.13.window-action:stand-small-scale-front-hand-lifted', slot='ens.room.mother:seated', dx=90, focal=True,
                   label='MOTHER on the line (stand-in card: woman.13 until a mother_cardigan card is cut)')],
        archive='ens.room.mother:archive', action=False, focal_note='the corded phone ringing beside the empty armchair'),
    '09.4': dict(   # Father and son to the inner harbour: walking away along the kerb light toward the dawn
        shot='WS', cam=165,
        ens=[('ens.harbour.dawn_sky', {}),
             ('ens.harbour.quay_path_east', dict(k=1.7, x=820)),
             ('ens.props.notice_board', dict(k=1.2, x=230))],
        cast=[dict(who='parents', role='father', pose='poet.14.exit:1-stand', x=1130, k=1.26, h_cm=183, flip=True, op=.6,
                   label='FATHER, summoned pale from the east (stand-in back card until an elder_father_coat card is cut)'),
              dict(who='poet', pose='poet.14.exit:1-stand', x=1030, k=1.2, focal=True, label='the son walking east beside him')],
        archive='ens.props.notice_board:archive', action='ACT-001__man'),
    '09.5': dict(   # The EX turns to haze: frontal two-shot at the booth curb, the EX's back dissolving, POET alone under the lamp
        shot='WS', cam=150,
        ens=[('ens.sky.harbour_night', {}),
             ('ens.harbour.quay', dict(k=2.3, x=600, skip=['ladder', 'lamp R'])),
             ('ens.phone_booth.quay', dict(k=1.5, x=1040))],
        cast=[dict(who='poet', pose='poet.08.main-poses:wince-standing-still-on-with-the-shoulders-beat-', x=1230, k=1.32, focal=True),
              dict(who='ex', role='ex', pose='poet.08.main-poses:08-ex-strictly-walks-back-away-with-both-hands-p', x=560, k=1.15, op=.55)],
        props=[dict(ref='07.fx.party-haze:amber-wash-card-a', x=560, k=1.14, h_cm=120, y_cm=40, op=.55, blend='screen', label='the orange haze taking him'),
               dict(ref='11.props.parked-motorcycle:part-1', x=250, k=1.9, h_cm=105, op=.45, label='the bike already at the kerb in the dark (10)')],
        archive=None, action='ACT-024__man'),
}
