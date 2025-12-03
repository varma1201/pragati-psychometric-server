pragati-psychometric-server/
├── pyproject.toml / requirements.txt
├── .flaskenv
├── README.md
└── app/
├── **init**.py
├── server.py # entrypoint (gunicorn/flask run)
├── database_manager.py # minimal Mongo wrapper
├── psychometric_evaluator.py
├── psychometric_endpoints.py
├── user_profile_manager.py
└── extensions.py
