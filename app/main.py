# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cpplint
import logging
import os
import sys

from contextlib import contextmanager
from flask import Flask, request, redirect

UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = set(['cpp', 'h'])


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class LinterError(object):
    def __init__(self, filename, linenum, category, confidence, message):
      self.filename = filename
      self.linenum = linenum
      self.category = category
      self.confidence = confidence
      self.message = message
    
    def __str__(self):
      return '{}:{}:  {}  [{}] [{}]'.format(self.filename, self.linenum, 
                                            self.message, self.category, 
                                            self.confidence) 


class LinterErrorBuffer(object):  
  def __init__(self):
    self.errors = []

  def append(self, filename, linenum, category, confidence, message):
    self.errors.append(LinterError(filename, linenum, category, confidence, 
                                   message))
  

def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/lint', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    if 'file' not in request.files:
      flash('No file part')
      return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
      flash('No selected file')
      return redirect(request.url)
    if file and allowed_file(file.filename):
      lines = file.readlines()
      error_buffer = LinterErrorBuffer()

      # Use the same convention as cpplint to find the extension.
      cpplint.ProcessFileData(file.filename,
                              file.filename[file.filename.rfind('.') + 1:], 
                              lines, error_buffer.append)
      return '</br>'.join(str(x) for x in error_buffer.errors)

  # TODO: Replace this with a template file.
  return """
<!doctype html>
<title>Upload new File</title>
<h1>Upload new File</h1>
<form action="" method=post enctype=multipart/form-data>
<p><input type=file name=file>
<input type=submit value=Upload>
</form>
"""


@app.route('/')
def hello():
  """Return a friendly HTTP greeting."""
  return 'Hello World!'


@app.errorhandler(500)
def server_error(e):
  logging.exception('An error occurred during a request.')

  # TODO: Replace this with a template file.
  return """
An internal error occurred: <pre>{}</pre>
See logs for full stacktrace.
""".format(e), 500


if __name__ == '__main__':
  # This is used when running locally. Gunicorn is used to run the
  # application on Google App Engine. See entrypoint in app.yaml.
  app.run(host='127.0.0.1', port=8080, debug=True)
