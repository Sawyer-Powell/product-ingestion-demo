#!/bin/sh

curl -X POST \
  -F "file=@$1" \
  http://127.0.0.1:8000/upload
