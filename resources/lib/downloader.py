try:
    from urllib.request import Request as urllib_Request
    from urllib.request import HTTPHandler, HTTPSHandler, urlopen, install_opener, build_opener
except ImportError:
    from urllib2 import Request as urllib_Request
    from urllib2 import urlopen, install_opener, build_opener, HTTPError, HTTPSHandler, HTTPHandler

UA = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'


def download_url(url, header=None):
    for retries in range(0, 5):
        try:
            r = urllib_Request(url)
            r.add_header('User-Agent', UA)
            if header:
                for h_key, h_value in header.items():
                    r.add_header(h_key, h_value)
            http_handler = HTTPHandler(debuglevel=0)
            https_handler = HTTPSHandler(debuglevel=0)
            opener = build_opener(http_handler, https_handler)
            install_opener(opener)
            u = urlopen(r)
            contents = u.read()
            u.close()
            return contents
        except:
            raise RuntimeError('Could not open URL: {}'.format(url))
