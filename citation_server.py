#!/usr/bin/env python3
"""
Simple server to handle citation saving for the HTML interface
"""

import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import argparse

class CitationHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, output_dir=".", **kwargs):
        self.output_dir = output_dir
        self.json_file = os.path.join(output_dir, "citations.json")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # Handle count requests
        if path.endswith('?count=true'):
            self.handle_count_request()
            return

        # Serve the HTML file
        if path == '/' or path == '/citation_input.html':
            self.serve_html()
            return

        # Serve other static files
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == '/citations.json':
            self.handle_citation_save()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_count_request(self):
        """Return the count of existing citations"""
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        citations = [json.loads(line) for line in content.split('\n')]
                        count = len(citations)
                    else:
                        count = 0
            else:
                count = 0

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'count': count}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def handle_citation_save(self):
        """Save a citation to the JSON file"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            citation = json.loads(post_data.decode('utf-8'))

            # Validate citation
            required_fields = ['citation_id', 'citation_text', 'source_type']
            for field in required_fields:
                if field not in citation:
                    raise ValueError(f"Missing required field: {field}")

            # Save to file (append)
            with open(self.json_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(citation, ensure_ascii=False) + '\n')

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

            print(f"✅ Saved citation: {citation['citation_id']} ({citation['source_type']})")

        except Exception as e:
            print(f"❌ Error saving citation: {e}")
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def serve_html(self):
        """Serve the HTML interface"""
        html_file = os.path.join(os.path.dirname(__file__), 'citation_input.html')
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))

        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'HTML file not found')

    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass

def run_server(port=8000, output_dir="."):
    """Run the citation server"""
    os.makedirs(output_dir, exist_ok=True)

    # Create handler with output directory
    handler = lambda *args, **kwargs: CitationHandler(*args, output_dir=output_dir, **kwargs)

    server = HTTPServer(('localhost', port), handler)
    print(f"🚀 Citation server running at http://localhost:{port}")
    print(f"📁 Citations will be saved to: {os.path.abspath(output_dir)}/citations.json")
    print(f"🌐 Open http://localhost:{port} in your browser")
    print("Press Ctrl+C to stop the server")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Citation Input Server')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--output-dir', '-o', type=str, default='.', help='Directory to save citations to')

    args = parser.parse_args()
    run_server(port=args.port, output_dir=args.output_dir)