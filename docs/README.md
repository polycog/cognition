# Project Documentation

To run...

1. Create & activate a virtual environment
2. `pip install -r requirements.txt`
3. `make html`
4. `python -m http.server -d build/html`
5. In browser: `http://localhost:8000`

## To Deploy

Assume `DEST` is target.

`rsync -v --delete --recursive --progress --exclude='.git' --exclude='.gitignore' --exclude='_sources' build/html/* DEST`
