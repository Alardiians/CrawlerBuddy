import asyncio
import aiohttp
from aiohttp import ClientError
from urllib.parse import urljoin, urldefrag, urlparse
import sys
import time
import re
import csv
import logging

class AsyncCrawler:
    def __init__(self, root_url, *,
                 max_pages=100,
                 max_depth=3,
                 concurrency=5,
                 delay=0.5):
        self.root = root_url.rstrip('/')
        self.domain = urlparse(self.root).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.seen = set([self.root])
        self.count = 0
        self.delay = delay
        self.results = []

        self.queue = asyncio.Queue()
        self.queue.put_nowait((self.root, 0))
        self.sem = asyncio.Semaphore(concurrency)
        self.robots_txt = set()

        logging.basicConfig(filename='errors.log', level=logging.ERROR,
                            format='%(asctime)s [%(levelname)s] %(message)s')

    async def fetch_robots(self, session):
        robots_url = urljoin(self.root, '/robots.txt')
        try:
            async with session.get(robots_url) as resp:
                text = await resp.text()
                for line in text.splitlines():
                    if m := re.match(r'Disallow:\s*(\S+)', line):
                        self.robots_txt.add(urljoin(self.root, m.group(1)))
        except Exception as e:
            logging.error(f"Failed to fetch robots.txt: {e}")

    def allowed(self, url):
        for dis in self.robots_txt:
            if url.startswith(dis):
                return False
        return urlparse(url).netloc == self.domain

    async def crawl_page(self, session, url, depth):
        async with self.sem:
            await asyncio.sleep(self.delay)
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.content_type != 'text/html':
                        return
                    html = await resp.text()
            except (ClientError, asyncio.TimeoutError) as e:
                logging.error(f"Failed to fetch {url}: {e}")
                return
            except Exception as e:
                logging.error(f"Unexpected error at {url}: {e}")
                return

            self.count += 1
            print(f"[{self.count}/{self.max_pages}] {url}")
            self.results.append((url,))

            for href in re.findall(r'href=["\'](.*?)["\']', html, re.IGNORECASE):
                href = urldefrag(urljoin(url, href))[0]
                if (href not in self.seen
                    and self.allowed(href)
                    and depth + 1 <= self.max_depth):
                    self.seen.add(href)
                    await self.queue.put((href, depth + 1))

    async def worker(self):
        async with aiohttp.ClientSession(headers={'User-Agent': 'AsyncCrawler/1.0'}) as session:
            await self.fetch_robots(session)
            while self.count < self.max_pages:
                try:
                    url, depth = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    break
                await self.crawl_page(session, url, depth)
                self.queue.task_done()

    def write_csv(self, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['URL'])
                writer.writerows(self.results)
        except Exception as e:
            logging.error(f"Failed to write CSV: {e}")

    def run(self, output_file="output.csv"):
        start = time.time()
        loop = asyncio.get_event_loop()
        workers = [loop.create_task(self.worker()) for _ in range(self.sem._value)]
        loop.run_until_complete(asyncio.gather(*workers))
        self.write_csv(filename=output_file)
        print(f"Done: crawled {self.count} pages in {time.time()-start:.1f}s. Output saved to {output_file}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Asynchronous Web Crawler")
    parser.add_argument("root_url", help="Root URL to start crawling from")
    parser.add_argument("--max", type=int, default=100, help="Max number of pages to crawl")
    parser.add_argument("--depth", type=int, default=3, help="Max depth to crawl")
    parser.add_argument("--output", type=str, default="output.csv", help="Output CSV filename")
    args = parser.parse_args()

    crawler = AsyncCrawler(
        root_url=args.root_url,
        max_pages=args.max,
        max_depth=args.depth,
        concurrency=5,
        delay=0.5
    )
    crawler.run(output_file=args.output)
