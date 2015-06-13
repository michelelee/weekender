
from flask import Flask, render_template, redirect, request, flash, session, jsonify, json
from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
import requests

app = Flask(__name__)

app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined

@app.route('/')
def go_home():
	"""Homepage."""
	print "lots of changes again"
	return render_template("base.html")


@app.route('/my-flight')
def get_city_pics():
	get_pics = requests.get('https://api.instagram.com/v1/media/search?lat=48.858844&lng=2.294351&access_token=536176452.1fb234f.f67ad8054ffe4f46aecff1b2e4c4b7c6')
	print get_pics
	pics = get_pics
	return render_template("/my_flight.html", pics=pics)


if __name__ == "__main__":
	app.debug = True

	DebugToolbarExtension(app)


app.run()