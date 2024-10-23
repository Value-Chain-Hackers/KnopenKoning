
from logging import getLogger
logger = getLogger(__name__)

import requests
import os
import hashlib
import mimetypes

from queue import Queue
import threading
import concurrent


class WebDownloader:
    def __init__(self, urls, cache, max_workers=4, timeout=10):
        self.urls = urls
        self.cache = cache
        self.max_workers = max_workers
        self.timeout = timeout

    def download_url(self, url):
        try:
            self.cache.get(url)
            return f"Downloaded and cached: {url}"
        except requests.RequestException as e:
            return f"Failed to download {url}: {e}"

    def start_download(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.download_url, url): url for url in self.urls}
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                try:
                    result = future.result(timeout=self.timeout)
                    print(result)
                except concurrent.futures.TimeoutError:
                    print(f"Timeout error for URL: {url}")
                except Exception as e:
                    print(f"An error occurred for URL: {url}: {e}")

        print("All downloads complete.")
        
class WebCache:
    def __init__(self, cache_dir='.web_cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_md5_hash(self, url):
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _get_extension(self, content_type):
        extension = mimetypes.guess_extension(content_type)
        if extension is None:
            extension = '.html'  # Fallback to .html if no extension is found
        return extension

    def _get_cache_path(self, url, content_type):
        filename = self._get_md5_hash(url) + self._get_extension(content_type)
        return (os.path.join(self.cache_dir, filename), self._get_extension(content_type))

    def get(self, url):
        # Generate the file path
        hash_key = self._get_md5_hash(url)
        cached_files = [f for f in os.listdir(self.cache_dir) if f.startswith(hash_key)]
        if cached_files:
            logger.debug(f"Cache hit for URL: {url}")
            extension = os.path.splitext(cached_files[0])[1]
            # if the file is empty, return None
            if os.path.getsize(os.path.join(self.cache_dir, cached_files[0])) == 0:
                return (None, None)
            
            with open(os.path.join(self.cache_dir, cached_files[0]), 'rb') as file:
                return (file.read(), extension.strip("."))

        logger.debug(f"Cache miss for URL: {url}. Downloading...")
        # Fetch the content from the web
        response = None
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to dowload {url} {e}.")
            # create an empty file to avoid repeated download attempts
            with open(os.path.join(self.cache_dir, hash_key + ".html"), 'w') as file:
                pass
            return (None, None)

        # Get the content type and file path
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        cache_path, extension = self._get_cache_path(url, content_type)

        # Save the content to the cache
        with open(cache_path, 'wb') as file:
            file.write(response.content)

        return (response.content, extension.strip("."))
