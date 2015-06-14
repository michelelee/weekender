import datetime
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
def get_flight_results():
	flights = get_flights_list('SFO', 2)
	flight = "flight 1"
	price = "price"
	# currently we're only showing departure _date_, but we will show departure time later
	departure_time = "departure_time"
	# we don't need arrival time in this view
	arrival_time = "arrival_time"
	flight_results = [flight, price, departure_time, arrival_time]

	return render_template("/flight_results.html", flight=flight, price=price, departure_time=departure_time, arrival_time=arrival_time, flight_results=flight_results)

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

def get_flights_list(origin, duration):
	"""Returns a list of flight dicts, each containing the following:
	{
		"destination": "RIC",
		"departure_date": "2015-09-09",
		"return_date": "2015-09-16",
		"price": "83.95",
		"airline": "B6"
	}, {
		"destination": "SNA",
		"departure_date": "2015-09-23",
		"return_date": "2015-09-30",
		"price": "368.70",
		"airline": "UA"
	}, {
		"destination": "PAP",
		"departure_date": "2015-09-10",
		"return_date": "2015-09-17",
		"price": "371.46",
		"airline": "NK"
	}
	"""
	today = datetime.date.today() + datetime.timedelta(days=1) # this is a hack because amadeus sucks
	tomorrow = today + datetime.timedelta(days=1)

	departure_date_str = '--'.join([today.isoformat(), tomorrow.isoformat()])

	api = requests.get(
		'http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={origin}'
		'&departure_date={departure}&duration={duration}&max_price=1500&apikey={token}'.format(
			origin=origin,
			departure=departure_date_str,
			duration=duration,
			token=amadeus_token
		)
	)

	response_json = api.json()
	return response.get("results")


if __name__ == "__main__":
	app.debug = True
	DebugToolbarExtension(app)
	app.run()