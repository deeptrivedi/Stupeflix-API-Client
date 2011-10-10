import httplib2
import urlparse
import urllib
import time
import os.path
import os
import traceback

httplib2.debuglevel = 0

class Connection:
    def __init__(self, base_url, username=None, password=None, followRedirect = True, sendHTTP100Continue = True, userAgent = 'Basic Agent'):
        self.base_url = base_url
        self.username = username
        self.userAgent = userAgent
        self.url = urlparse.urlparse(base_url)
        
        (scheme, netloc, path, query, fragment) = urlparse.urlsplit(base_url)
            
        self.scheme = scheme
        self.host = netloc
        self.path = path
        
        self.followRedirect = followRedirect
        self.username = username
        self.password = password

        self.debuglevel = 0
        self.MAX_NETWORK_RETRY = 5
        self.sendHTTP100Continue = sendHTTP100Continue
        self.createHttp()

    def createHttp(self):
        self.h = httplib2.Http(cache = None)
        self.h.follow_redirects = self.followRedirect
        self.h.follow_all_redirects = self.followRedirect
        self.h.sendHTTP100Continue = self.sendHTTP100Continue

        # Create Http class with support for Digest HTTP Authentication, if necessary
        if self.username and self.password:
            self.h.add_credentials(self.username, self.password)
    
    def request_get(self, resource, args = None, headers={}):
        return self.request(resource, "get", args, headers=headers)
        
    def request_delete(self, resource, args = None, headers={}):
        return self.request(resource, "delete", args, headers=headers)
        
    def request_head(self, resource, args = None, headers={}):
        return self.request(resource, "head", args, headers=headers)
        
    def request_post(self, resource, args = None, body = None, filename=None, headers={}):        
        return self.request(resource, "post", args , body = body, filename=filename, headers=headers)
        
    def request_put(self, resource, args = None, body = None, filename=None, headers={}, sendcallback = None):
        resp = self.request(resource, "put", args , body = body, filename=filename, headers=headers, sendcallback = sendcallback)
        return resp
 
    def dump(self, message, request_uri, method):
        if self.debuglevel > 0:
            print message, " " , time.asctime(), " " , request_uri, "\n"

    def request(self, resource, method = "get", args = None, body = None, filename=None, headers={}, sendcallback = None):        
        params = None
        path = resource

        if headers == None:
            headers = {}

        headers['User-Agent'] = self.userAgent
        
        # TEMPORARY : add support for streaming
        if method != "get":
            if not body and filename:
                body = open(filename, 'r')
                if not "Content-Length" in headers:
                    headers["Content-Length"] = str(os.stat(filename).st_size)


        if args:
            path += u"?" + urllib.urlencode(args)
            
        request_path = []
        if self.path != "/":
            if self.path.endswith('/'):
                request_path.append(self.path[:-1])
            else:
                request_path.append(self.path)
            if path.startswith('/'):
                request_path.append(path[1:])
            else:
                request_path.append(path)
                
        uri = u"%s://%s%s" % (self.scheme, self.host, u'/'.join(request_path))

        for i in range(self.MAX_NETWORK_RETRY):
            if i == (self.MAX_NETWORK_RETRY - 1):
                resp, content = self.h.request(uri, method.upper(), body=body, headers=headers, sendcallback = sendcallback)
                break
            else:
                try:
                    resp, content = self.h.request(uri, method.upper(), body=body, headers=headers, sendcallback = sendcallback)
                    break
                except Exception, e:
                    print traceback.format_exc(e)
                    print "RETRYING..."
                    self.createHttp()
        
        return {u'headers':resp, u'body':content}

    def request_raw(self, method = "get", args = None, body = None, filename=None, headers={}, sendcallback = None):
        if body == None and filename != None:
            body = open(filename)            

        for i in range(self.MAX_NETWORK_RETRY):
            if i == (self.MAX_NETWORK_RETRY - 1):
                resp, content = self.h.request(self.base_url, method.upper(), body=body, headers=headers, sendcallback = sendcallback )                
                break
            else:
                try:
                    resp, content = self.h.request(self.base_url, method.upper(), body=body, headers=headers, sendcallback = sendcallback )                
                    break
                except Exception, e:
                    print traceback.format_exc()
                    print "RETRYING RAW... ", (i + 1), e, str(e)
                    self.createHttp()

        return {u'headers':resp, u'body':content}