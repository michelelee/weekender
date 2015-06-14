import datetime
import dateutil.parser
import json
from flask import Flask, render_template, redirect, request, flash, session, jsonify, json
from jinja2 import StrictUndefined
from flask_debugtoolbar import DebugToolbarExtension

from keys import amadeus_token
from keys import instagram_token
from keys import sabre_token
from mock_flightstats_api_response import SUNDAY_SCHEDULED_FLIGHTS
import requests
import pprint

app = Flask(__name__)

app.secret_key = "ABC"

app.jinja_env.undefined = StrictUndefined

DEFAULT_DURATION = 2

@app.route('/')
def get_flight_results():
	depart_date = datetime.date.today()
	duration = DEFAULT_DURATION
	theme = 'BEACH'

	price_by_destination = filter_flight_prices_by_theme(
		get_flight_prices('SFO', depart_date, duration),
		theme
	)

	flights_with_price = get_scheduled_flights_with_price(SUNDAY_SCHEDULED_FLIGHTS, price_by_destination)

	return_date = depart_date + datetime.timedelta(days=duration)
	return render_template("/flight_results.html", flight_results=flights_with_price, depart_date=depart_date.isoformat(), return_date=return_date.isoformat())


@app.route('/my-flight')
def flight_details():
	dest = request.args.get('dest')
	carrier = request.args.get('carrier')
	outbound_flight = request.args.get('outbound_flight')
	depart_date = request.args.get('depart_date')
	return_date = request.args.get('return_date')

	airline_names = get_airline_names()

	flight_itinerary, fare = get_flight_detail('SFO', dest, carrier, outbound_flight, depart_date, return_date)
	outbound_flight = None
	inbound_flight = None
	booking_link = None

	if flight_itinerary:
		outbound = flight_itinerary['outbound']['flights'][0]
		outbound_flight = {
			'depart': dateutil.parser.parse(outbound['departs_at']).strftime('%a, %b %d %I:%M %p'),
			'arrive': dateutil.parser.parse(outbound['arrives_at']).strftime('%a, %b %d %I:%M %p'),
			'carrier': airline_names.get(outbound['marketing_airline']),
			'flight_number': outbound['flight_number']
		}

		inbound = flight_itinerary['inbound']['flights'][0]
		inbound_flight = {
			'depart': dateutil.parser.parse(inbound['departs_at']).strftime('%a, %b %d %I:%M %p'),
			'arrive': dateutil.parser.parse(inbound['arrives_at']).strftime('%a, %b %d %I:%M %p'),
			'carrier': airline_names.get(inbound['marketing_airline']),
			'flight_number': inbound['flight_number']
		}

		booking_link = 'https://www.google.com/flights/#search;f=SFO;t={dest};d={depart_date};r={return_date};'\
		'sel=SFO{dest}0{depart_carrier}{depart_flight},{dest}SFO0{return_carrier}{return_flight}'.format(
			dest=dest,
			depart_date=depart_date,
			return_date=return_date,
			depart_carrier=outbound['marketing_airline'],
			depart_flight=outbound['flight_number'],
			return_carrier=inbound['marketing_airline'],
			return_flight=inbound['flight_number']
		)

	dest_city_info = get_city_info(dest)

	api = requests.get('https://api.instagram.com/v1/media/search?lat={lat}&lng={lng}&access_token={token}'.format(
			lat=dest_city_info['city']['location']['latitude'],
			lng=dest_city_info['city']['location']['longitude'],
			token=instagram_token
		)
	)

	pics_json = api.json()
	data_list = pics_json.get("data")
	sorted_list = sorted(data_list, key=lambda k:k['likes']['count'], reverse=True)
	pics = []
	for item in sorted_list:
		images = item.get("images")
		image_info = images.get("standard_resolution")
		url = image_info.get("url")

		# some basic heuristic to match better photos
		if not len(item['users_in_photo']):
			pics.append(url)

	return render_template(
		"/my_flight.html",
		url=pics[:7],
		dest=dest,
		city_name=dest_city_info['city']['name'], 
		outbound_flight=outbound_flight,
		inbound_flight=inbound_flight,
		fare=fare,
		booking_link=booking_link
	)

