#!/usr/bin/env python3
"""Local dev server for WYGWYL. Serves the repo ROOT (so /index.html and /shots/... both resolve)
and supports HTTP Range requests (needed to scrub/seek the film).  Usage: python3 serve.py [port]"""
import os, re, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class H(SimpleHTTPRequestHandler):
    def send_head(self):
        rng, path = self.headers.get('Range'), self.translate_path(self.path)
        m = re.match(r'bytes=(\d*)-(\d*)', rng or '')
        if not m or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        a = int(m.group(1) or 0); b = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (a, b, size))
        self.send_header('Content-Length', str(b - a + 1)); self.end_headers()
        f = open(path, 'rb'); f.seek(a); self._left = b - a + 1; return f
    def copyfile(self, src, dst):
        left = getattr(self, '_left', None)
        if left is None: return super().copyfile(src, dst)
        dst.write(src.read(left)); self._left = None
    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes'); super().end_headers()

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8800
    print('WYGWYL → http://127.0.0.1:%d/' % port)
    ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
