from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import cloudinary
from urllib.parse import quote

app = Flask(__name__)

app.secret_key = "k8HDLZbie2T8UWvC70S7f-SukGY"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:1234@localhost/gymdb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["MIN_AGE"]=15
app.config["MAX_AGE"]=20


db = SQLAlchemy(app)
login = LoginManager(app=app)


cloudinary.config(
    cloud_name = "duithan01",
    api_key = "691936669278626",
    api_secret = "99J5hbHBCXAbC9qbWZDKZs7nLoU"
)
# % quote("123456")