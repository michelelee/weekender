from flask import Flask, render_template, redirect, request, flash, session, jsonify, json
from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
from keys import amadeus_token
from keys import instagram_token
import requests
import pprint

app = Flask(__name__)

app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined

@app.route('/')
def go_home():
	"""Homepage."""
	return render_template("base.html")


@app.route('/my-flight')
def media_search():
	api = requests.get('https://api.instagram.com/v1/media/search?lat=48.858844&lng=2.294351&access_token={token}'.format(token=instagram_token))

	pics_json = api.json()
	data_list = pics_json.get("data")
	pics = []
	for item in data_list:
		images = item.get("images")
		image_info = images.get("standard_resolution")
		url = image_info.get("url")
		pics.append(url)

	return render_template("/my_flight.html", url=pics[:6])

def get_flights_list():
	pass


if __name__ == "__main__":
	app.debug = True
	DebugToolbarExtension(app)
	app.run()