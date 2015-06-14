
from flask import Flask, render_template, redirect, request, flash, session, jsonify, json
from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension
import requests
import pprint

app = Flask(__name__)

app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined

access_token="536176452.1fb234f.f67ad8054ffe4f46aecff1b2e4c4b7c6"

@app.route('/')
def go_home():
	"""Homepage."""
	print "lots of changes again"
	return render_template("base.html")

@app.route('/flight-results')
def get_flight_results():
	flight = "flight 1"
	price = "price"
	departure_time = "departure_time"
	arrival_time = "arrival_time"
	flight_results = [flight, price, departure_time, arrival_time]

	return render_template("/flight_results.html", flight=flight, price=price, departure_time=departure_time, arrival_time=arrival_time, flight_results=flight_results)

@app.route('/my-flight')
def media_search():
	api = requests.get('https://api.instagram.com/v1/media/search?lat=48.858844&lng=2.294351&access_token=536176452.1fb234f.f67ad8054ffe4f46aecff1b2e4c4b7c6')

	pics_json = api.json()
	data_list = pics_json.get("data")
	pics = []
	for item in data_list:
		images = item.get("images")
		image_info = images.get("standard_resolution")
		url = image_info.get("url")
		pics.append(url)

	return render_template("/my_flight.html", url=pics[:6])


if __name__ == "__main__":
	app.debug = True
	DebugToolbarExtension(app)
	app.run()