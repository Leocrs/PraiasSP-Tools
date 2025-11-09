web: gunicorn -w 4 -b 0.0.0.0:$PORT api.index:app
release: python -c "from api.index import init_db; init_db()"