def get_scheduled_flights_with_price(scheduled_flights, price_by_destination):
	"""Merges flight schedules with pricing data"""
	airline_names = get_airline_names()
	result_flights = []
	for flight in scheduled_flights['scheduledFlights']:
		departure_time = dateutil.parser.parse(flight['departureTime'])
		# filter only flights past the current time + 1 hour
		if departure_time > datetime.datetime.now() + datetime.timedelta(hours=1):
			if flight['arrivalAirport']['iata'] in price_by_destination:
				scheduled_flight = flight
				scheduled_flight['price'] = price_by_destination[flight['arrivalAirport']['iata']]
				scheduled_flight['departureTime'] = departure_time.strftime('%I:%M %p')
				scheduled_flight['carrier']['name'] = airline_names.get(scheduled_flight['carrier']['iata'])
				result_flights.append(scheduled_flight)

	return result_flights

def filter_flight_prices_by_theme(flight_prices, theme):
	"""Queries the Sabre API for airports matching the given theme, then filters the list of flights to only these airports"""
	# no theme specified, just return everything
	if not theme:
		return flight_prices

	headers = {'Authorization': sabre_token}
	api = requests.get('https://api.test.sabre.com/v1/lists/supported/shop/themes/' + theme, headers=headers)
	destinations = api.json()['Destinations']

	airport_codes = []
	for destination in destinations:
		airport_codes.append(destination['Destination'])

	filtered_prices = {}

	for theme_airport in airport_codes:
		if theme_airport in flight_prices:
			filtered_prices[theme_airport] = flight_prices[theme_airport]

	return filtered_prices


def get_airline_names():
	"""Queries the Sabre Airline Info API to map airline codes to their names"""
	headers = {'Authorization': sabre_token}
	api = requests.get('https://api.test.sabre.com/v1/lists/utilities/airlines', headers=headers)
	airline_info = api.json()['AirlineInfo']
	code_to_name = {}
	for airline in airline_info:
		code_to_name[airline['AirlineCode']] = airline['AirlineName']

	return code_to_name

def get_city_info(airport_code):
	"""Queries the Amadeus Location Services API to fetch city information for the given airport"""
	api = requests.get('http://api.sandbox.amadeus.com/v1.2/location/{airport}/?apikey={token}'.format(
			airport=airport_code,
			token=amadeus_token
		)
	)
	response_json = api.json()

	# if airport_code was actually a city code, no need to fetch city data again since our result already contains it
	if 'city' not in response_json:
		city_code = response_json['airports'][0]['city_code']
		api = requests.get('http://api.sandbox.amadeus.com/v1.2/location/{city}/?apikey={token}'.format(
				city=city_code,
				token=amadeus_token
			)
		)
		response_json = api.json()

	return response_json


def get_flight_detail(origin, destination, carrier, outbound_flight, depart_date, return_date):
	"""Queries the Amadeus Low Fare Search API to fetch itineraries for the specified parameters"""
	api = requests.get('http://api.sandbox.amadeus.com/v1.2/flights/low-fare-search?origin={origin}'
		'&destination={destination}&departure_date={departure_date}&return_date={return_date}&direct=true&apikey={token}'.format(
			origin=origin,
			destination=destination,
			departure_date=depart_date,
			return_date=return_date,
			token=amadeus_token
		)
	)
	response_json = api.json()
	return _get_best_itinerary_for_outbound_flight(response_json, carrier, outbound_flight)

def _get_best_itinerary_for_outbound_flight(flight_search_results, marketing_carrier, outbound_flight):
	# find the first returned itinerary with the specified outbound flight number
	for result in flight_search_results['results']:
		for itinerary in result['itineraries']:
			flight_number = itinerary['outbound']['flights'][0]['flight_number']
			carrier = itinerary['outbound']['flights'][0]['marketing_airline']
			if flight_number == outbound_flight and carrier == marketing_carrier:
				return itinerary, result['fare']

	return None, None

def get_flight_prices(origin, depart_date, duration):
	"""Queries the Amadeus Inspiration Search API to fetch pricing data for direct flights from the specified origin.
	Returns a mapping from destination to roundtrip flight price."""

	api = requests.get(
		'http://api.sandbox.amadeus.com/v1.2/flights/inspiration-search?origin={origin}'
		'&departure_date={departure}&duration={duration}&max_price=20000&direct=true&apikey={token}'.format(
			origin=origin,
			departure=depart_date.isoformat(),
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
	app.run()