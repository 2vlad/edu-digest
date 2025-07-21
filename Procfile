web: gunicorn --bind 0.0.0.0:$PORT "src.admin_panel:app"
worker: python main.py collect
scheduler: python scheduler.py