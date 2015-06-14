import json
import re
import datetime
from pyquery.pyquery import PyQuery as pq

with open("result_1.txt", "r") as myfile:
    data=myfile.read().replace('\n', '')

with open("result_18_output.txt", "w+") as outfile:
	output_list = []

	d = pq(data)
	for tr in d('tr'):
		cols = pq(tr)('td')
		if cols:
			dest_airport = cols.eq(0).text()
			match = re.search(r'\((\w+)\)', dest_airport)
			airport_code = match.group(1)

			airline_link = cols.eq(0)('a').attr('href')
			match = re.search(r'airline=(\w+)', airline_link)
			airline = match.group(1)

			match = re.search(r'flightNumber=(\d+)', airline_link)
			flight_number = match.group(1)
			
			departure_time = datetime.datetime.strptime(cols.eq(3).text(), '%I:%M %p').replace(2015, 6, 15).isoformat()
			new_obj = {
				'carrier': {
					'iata': airline
				},
				'flightNumber': str(flight_number),
				'departureAirport': {
					'iata': 'SFO'
				},
				'arrivalAirport': {
					'iata': airport_code
				},
				'departureTime': departure_time
			}
			output_list.append(new_obj)


	outfile.write(json.dumps(output_list))