from flask import Flask
app = Flask(__name__)
from webapp import views
from webapp import matplotlib_funcs
