#!/usr/bin/python2
# -*- coding: utf-8 -*-

import BaseHTTPServer
import urllib2
import re
import bs4
import argparse
from subprocess import call
from bs4 import BeautifulSoup
from urlparse import urlparse


def modify_html(dom_el, tag_name=None):
    if (isinstance(dom_el, bs4.element.NavigableString) and
            not isinstance(dom_el, bs4.element.Comment) and
            tag_name != 'script'):
        fake_content = re.sub(ur'\b([А-яёЁA-z]{6})\b', ur'\1™',
                              dom_el.string,
                              flags=re.UNICODE)
        dom_el.replace_with(fake_content)
    if 'children' in dir(dom_el):
        for el in dom_el.children:
            modify_html(el, dom_el.name)


def replacement_href(soup, site, host, port):
    pr = urlparse(site)
    proxy_url = 'http://' + host + ':' + str(port)
    for a in soup.findAll('a'):
        if not a.get('href'):
            continue
        regexp = r'https?:\/\/(' + pr.netloc + ')'
        fake_url = re.sub(regexp, proxy_url, a['href'])
        a['href'] = fake_url


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        dst_request = urllib2.urlopen(args.site + s.path)
        dst_headers = dst_request.headers.dict
        s.send_response(dst_request.code)
        for header_name in dst_headers:
            s.send_header(header_name, dst_headers.get(header_name))
        s.end_headers()
        content = dst_request.read()
        if re.match(r'text\/html', dst_headers.get('content-type', '')):
            soup = BeautifulSoup(content, 'html.parser')
            modify_html(soup.body)
            replacement_href(soup, args.site, args.host, args.port)
            content = soup.encode(formatter=None)
        s.wfile.write(content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Proxy Server 0.0.2')
    parser.add_argument('--host', default='localhost',
                        help='Host that will listen server \
                        (default: localhost)')
    parser.add_argument('--port', default='8000', type=int,
                        help='Port that will listen server (default: 8000)')
    parser.add_argument('--site', default='http://habrahabr.ru',
                        help='Destination host (default: http://habrahabr.ru)')
    args = parser.parse_args()
    httpd = BaseHTTPServer.HTTPServer((args.host, args.port), Handler)
    print "Server Starts - %s:%s. Site - %s" % (args.host,
                                                args.port,
                                                args.site)
    for program_name in ['open', 'xdg-open']:
        try:
            call([program_name, 'http://' + args.host + ':' + str(args.port)])
        except:
            print 'Failed to call program: %s' % program_name
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print "Server Stops - %s:%s" % (args.host, args.port)
