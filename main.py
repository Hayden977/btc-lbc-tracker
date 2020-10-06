from bs4 import BeautifulSoup
import requests

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

if __name__ == "__main__":
	btc = req_wrapper("https://www.coinbase.com/price/bitcoin")
	print(parse(btc, "AssetChartAmount__Number-sc-1b4douf-1 AWmny"))
	lbc = req_wrapper("https://coinmarketcap.com/currencies/library-credit/")
	print(parse(lbc, "cmc-details-panel-price__price"))

