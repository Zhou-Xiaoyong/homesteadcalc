#!/usr/bin/env python3
"""Single-post validator for HomesteadCalc blog articles.

Checks, for the given pages:
  1. every internal link resolves to a file on disk
  2. no internal href carries a .html suffix (clean-URL rule)
  3. HTML tags are balanced
  4. no placeholder text in the visible text (tags stripped first)
Exit code 0 = pass, 1 = fail.
"""
import html
import os
import re
import sys
from html.parser import HTMLParser

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'}
BAD = ['coming soon', 'lorem ipsum', 'todo', 'fixme', 'xxx placeholder', '[insert']


def internal(href):
    if href.startswith(('http://', 'https://', 'mailto:', '#', '//')):
        return None
    return href.split('#')[0].split('?')[0]


def resolve(href, page):
    if href.startswith('/'):
        path = href.lstrip('/')
    else:
        path = os.path.normpath(os.path.join(os.path.dirname(page), href))
    path = path.replace(os.sep, '/')
    if path in ('', '.'):
        path = 'index.html'
    if path.endswith('/'):
        path += 'index.html'
    if not os.path.splitext(path)[1]:
        path += '.html'
    return path


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(('extra close', tag, self.getpos()))
            return
        if self.stack[-1][0] != tag:
            self.errors.append(('mismatch', tag, self.getpos(), self.stack[-1]))
            return
        self.stack.pop()


def main(pages):
    ok = True
    for page in pages:
        src = open(page, encoding='utf-8').read()
        for href in re.findall(r'href="([^"]+)"', src):
            href_clean = internal(href)
            if href_clean is None:
                continue
            if href_clean.endswith('.html'):
                print('FAIL .html internal link: %s -> %s' % (page, href))
                ok = False
            resolved = resolve(href_clean, page)
            if not os.path.exists(resolved):
                print('FAIL missing target: %s -> %s (%s)' % (page, href, resolved))
                ok = False

        parser = Balance()
        parser.feed(src)
        if parser.stack or parser.errors:
            print('FAIL tag balance: %s unclosed=%s errors=%s'
                  % (page, [t for t, _ in parser.stack], parser.errors))
            ok = False

        body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', src, flags=re.S)
        text = html.unescape(re.sub(r'<[^>]+>', ' ', body)).lower()
        for bad in BAD:
            if bad in text:
                print('FAIL placeholder text: %s -> %r' % (page, bad))
                ok = False

        print('%s checked: links | tags | placeholders' % page)

    print('RESULT: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
