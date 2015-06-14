from flask import Flask, render_template, redirect, request, flash, session, jsonify, json
from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
from keys import amadeus_token
from keys import instagram_token
import requests

app = Flask(__name__)

app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined

@app.route('/')
def go_home():
	"""Homepage."""
	return render_template("base.html")


@app.route('/my-flight')
def get_city_pics():
	get_pics = requests.get('https://api.instagram.com/v1/media/search?lat=48.858844&lng=2.294351&access_token={token}'.format(token=instagram_token))
	print get_pics
	pics = get_pics
	return render_template("/my_flight.html", pics=pics)

def get_flights_list():
	pass


if __name__ == "__main__":
	app.debug = True

	DebugToolbarExtension(app)


app.run()