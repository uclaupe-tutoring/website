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
import requests

from contextlib import contextmanager
from flask import Flask, request, redirect, make_response

UPLOAD_FOLDER = '.'
ALLOWED_EXTENSIONS = set(['cpp', 'h'])
BLACKLISTED_FILTERS = set(['build/include_alpha','legal/copyright','build/c++11','build/include_order','whitespace/end_of_line','runtime/string','build/namespaces','build/include_what_you_use','whitespace/ending_newline'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

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

def generate_markdown(file_contents):
  return """
## CS31/CS32/CS33 [the class this problem is for]

### Your Problem Title

*Contributed by Your Name*.

Your problem description. Remember to wrap in-line code in `ticks`!

#### Example

Example inputs and outputs, if helpful. If you don't have this, remove this section.

#### Solution

If you solution would benefit from a textual description, put that here. If you only want to provide the code, then remove these sentences!

```cpp
%s
```

---
""" % file_contents

def file_compiles(file_contents):
  data = {
    'source':file_contents,
    'compiler':'g530',
    'options':'',
    'filters':{
      'labels':'true',
      'directives':'true',
      'commentOnly':'true'
    }
  }
  r = requests.post('http://gcc.godbolt.org/compile', json=data) 
  return r.json()['code'] == 0

@app.route('/practice', methods=['GET', 'POST'])
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
      error_buffer.errors = filter(lambda x: x.category not in BLACKLISTED_FILTERS, error_buffer.errors)
      if len(error_buffer.errors) == 0:
        if file_compiles('\n'.join(lines)):
          response = make_response(generate_markdown(''.join(lines)))
          response.headers["Content-Disposition"] = "attachment; filename=problem.md"
          return response
        else:
          return 'Your input had compilation errors! Try checking it at the <a href=http://gcc.godbolt.org/>online compiler</a> we use.'
      else:
        return '</br>'.join(str(x) for x in error_buffer.errors if x.category not in BLACKLISTED_FILTERS)

  # TODO: Replace this with a template file.
  return """
<!doctype html>
<title>UPE Tutoring</title>
<h1>UPE Tutoring Fall '16 Practice Problem Tool</h1>
Upload your .cpp or .h file containing a practice problem.</br>
We'll run it through <a href="https://github.com/google/styleguide/tree/gh-pages/cpplint">Google's C++ linter</a>
 to check for style violations,</br>
attempt to compile it, then give you a markdown file to fill out and submit!
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
