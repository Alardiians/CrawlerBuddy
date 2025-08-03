# WebCrawler
Async Web Crawler – Instructions
This is a domain-restricted, robots.txt-respecting asynchronous web crawler written in Python. It exports crawled URLs to a CSV and logs any errors to a log file.

Step 1: Install Dependencies
On Debian-based systems (Parrot, Kali, Ubuntu, etc.), run:

sudo apt update

sudo apt install python3-aiohttp

Alternatively, for isolated use or on other systems, create a virtual environment:

python3 -m venv venv

source venv/bin/activate

pip install aiohttp

Step 2: Save the Crawler Script
Save the provided code to a file called:

async_crawler.py

Make it executable if you want:

chmod +x async_crawler.py

Step 3: Run the Crawler

Basic Usage
python async_crawler.py <root_url>
Example:
python async_crawler.py https://quotes.toscrape.com
This crawls up to 100 pages, to a depth of 3, and saves results to output.csv.

Optional Flags
You can customize the crawl with:
--max <number>     # Maximum number of pages to crawl (default: 100)
--depth <number>   # How deep to crawl from the root URL (default: 3)
--output <file>    # Filename for the CSV output (default: output.csv)
Example with options:
python async_crawler.py https://books.toscrape.com --max 50 --depth 2 --output books.csv

Output Files
output.csv-----Crawled URLs and their depth
errors.log	------ Log of pages that failed to load

Cleaning Up
If you're using a virtual environment, deactivate it with:
deactivate

Notes
Only URLs within the same domain are crawled.

Crawler automatically skips URLs disallowed by robots.txt.

Delay between requests is 0.5s to avoid hammering servers.

HTML is parsed via regex (not JavaScript-rendered).
