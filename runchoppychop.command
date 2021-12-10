#!/bin/bash

cd "$(dirname "$0")"

echo Pulling latest version of ChoppyChop...
git stash
git pull origin main

./prepare_virtualenv.sh

# Run
source .env/bin/activate
.env/bin/python ./ChoppyChop.py "$@"
