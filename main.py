from bs4 import BeautifulSoup
from flask import Flask, render_template
from datetime import datetime
import requests, time, csv, threading

app = Flask(__name__)
db_path = "./out.csv"
datetime_string = "%Y-%m-%d %H:%M:%S"
display_cell_width = 10
display_height = 200
refresh = 30

def req_wrapper(url=None):
	"""
	Create a request and return the successful response for a given URL.
	"""
	if url is None:
		return None
	else:
		response = requests.get(url)
		if response.status_code == 200:
			return response
		else:
			print(f"HTTP request to {url} returned code {response.status_code}. See https://httpstatuses.com/.")
			return None

def parse(request, class_pattern=""):
	"""
	Scrape a response object for price data.
	"""
	if class_pattern == "":
		print(f"\"{class_pattern}\" is a null selector.")
	doc_soup = BeautifulSoup(request.content, "html.parser")
	doc_spans = doc_soup.find_all("span", {"class": class_pattern})
	return doc_spans[0].text

def cstns(s):
	"""
	Convert a currency string to a number string.
	"""
	return s.replace("$", "").replace(",", "")

def read_csv_entries(n=10):
	"""
	Return the n latest entries in the database.
	"""
	with open(db_path, "r") as f:
		return [line for line in f][-n:]

def write_csv(data):
	"""
	Write a row of data into the database.
	"""
	with open(db_path, "a") as f:
		writer = csv.writer(f, lineterminator='\n')
		writer.writerow(data)

def do_scrape():
	"""
	Perform the scrape procedure.
	"""
	btc_req = req_wrapper("https://www.coinbase.com/price/bitcoin")
	btc = parse(btc_req, "AssetChartAmount__Number-sc-1b4douf-1")
	lbc_req = req_wrapper("https://coinmarketcap.com/currencies/library-credit/")
	lbc = parse(lbc_req, "cmc-details-panel-price__price")
	now = datetime.now().strftime(datetime_string)
	return [now] + [cstns(x) for x in [btc, lbc]]

def do_daemon(wait=refresh):
	"""
	Create an infinite loop for the scraping function to run on a side thread.
	"""
	while True:
		scraped = do_scrape()
		print(f"\r{scraped}", end='')
		write_csv(scraped)
		time.sleep(wait)

def fit_between(value, price_min, price_max, graph_min, graph_max):
	# https://stackoverflow.com/a/1969274
	left_span = price_max - price_min
	right_span = graph_max - graph_min
	scaled = float(float(value) - price_min) / float(left_span)
	return graph_min + (scaled * right_span)

@app.before_first_request
def startup():
	logger_daemon = threading.Thread(target=do_daemon, daemon=True)
	logger_daemon.start()

@app.route('/')
def hello_world():
	rows = read_csv_entries(40)
	current = rows[-1].split(',')
	cells = [row.split(',') for row in rows]
	display_cells = len(cells)
	for x in cells:
		x[1] = fit_between(x[1], 10600, 11000, display_height, 0)
		x[2] = fit_between(x[2], 0.01, 0.025, display_height, 0)
	return render_template("index.html", current=current, data=cells, n=display_cells, w=display_cell_width, h=display_height, timeout=refresh/2)

if __name__ == "__main__":
	app.run()
