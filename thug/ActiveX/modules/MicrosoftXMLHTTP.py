# Microsoft XMLHTTP

import logging
import six.moves.urllib.parse as urlparse
import thug.DOM as DOM

log = logging.getLogger("Thug")


def abort(self):
    log.ThugLogging.add_behavior_warn("[Microsoft XMLHTTP ActiveX] abort")
    return 0


def open(self, bstrMethod, bstrUrl, varAsync = True, varUser = None, varPassword = None):  # pylint:disable=redefined-builtin
    # Internet Explorer ignores any \r\n or %0d%0a or whitespace appended to the domain name
    parsedUrl = urlparse.urlparse(bstrUrl)
    netloc = parsedUrl.netloc.strip("\r\n\t")
    bstrUrl = urlparse.urlunparse((parsedUrl.scheme, netloc, parsedUrl.path, parsedUrl.params, parsedUrl.query, parsedUrl.fragment))

    msg = "[Microsoft XMLHTTP ActiveX] open('%s', '%s', %s" % (bstrMethod, bstrUrl, varAsync is True, )
    if varUser:
        msg = "%s, '%s'" % (msg, varUser, )
    if varPassword:
        msg = "%s, '%s'" % (msg, varPassword, )
    msg = "%s)" % (msg, )
    log.ThugLogging.add_behavior_warn(msg)
    log.ThugLogging.log_exploit_event(self._window.url,
                                      "Microsoft XMLHTTP ActiveX",
                                      "Open",
                                      forward = False,
                                      data = {
                                                "method" : str(bstrMethod),
                                                "url"    : str(bstrUrl),
                                                "async"  : str(varAsync)
                                             }
                                     )

    self.bstrMethod  = str(bstrMethod)
    self.bstrUrl     = str(bstrUrl)
    self.varAsync    = varAsync
    self.varUser     = varUser
    self.varPassword = varPassword
    self.readyState  = 4
    return 0


def send(self, varBody = None):
    msg = "send"
    if varBody:
        msg = "%s('%s')" % (msg, str(varBody), )

    log.ThugLogging.add_behavior_warn("[Microsoft XMLHTTP ActiveX] %s" % (msg, ))
    log.ThugLogging.add_behavior_warn("[Microsoft XMLHTTP ActiveX] Fetching from URL %s (method: %s)" % (self.bstrUrl, self.bstrMethod, ))
    log.ThugLogging.log_exploit_event(self._window.url,
                                      "Microsoft XMLHTTP ActiveX",
                                      "Send",
                                      forward = False,
                                      data = {
                                                "method" : self.bstrMethod,
                                                "url"    : str(self.bstrUrl)
                                             }
                                     )

    response = None

    try:
        response = self._window._navigator.fetch(self.bstrUrl,
                                                 method        = self.bstrMethod,
                                                 headers       = self.requestHeaders,
                                                 body          = varBody,
                                                 redirect_type = "Microsoft XMLHTTP Exploit")
    except Exception:
        log.ThugLogging.add_behavior_warn('[Microsoft XMLHTTP ActiveX] Fetch failed')
        self.dispatchEvent("timeout")

    if response is None:
        return 0

    self.status          = response.status_code
    self.responseHeaders = response.headers
    self.responseBody    = response.content
    self.responseText    = response.content
    self.readyState      = 4

    self.dispatchEvent("readystatechange")

    contenttype = self.responseHeaders.get('content-type', None)
    if contenttype is None:
        return 0

    if 'text/html' in contenttype:
        doc = DOM.W3C.w3c.parseString(self.responseBody)

        window = DOM.Window.Window(self.bstrUrl, doc, personality = log.ThugOpts.useragent)
        # window.open(self.bstrUrl)

        dft = DOM.DFT.DFT(window)
        dft.run()
        return

    handler = log.MIMEHandler.get_handler(contenttype)
    if handler:
        handler(self.bstrUrl, self.responseBody)

    return 0


def setRequestHeader(self, bstrHeader, bstrValue):
    log.ThugLogging.add_behavior_warn("[Microsoft XMLHTTP ActiveX] setRequestHeaders('%s', '%s')" % (bstrHeader, bstrValue, ))
    self.requestHeaders[bstrHeader] = bstrValue
    return 0


def getResponseHeader(self, header):
    body = ""
    if header in self.responseHeaders:
        body = self.responseHeaders[header]

    try:
        self._window._navigator.fetch(self.bstrUrl,
                                      method  = self.bstrMethod,
                                      headers = self.requestHeaders,
                                      body    = body)
    except Exception:
        pass


def getAllResponseHeaders(self):
    output = ""
    for k, v in self.responseHeaders.items():
        output += "%s: %s\r\n" % (k, v, )

    return output


def overrideMimeType(self, mimetype):
    pass


def addEventListener(self, _type, listener, useCapture = False):
    if _type.lower() not in ('readystatechange', 'timeout'):
        return

    setattr(self, 'on%s' % (_type.lower(), ), listener)


def removeEventListener(self, _type, listener, useCapture = False):
    _listener = getattr(self, 'on%s' % (_type.lower(), ), None)
    if _listener is None:
        return

    if _listener in (listener, ):
        delattr(self, 'on%s' % (_type.lower(), ))


def dispatchEvent(self, evt, pfResult = True):
    listener = getattr(self, 'on%s' % (evt.lower(), ), None)
    if listener is None:
        return

    with self._window.context as ctx:  # pylint:disable=unused-variable
        listener.__call__()
