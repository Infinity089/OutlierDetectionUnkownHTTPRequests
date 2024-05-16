from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import threading
import os
import json
import requests
from urllib.parse import urlparse
from generate_self_signed_cert import generate_self_signed_cert
from datetime import datetime

CERT_PATH = 'cert.pem'
KEY_PATH = 'key.pem'
DATA_DIRECTORY = 'Data'
NGINX_START_PAGE = b"<!DOCTYPE html><html><head><title>Welcome to Nginx!</title></head><body><h1>Welcome to Nginx!</h1></body></html>"
JSON_EXTENSION = 'json'
LOG_COLLECTOR_URL = "[URL_LOG_COLLECTOR]"
LOG_COLLECTOR_TOKEN = "[SECRET]"


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        self.handle_request('POST', body)

    def do_DELETE(self):
        self.handle_request('DELETE')

    def do_PUT(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        self.handle_request('PUT', body)

    def do_PATCH(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        self.handle_request('PATCH', body)

    def do_HEAD(self):
        self.handle_request('HEAD')

    def do_OPTIONS(self):
        self.handle_request('OPTIONS')

    def handle_request(self, method, body=None):
        # Extrahiere die relevanten Informationen aus dem Request
        source_ip = self.client_address[0]
        source_port = self.client_address[1]
        path = self.path
        headers = dict(self.headers)
        request_body = body

        # Analysiere den Pfad und extrahiere die Parameter
        parsed_path = urlparse(path)

        # Füge den aktuellen UTC-Timestamp hinzu
        timestamp = datetime.utcnow().isoformat()

        # Erstelle einen Dictionary-Eintrag für den aktuellen Request
        request_data = {
            'Timestamp': timestamp,
            'SourceIP': source_ip,
            'SourcePort': source_port,
            'Method': method,
            'Path': parsed_path.path,
            'PathParams': parsed_path.query,
            'Headers': headers,
            'Body': request_body
        }

        # Erstelle den Dateinamen basierend auf dem aktuellen Datum
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        json_filename = os.path.join(DATA_DIRECTORY, f"request_data_{date_str}.{JSON_EXTENSION}")

        # Stelle sicher, dass das Datenverzeichnis existiert
        if not os.path.exists(DATA_DIRECTORY):
            os.makedirs(DATA_DIRECTORY)

        # Lade vorhandene Daten aus der JSON-Datei oder erstelle eine leere Liste
        existing_data = []
        if os.path.exists(json_filename):
            with open(json_filename, 'r') as json_file:
                existing_data = json.load(json_file)

        # Füge den aktuellen Request-Daten zum vorhandenen Datensatz hinzu
        existing_data.append(request_data)

        # Speichere die aktualisierten Daten in der JSON-Datei
        with open(json_filename, 'w') as json_file:
            json.dump(existing_data, json_file, indent=2)
        # Sende die Response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(NGINX_START_PAGE)

        # Test Connection API
        headers = {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip,deflate',
                    'Connection': 'keep-alive',
                    'token': LOG_COLLECTOR_TOKEN
                    }
        payload = json.dumps(request_data)
        response = requests.request("POST", LOG_COLLECTOR_URL, headers=headers, data=payload, verify=False)


def start_server(port, use_ssl=False):
    server_class = HTTPServer
    handler_class = MyHandler

    if use_ssl:
        httpd = server_class(("0.0.0.0", port), handler_class)
        httpd.socket = ssl.wrap_socket(httpd.socket, certfile=CERT_PATH, keyfile=KEY_PATH, server_side=True)
    else:
        httpd = server_class(("0.0.0.0", port), handler_class)

    print(f"Server running on port {port}")
    httpd.serve_forever()

def start_servers_in_thread(ports, use_ssl=False):
    threads = []

    for port in ports:
        thread = threading.Thread(target=start_server, args=(port, use_ssl))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    generate_self_signed_cert(CERT_PATH, KEY_PATH)

    http_ports = [80, 81, 8080, 8081, 8000]
    https_ports = [443, 4433, 4443, 8443, 8444, 8445]

    http_thread = threading.Thread(target=start_servers_in_thread, args=(http_ports,))
    https_thread = threading.Thread(target=start_servers_in_thread, args=(https_ports, True))

    http_thread.start()
    https_thread.start()

    http_thread.join()
    https_thread.join()