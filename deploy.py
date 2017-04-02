#!/usr/local/bin/python

import argparse
import distutils.spawn
import shutil
import subprocess
import os


DEV_APPSERVER_PATH = distutils.spawn.find_executable('dev_appserver.py')
GCLOUD_PATH = distutils.spawn.find_executable('gcloud')

APP_PATH = os.path.join(os.path.dirname(__file__), 'app')
LIB_PATH = os.path.join(APP_PATH, 'lib')

def main():
  parser = argparse.ArgumentParser(description='Deploys to App Engine.')
  parser.add_argument('--local',
                      action='store_true',
                      help='Deploys using the local development server.')
  args = parser.parse_args()

  # First, we clean out our existing dependencies and retrieve them using pip.
  if os.path.isdir(LIB_PATH):
    shutil.rmtree(LIB_PATH)
  p = subprocess.Popen([
      'pip',
      'install',
      '-r',
      'requirements.txt',
      '-t',
      'lib'
  ], cwd=APP_PATH)
  p.communicate()

  # Then, we deploy according to the --local flag.
  if args.local:
    os.execvp(DEV_APPSERVER_PATH, [
        DEV_APPSERVER_PATH,
        os.path.join(APP_PATH, 'app.yaml')])

  os.execvp(GCLOUD_PATH, [
      GCLOUD_PATH,
      'app',
      'deploy',
      '/Users/daniel/upewebsite/app/app.yaml'#os.path.join(APP_PATH, 'app.yaml')
  ])

if __name__ == '__main__':
  main()
  
