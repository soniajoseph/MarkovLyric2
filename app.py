from flask import Flask
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.debug = True

bootstrap = Bootstrap(app)

if __name__ == '__main__':
    app.run()

from app import routes


