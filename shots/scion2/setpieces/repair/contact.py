"""contact sheet of registry parts: python3 contact.py out.jpg id1 id2 ..."""
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import query
def sheet(ids, out, cell=300, cols=5):
    th = []
    for i in ids:
        r = query.get(i)
        im = cv2.imread(query.path(r), cv2.IMREAD_UNCHANGED)
        if im.shape[2] == 3: im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
        a = im[..., 3:4] / 255.
        chk = np.full(im.shape[:2] + (3,), 230.)
        chk[(np.add.outer(np.arange(im.shape[0]) // 16, np.arange(im.shape[1]) // 16) % 2) == 0] = 200
        c = (im[..., :3] * a + chk * (1 - a)).astype(np.uint8)
        k = min(cell / c.shape[1], (cell - 30) / c.shape[0])
        c = cv2.resize(c, (max(1, int(c.shape[1] * k)), max(1, int(c.shape[0] * k))), interpolation=cv2.INTER_AREA)
        t = np.full((cell, cell, 3), 255, np.uint8); t[:c.shape[0], :c.shape[1]] = c
        cv2.putText(t, i[:48], (2, cell - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 0), 1)
        cv2.putText(t, i[48:96], (2, cell - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 0, 0), 1)
        th.append(t)
    while len(th) % cols: th.append(np.full((cell, cell, 3), 255, np.uint8))
    cv2.imwrite(out, np.vstack([np.hstack(th[i:i + cols]) for i in range(0, len(th), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
if __name__ == '__main__':
    sheet(sys.argv[2:], sys.argv[1])
