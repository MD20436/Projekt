from flask import Flask
from blueprints.scraping import scraping_bp
from db import initialize_db

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    app.config.from_object('config.Config')
    initialize_db(app)

    app.register_blueprint(scraping_bp, url_prefix='/scraping')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
