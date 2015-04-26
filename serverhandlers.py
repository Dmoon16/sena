'''
Created on 08.04.2012

@author: Adrian Rosian
'''
import http.server

class DataServerHandler(http.server.BaseHTTPRequestHandler):
    data = []
    default_request_version = "HTTP/1.1"
    def do_GET(self):
        import json
        from time import time
        self.send_response(200, 'OK')
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        if self.data:
            self.data.reverse()
            jsonData = json.dumps(self.data)
            lines = jsonData.splitlines()
            for i in range(len(lines)):
                lines[i] = 'data: ' + lines[i]
            jsonData = 'id: {0:d}\n'.format(int(time())) + '\n'.join(
                 lines) + '\n\n'  
            self.wfile.write(bytes(jsonData, 'UTF-8'))
        else:
            jsonData = 'id: {0:d}\n'.format(int(time())) + 'data: []\n\n'
            self.wfile.write(bytes(jsonData, 'UTF-8'))

class CommandServerHandler(http.server.BaseHTTPRequestHandler):
    lastCommand = ''
    responseJson = None
    server_version= "CommandHandler/1.1"
    def do_GET(self):
        from urllib import parse
        components = parse.urlparse(str(self.path))
        query = parse.parse_qs(components.query)
        if 'c' in query and query['c'] and isinstance(query['c'], list):
            self.lastCommand = query['c'].pop()
            self.server.lastCommand = self.lastCommand
        self.dumpReq(None)
    def dumpReq(self, formInput=None):        
        response= "<html><head></head><body>"
        response+= "<p>HTTP Request</p>"
        response+= "<p>self.lastCommand= <tt>'{:s}'</tt></p>"\
            .format(self.lastCommand)
        response+= "</body></html>"
        self.sendPage( "text/html", response )
    def sendPage( self, contentType, body ):
        self.send_response( 200 )
        self.send_header("Content-type", contentType)
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(bytes(body, 'UTF-8'))