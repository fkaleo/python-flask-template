#!/usr/bin/env python
from flask import Flask, request, jsonify, send_file, make_response
from werkzeug.http import parse_options_header
from waitress import serve
import os

from function import handler

app = Flask(__name__)

class Event:
    def __init__(self):
        self.body = request.get_data()
        self.json = request.get_json()
        self.form = request.form
        self.files = request.files
        self.headers = request.headers
        self.method = request.method
        self.query = request.args
        self.path = request.path

class Context:
    def __init__(self):
        self.hostname = os.environ['HOSTNAME']

def format_status_code(resp):
    if 'statusCode' in resp:
        return resp['statusCode']
    
    return 200

def format_body(resp):
    if 'body' not in resp:
        return ""
    elif type(resp['body']) == dict:
        return jsonify(resp['body'])
    else:
        return make_response(str(resp['body']))

def format_headers(resp):
    if 'headers' not in resp:
        return []
    elif type(resp['headers']) == dict:
        headers = []
        for key in resp['headers'].keys():
            header_tuple = (key, resp['headers'][key])
            headers.append(header_tuple)
        return headers
    
    return resp['headers']

def format_response(resp):
    if resp == None:
        return ('', 200)

    statusCode = format_status_code(resp)
    response = format_body(resp)
    headers = format_headers(resp)
    for header in headers:
        response.headers.set(header[0], header[1])

    return (response, statusCode)

def header_values(headers, header):
    return [item[1] for item in headers if item[0] == header]

def first_header_value(headers, header):
    return next(iter(header_values(headers, header)), None)

def file_response(resp):
    headers = format_headers(resp)

    mimetype = first_header_value(headers, 'Content-Type')

    content_disposition_header = first_header_value(headers, 'Content-Disposition')

    as_attachment = None
    attachment_filename = None
    if content_disposition_header:
        content_disposition = parse_options_header(content_disposition_header)
        as_attachment = (content_disposition[0] == 'attachment')
        attachment_filename = content_disposition[1]['filename']

    if not (mimetype or attachment_filename):
        raise ValueError("please define at least a Content-Type header or a "
                         "Content-Disposition header with filename param")

    return send_file(resp['file'], mimetype, as_attachment, attachment_filename)

@app.route('/', defaults={'path': ''}, methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
@app.route('/<path:path>', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def call_handler(path):
    event = Event()
    context = Context()
    response_data = handler.handle(event, context)
    if('file' in response_data):
        return file_response(response_data)
    else:
        return format_response(response_data)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)