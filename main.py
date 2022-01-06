from flask import Flask, render_template, request, Response, jsonify
from bs4 import BeautifulSoup as bs
import requests
import re
from selenium import webdriver
import datetime
import numpy as np
from lxml import html
from selenium.webdriver.chrome.options import Options  
import os

app = Flask(__name__)

@app.route("/teams")
def teams_dic():
	teams, teams_url_dict = get_teams()
	# print(teams)
	return jsonify(teams)

@app.route('/', methods=['GET', 'POST'])
def index():
	seat_results_1 = []
	seat_results_2 = []

	if request.method == "POST":
		dates_url_dict = get_games(request.form["team"], team_url_dict)
		date = datetime.datetime.strptime(request.form["date"],"%Y-%m-%d")
		string_date = date.strftime("%-m-%-d-%Y")

		best_seats = get_best_seats(teams, request.form["team"])

		game_url = "https://www.stubhub.com" + dates_url_dict[string_date]
		# print(game_url)
		# print(best_seats)

		# print(best_seats[0].keys())
		
		chrome_options = Options()  
		chrome_options.headless = True
		user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'    
		chrome_options.add_argument('user-agent={0}'.format(user_agent))
		chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

		for seat in best_seats:
			for key, value in seat.items():

				seat_url = game_url + "?sid=" + seat[key]
				wd = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=chrome_options)
				wd.get(seat_url)
				# wd.get_screenshot_as_file("screenshot.png")
				element = wd.find_element_by_class_name('EventRoyal__container')
				seat_info = element.text.split("\n")[2:]
				seat_info = seat_info[:-31]
				num_prices = 5
				num_info = 6
				seat_info = seat_info[0:num_prices*num_info]
				print(seat_info)
				new_info = np.array_split(seat_info, 5)
				# print(new_info)

				test = []
				for listing in new_info:
					new_info_list = list(listing)
					if tickets_in_range(listing[2][:-7], request.form["num_tickets"]):
						test.append({"row": listing[1][4:], "num_tickets": listing[2][:-7], "price": listing[3], "image": key})
					else:
						test.append({"row": "", "num_tickets": "", "price": "", "image": key})

					
				seat_results_1.append(test)
				# print(seat_results_1)


		# for seat in best_seats[3:]:
		# 	for key, value in seat.items():
		# 		seat_results_2.append({"row": "10", "price": "$20", "num_tickets": "2", "image": key})
		
		# print(seat_results_1)
		wd.close()
		return render_template('index.html', movie_errors=[], seat_results_1=seat_results_1[0:3], seat_results_2=seat_results_1[3:])

	return render_template('index.html', movie_errors=[], seat_results_1=seat_results_1[0:3], seat_results_2=seat_results_1[3:])



def main():
	teams, team_url_dict = get_teams()
	# dates_url_dict = get_games("Philadelphia 76ers", team_url_dict)
	# best_seats = get_best_seats(teams, "Philadelphia 76ers")

	# game_url = "https://www.stubhub.com" + dates_url_dict["1-12-2022"]
	# print(best_seats)



	# # for seat in best_seats[0]:
	# seat_url = game_url + "?sid=" + best_seats["101"]
	# print(seat_url)
	# wd = webdriver.Chrome()
	# wd.get(seat_url)
	# element = wd.find_element_by_class_name('UnifiedLayout__mainContainer')
	# seat_info = element.text.split("\n")[2:]
	# seat_info = seat_info[:-31]
	# num_prices = 5
	# num_info = 6
	# print(seat_info[0:num_prices*num_info])

	return None

def tickets_in_range(tickets, num_tickets):
	tickets_list = []
	tickets = tickets.strip()
	print("tick: " + str(tickets))
	print(tickets[len(tickets) - 1])
	if len(tickets) != 2:
		tickets_list = [str(i) for i in range(1, int(tickets[len(tickets) - 1]) + 1)]
		# tickets_string = "".join(t for t in tickets_list)
		# print(tickets_string)
		if num_tickets in tickets_list:
			return True
	else:
		if num_tickets == tickets:
			return True

	return False

def get_teams():
	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '\
           'AppleWebKit/537.36 (KHTML, like Gecko) '\
           'Chrome/75.0.3770.80 Safari/537.36'}

	teams = []
	team_url_dict = {}

	stub_url = "https://www.stubhub.com/nba-tickets/grouping/115/"

	r = requests.get(stub_url, headers=headers)
	soup = bs(r.text, "html.parser")	

	teams_html = soup.find_all("div", class_="EntitiesSeoLinks__Container")
	for team in teams_html[0].find_all("li")[:30]:
		teams.append({"name": team.contents[0].text})
		team_url_dict[team.contents[0].text] = team.contents[0]["href"]

	return teams, team_url_dict

def get_games(team, team_url_dict):
	headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '\
           'AppleWebKit/537.36 (KHTML, like Gecko) '\
           'Chrome/75.0.3770.80 Safari/537.36'}

	team_url = "https://www.stubhub.com/" + str(team_url_dict[team])
	r = requests.get(team_url, headers=headers)
	soup = bs(r.text, "html.parser")

	games = []
	dates_url_dict = {}

	redirects_html = soup.find_all("div", class_="EventRedirection")
	for game in redirects_html:
		# games.append(game.contents[0]["href"])
		m = re.search(r'\d{1,2}-\d{1,2}-\d{4}', str(game.contents[0]["href"]))
		dates_url_dict[m.group(0)] = game.contents[0]["href"]

	# print(dates_url_dict)

	return dates_url_dict

def get_best_seats(teams, team):
	best_seats_url_dict = {}
	best_seats = [{"124":"29901"}, {"101":"29896"}, {"102":"29897"}, {"112":"29898"}, {"113":"29899"}, {"114":"29900"}]
	best_seats_url_dict[team] = best_seats
	return best_seats_url_dict[team]

if __name__ == "__main__":
	teams, team_url_dict = get_teams()
	app.run(debug=True)
	# app.run(host='127.0.0.9',port=4455,debug=True) 
	# main()