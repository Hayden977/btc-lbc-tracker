from bs4 import BeautifulSoup
from flask import Flask, render_template
from datetime import datetime
import requests, time, csv, threading

# Flask
app = Flask(__name__)
# Strings
datetime_string = "%Y-%m-%d %H:%M:%S"
db_path = "./out.csv"
# Graph
graph_cell_width = 10
graph_height = 200
graph_hz = 30
# Pricing
prices = [10800, 12000, 0.025, 0.01]

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
		return class_pattern
	else:
		doc_soup = BeautifulSoup(request.content, "html.parser")
		doc_spans = doc_soup.find_all("span", {"class": class_pattern})
		return doc_spans[0].text

def read_csv_entries(n=10):
	"""
	Return the n latest entries in the database.
	"""
	if n < 0 or n == None:
		print(f"Row selector \"{n}\" is outside the valid range.")
		return []
	else:
		with open(db_path, "r") as f:
			return [line for line in f][-n:]

def write_csv(data):
	"""
	Write a row of data into the database.
	"""
	if data == None or data == []:
		print(f"Null result \"{data}\" cannot be written to a file.")
	else:
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
	return [now] + [x.replace("$", "").replace(",", "") for x in [btc, lbc]]

def do_daemon(wait=graph_hz):
	"""
	Create an infinite loop for the scraping function to run on a side thread.
	"""
	if wait <= 0:
		print(f"Daemon requires a non-zero counter to loop.")
	while True:
		scraped = do_scrape()
		print(f"\r{scraped}", end='')
		write_csv(scraped)
		time.sleep(wait)

def fit_between(value=0, price_min=0, price_max=0, graph_min=0, graph_max=0):
	"""
	Fits a value in a range to a value in another range.
	"""
	# https://stackoverflow.com/a/1969274
	left_span = price_max - price_min
	right_span = graph_max - graph_min
	scaled = float(float(value) - price_min) / float(left_span)
	return graph_min + (scaled * right_span)

@app.before_first_request
def startup():
	"""
	Start data logger on app startup.
	"""
	logger_daemon = threading.Thread(target=do_daemon, daemon=True)
	logger_daemon.start()

@app.route('/')
def hello_world():
	"""
	Prepare and render the data to a webpage.
	"""
	rows = read_csv_entries(40)
	current = rows[-1].split(',')
	cells = [row.split(',') for row in rows]
	for x in cells:
		x[1] = fit_between(x[1], prices[0], prices[1], graph_height, 0)
		x[2] = fit_between(x[2], prices[2], prices[3], graph_height, 0)
	return render_template("index.html", current=current, data=cells, n=len(cells), w=graph_cell_width, h=graph_height, timeout=graph_hz/2, prices=prices)

if __name__ == "__main__":
	app.run()
