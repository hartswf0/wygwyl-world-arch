"""Generation prompts for every Kit 3 sheet: style + identity + the sheet's job + the template rules.

    python3 shots/arena/parts/kit3/prompts.py      # writes kit3/prompts.json

Each prompt is meant to go to an image model together with its template PNG (kit3/out) as a
layout / control image, and the character's reference images. The template, not the model,
decides where every brad is.
"""
import json, os
from kit import CHARS, HAND_SHAPES, EYES, BROWS, MOUTHS, HEAD_VIEWS, FEET

HERE = os.path.dirname(os.path.abspath(__file__))

STYLE = ("Hand-painted cut-out puppet parts for a paper-puppet stop-motion film. Every part is a separate flat card cut "
         "from corrugated cardboard: gouache paint with confident ink linework, the cardboard's flutes faintly visible "
         "through the paint, and a thin raw kraft-brown cut edge (2-3 px) all round each card. Brass split-pin brads "
         "where the template marks them. Shot flat-on and orthographic, soft even light, no cast shadows, no "
         "perspective. Pure white background. Cards never touch or overlap. No text, labels, crosses, grid or dashed "
         "lines in the output.")

TEMPLATE = ("Use the attached template as the exact layout: paint one card inside each grey ghost shape, the same "
            "position, size and orientation, filling the ghost and staying inside its dashed outline. Put a brass brad "
            "exactly on every green cross. The red cross marks where the next card pins: it must fall inside this "
            "card's rounded end, never on its edge. The 10 cm ruler sets the scale for the whole sheet.")

IDENTITY = {
    'man': ("THE MAN: a Black man in his thirties, dark brown skin, short faded haircut, full well-groomed beard. "
            "Outfit, as in the reference photos: a black matte technical track jacket with a stand-up funnel collar, "
            "a centre zip, thin red piping running from each shoulder seam down the chest toward the side seams, "
            "elastic cuffs and an elastic hem; black track trousers with an elastic waist and a drawstring, slightly "
            "tapered; black leather Chelsea boots. His black sunglasses are a separate plug-in card, never painted onto "
            "the head. Panel B: his two tracksuit photos, then his cardboard head front and side (no glasses)."),
    'poet': ("THE POET: a Black woman, dark brown skin, a full rounded afro, calm and open face. A teal dress with a "
             "gold floral print: a fitted sleeveless bodice and an A-line skirt to the knee; bare brown arms with one "
             "slim gold bangle; flat dark teal shoes. Panel B: her current cards, for the dress print and colours. She needs her eyes OPEN: her only head today is a profile with closed eyes."),
    'dot': ("DOT, THE LITTLE ONE: a child-sized crash-test dummy, 105 cm, painted mustard yellow on cardboard: a "
            "round head with black-and-yellow quartered crash targets on both sides and a small red bow on top, a "
            "segmented body with brass brads, a red stripe down the chest, mitten hands, flat little feet. Her face "
            "is NOT painted on: it is drawn by code from the motion bank (eyes, brows, mouth), so the head plate stays "
            "blank yellow."),
}


def prompts():
    out = {'style': STYLE, 'template_rules': TEMPLATE, 'sheets': []}

    def add(cid, sheet, job, template=True, extra=''):
        txt = ' '.join(x for x in (STYLE, IDENTITY[cid], job, TEMPLATE if template else '', extra) if x)
        out['sheets'].append({'id': f'{cid}.{sheet}', 'character': cid, 'sheet': sheet,
                              'template': f'out/{cid}.{sheet}.template.png' if template else None, 'job': job, 'prompt': txt})

    for cid, C in CHARS.items():
        for view in ('front', 'threequarter', 'back', 'profile'):
            facing = {'front': 'facing the viewer', 'threequarter': 'turned three-quarters to screen right',
                      'back': 'seen from directly behind (show the back of the jacket or dress: no zip, no buttons, no face)',
                      'profile': 'in strict profile facing screen right'}[view]
            job = (f"SHEET {cid}.body.{view}: the body cards {facing}. The torso card"
                   + (" (the jacket, the elastic hem at the bottom; the hip brads sit just above the hem)" if cid == 'man' else
                      " (the sleeveless bodice; plus a separate skirt card that hangs from the waist brads)" if cid == 'poet' else
                      " (the dummy chest with its red stripe)")
                   + ", both upper arms, both forearms with their cuffs, both thighs (each thigh card's top is a rounded seat that "
                   "tucks under the hem: there is NO separate pelvis or shorts card), both shins and both feet. Each card ends in a "
                   "round disc at every brad, so it can turn on the brad without a gap.")
            add(cid, f'body.{view}', job)
        hv = ', '.join(HEAD_VIEWS)
        add(cid, 'heads', f"SHEET {cid}.heads.blank: five head plates ({hv}), each with its neck tab. The plates are BLANK: "
            "no eyes, no brows, no mouth, no glasses; keep the skin, the hair, the ears, the nose and the beard"
            + (" (the afro is part of the plate and, in the back view, covers the whole head)" if cid == 'poet' else '')
            + ". The face plug-ins are pasted onto the marked eye and mouth anchors later.")
        for view in ('front', 'profile'):
            add(cid, f'face.{view}', f"SHEET {cid}.face.{view}: the face plug-ins, {view} view, each a small separate card "
                f"centred on its cross: one blank head plate at left; EYES (a pair per cell): {', '.join(EYES)}; "
                f"BROWS (a pair per cell): {', '.join(BROWS)}; MOUTHS: {', '.join(MOUTHS)}. Paint the features in the head's "
                "own style and skin tone, each on a skin-coloured card just larger than the feature so it sits on the plate "
                "without a seam. Eye whites and irises are painted; the pupils may be left out (code can draw them so the "
                "gaze follows the motion)."
                + (" Also one pair of black sunglasses, front and profile, as their own card." if cid == 'man' else ''),
                template=cid != 'dot', extra='' if cid != 'dot' else
                'Dot needs no painted features: this sheet is drawn by code (dummyhead.py).')
        add(cid, 'hands', f"SHEET {cid}.hands.R: the RIGHT hand only (the left is its mirror), {len(HAND_SHAPES)} shapes "
            f"({', '.join(HAND_SHAPES)}), each from the back and from the palm. Every hand is painted on a small cardboard "
            "tab with a brass eyelet at the wrist: the eyelet sits on the green cross, the hand's long axis runs along the "
            "dashed line, fingers toward the red cross. All hands at one scale, the size the ruler says (a real hand, "
            "never bigger than the face)."
            + (" Mitten hands: the fingers are one rounded paddle with a separate thumb." if cid == 'dot' else ''))
        add(cid, 'feet', f"SHEET {cid}.feet.R: the RIGHT {'boot' if cid == 'man' else 'shoe' if cid == 'poet' else 'foot'} "
            f"in six states ({', '.join(FEET)}): the ankle brad on the green cross, the sole meeting the floor line at the "
            "toe (red) and heel (blue) crosses. Front and back views are seen end-on.")
        add(cid, 'replacements', f"SHEET {cid}.replacements: whole-body replacement cards for poses a jointed puppet "
            "cannot hold: sitting on a chair (side view), kneeling, lying on the back, lying on the side, a deep crouch, "
            "falling backwards. Same scale as the body sheets (the 10 cm ruler); each card has one brass brad at the hip "
            "so the rig can pin it to the pelvis; the head and hands are left OFF (they plug in).", template=False)
    return out


if __name__ == '__main__':
    P = prompts()
    json.dump(P, open(os.path.join(HERE, 'prompts.json'), 'w'), indent=1)
    print(len(P['sheets']), 'sheet prompts')
