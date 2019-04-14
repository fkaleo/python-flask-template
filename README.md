OpenFaaS Python Flask Templates
=============================================

The Python Flask templates that make use of the incubator project [of-watchdog](https://github.com/openfaas-incubator/of-watchdog).

Templates available in this repository:
- python27-flask
- python3-flask
- python3-flask-armhf
- python3-http
- python3-http-armhf

Notes:
- To build and deploy a function for Raspberry Pi or ARMv7 in general, use the language templates ending in *-armhf*

## Downloading the templates
```
$ faas template pull https://github.com/openfaas-incubator/python-flask-template
```

# Using the python27-flask/python3-flask templates
Create a new function
```
$ faas new --lang python27-flask <fn-name>
```
Build, push, and deploy
```
$ faas up -f <fn-name>.yml
```
Test the new function
```
$ echo -n content | faas invoke <fn-name>
```

# Using the python3-http templates
Create a new function
```
$ faas new --lang python3-http <fn-name>
```
Build, push, and deploy
```
$ faas up -f <fn-name>.yml
```
Set your OpenFaaS gateway URL. For example:
```
$ OPENFAAS_URL=http://127.0.0.1:8080
```
Test the new function
```
$ curl -i $OPENFAAS_URL/function/<fn-name>
```

## Event and Context Data
The function handler is passed two arguments, *event* and *context*.

*event* contains data about the request, including:
- body: request body (`bytes`)
- json: json body if the request is application/json (`dict`)
- form: form fields if the request is either `application/x-www-form-urlencoded` or has parts without filename param in `multipart/form-data` (`werkzeug.ImmutableMultiDict`)
- files: multipart/form-data parts with filename parameter (`werkzeug.ImmutableMultiDict` of `str` to `werkzeug.FileStorage`)
- headers: http headers (`werkzeug.EnvironHeaders`)
- method: http method (str)
- query: url query (`werkzeug.ImmutableMultiDict`) 
- path: url path (`str`)

*context* contains basic information about the function, including:
- hostname
## Response Object
The response object may contain the following attributes:

### `statusCode`
Allows to specify the response status.
 
### `headers`
Allows to specify response headers.

### `body`
Defines response body, unless you want to return a file.
By default, the template will automatically attempt to set the correct Content-Type header for you based on the type of response. 

For example, returning a dict object type will automatically attach the header `Content-Type: application/json` and returning a string type will automatically attach the `Content-Type: text/html, charset=utf-8` for you.

You can override the detected mimetype by passing your own Content-Type header.

### `file`
Use the `file` attribute if you need to send a file. You can use an `fp` or a file name string as value. The response will be a file of the appropriate Content-Type with Content-Disposition header, i.e. you can suggest a file name for download. 



## Example usage
### Custom status codes and response bodies
Successful response status code and JSON response body
```python
def handle(event, context):
    return {
        "statusCode": 200,
        "body": {
            "key": "value"
        }
    }
```
Successful response status code and string response body
```python
def handle(event, context):
    return {
        "statusCode": 201,
        "body": "Object successfully created"
    }
```
Failure response status code and JSON error message
```python
def handle(event, context):
    return {
        "statusCode": 400,
        "body": {
            "error": "Bad request"
        }
    }
```
### Custom Response Headers
Setting custom response headers
```python
def handle(event, context):
    return {
        "statusCode": 200,
        "body": {
            "key": "value"
        },
        "headers": {
            "Location": "https://www.example.com/"
        }   
    }
```
Returning a custom mimetype [rfc7807](https://tools.ietf.org/html/rfc7807.html)
```python
def handle(event, context):
    return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/problem+json"
                },
                "body": {
                    "title": "No files given",
                    "type": "https://example.com/probs/no-files",
                    "detail": "Ensure that the multipart boundaries match the one in content-type, "
                                    "and the content-disposition of each file part contains both the name 'files' "
                                    "as well as a 'filename' attribute"
                }
            }
```
### Accessing Event Data
Accessing request body
```python
def handle(event, context):
    return {
        "statusCode": 200,
        "body": "You said: " + str(event.body)
    }
```
Accessing request method
```python
def handle(event, context):
    if event.method == 'GET':
        return {
            "statusCode": 200,
            "body": "GET request"
        }
    else:
        return {
            "statusCode": 405,
            "body": "Method not allowed"
        }
```
Accessing request query string arguments
```python
def handle(event, context):
    return {
        "statusCode": 200,
        "body": {
            "name": event.query['name']
        }
    }
```
Accessing request headers
```python
def handle(event, context):
    return {
        "statusCode": 200,
        "body": {
            "content-type-received": event.headers['Content-Type']
        }
    }
```
Accessing form data
```python
def handle(event, context):
    foo_val = event.form.get('foo')
    return {
        "statusCode": 200,
        "body": foo_val 
    }
```
Accessing json
```python
def handle(event, context):
    json = event.json
    return {
        "statusCode": 200,
        "body": json 
    }
```

### Working with Multipart Requests

Consider this sample multipart request with two files and a desired result file name:
```http request
POST http://localhost:5000
Accept: application/pdf
Content-Type: multipart/form-data; boundary=WebAppBoundary

--WebAppBoundary
Content-Disposition: form-data; name="resultFileName"

My merged file.pdf

--WebAppBoundary
Content-Disposition: form-data; name="files"; filename="FirstDocument.pdf"
Content-Type: application/pdf

< FirstDocument.pdf

--WebAppBoundary
Content-Disposition: form-data; name="files"; filename="SecondDocument.pdf"
Content-Type: application/pdf

< SecondDocument.pdf
```
The function merges the two documents into one file with the desired result file name. 

Note that we use the `file` attribute in the returned response object to make sure Python treats the response as a file.
```python
from PyPDF2 import PdfFileMerger, PdfFileReader
import tempfile

def handle(event, context):
    result_file_name = event.form.get('resultFileName') # part without filename having the name 'resultFileName'
    file_storages = event.files.getlist("files")        # parts with filename having the name 'files'
    
    # merge the files
    merger = PdfFileMerger()    
    for file_storage in file_storages:
        pdf_file_reader = PdfFileReader(file_storage)
        merger.append(pdf_file_reader)
    merged = tempfile.TemporaryFile()
    merger.write(merged)
    for file_storage in file_storages:
        file_storage.close()
    merged.seek(0)
    
    return {
            'statusCode': 200,
            "headers": {
                "Content-Disposition": 'attachment; filename="' + result_file_name + '"',
                'Content-Type': 'application/pdf'
            },
            'file': merged                               # use file attribute for files
        }
```
The response contains the resulting file as pdf with Content-Disposition header:

```http request
HTTP/1.1 200 OK
Cache-Control: public, max-age=43200
Content-Disposition: attachment; filename="My merged file.pdf"
Content-Length: 15774
Content-Type: application/pdf

%PDF-1.3
...

```

