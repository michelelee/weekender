import datetime
import dateutil.parser
from flask import Flask, render_template, redirect, request, flash, session, jsonify, json
from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension

from keys import amadeus_token
from keys import instagram_token
from mock_flightstats_api_response import SUNDAY_SCHEDULED_FLIGHTS
import requests
import pprint

app = Flask(__name__)

app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined

DEFAULT_DURATION = 2

@app.route('/')
def get_flight_results():
	price_by_destination = get_flight_prices('SFO', DEFAULT_DURATION)
	# TODO: filter flights list by theme
	flights_with_price = get_scheduled_flights_with_price(price_by_destination)
	#flight_details = get_flight_detail('SFO', flight['destination'], datetime.datetime.strptime(flight['departure_date'], '%Y-%m-%d'), flight['return_date'])

	return render_template("/flight_results.html", flight_results=flights_with_price)

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

def get_scheduled_flights_with_price(price_by_destination):
	result_flights = []
	for flight in SUNDAY_SCHEDULED_FLIGHTS['scheduledFlights']:
		departure_time = dateutil.parser.parse(flight['departureTime'])
		# filter only flights past the current time
		if departure_time > datetime.datetime.now():
			if flight['arrivalAirport']['iata'] in price_by_destination:
				scheduled_flight = flight
				scheduled_flight['price'] = price_by_destination[flight['arrivalAirport']['iata']]
				scheduled_flight['departureTime'] = departure_time.strftime('%I:%M %p')
				result_flights.append(scheduled_flight)

	return result_flights

def get_flight_detail(origin, destination, departure_time, return_date):
	"""departure_time is a datetime object"""
	departure_date = departure_time.date().isoformat()
	api = requests.get('http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={origin}'
		'&destination={destination}&departure_date={departure_date}&return_date={return_date}&direct=true&apikey={token}'.format(
			origin=origin,
			destination=destination,
			departure_date=departure_date,
			return_date=return_date,
			token=amadeus_token
		)
	)

	response_json = api.json()

	# find the first returned itinerary with the specified departure time (list is already sorted by price)
	s = 0
	for result in response_json['results']:
		for itinerary in result['itineraries']:
			s += 1 # do something more than this
	print s
	return response_json

def get_flight_prices(origin, duration):
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
	today = datetime.date.today()
	tomorrow = today #+ datetime.timedelta(days=1)

	departure_date_str = '--'.join([today.isoformat(), tomorrow.isoformat()])

	api = requests.get(
		'http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={origin}'
		'&departure_date={departure}&duration={duration}&max_price=20000&direct=true&apikey={token}'.format(
			origin=origin,
			departure=departure_date_str,
			duration=duration,
			token=amadeus_token
		)
	)

	response_json = api.json()
	flights = response_json.get("results")
	price_by_destination = {}
	for flight in flights:
		price_by_destination[flight["destination"]] = flight["price"]

	return price_by_destination


if __name__ == "__main__":
	app.debug = True
	DebugToolbarExtension(app)
	app.run()