#!/usr/bin/python3

import requests
from bs4 import BeautifulSoup
import re
import sys

base_url = "https://files.kde.org/kde-linux/"

def download_file(download_url, filename):
    print(f"Start downloading from: {download_url}")
    with requests.get(download_url, stream=True) as req:
        req.raise_for_status()
        with open(filename, 'wb') as file:
            for chunk in req.iter_content(chunk_size=8192):
                file.write(chunk)
    print("Download completed")
    print(f"Downloaded file: {filename}")

def download_latest():
    url = base_url + "?C=M;O=D"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pattern = re.compile(r'kde-linux_\d+\.raw$')
    links = soup.find_all("a", href=pattern)

    if links:
        latest_href = links[0]["href"]
        download_url = base_url + latest_href
        download_file(download_url, latest_href)
    else:
        print("Raw files not found")
        sys.exit(1)

def download_specific(build_version):
    filename = f"kde-linux_{build_version}.raw"
    download_url = base_url + filename
    try:
        resp = requests.head(download_url)
        if resp.status_code != 200:
            print(f"Specified build not found: {build_version}")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking build: {e}")
        sys.exit(1)

    download_file(download_url, filename)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script.py [--latest | --build=VERSION]")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--latest":
        download_latest()
    elif arg.startswith("--build="):
        build_version = arg.split("=", 1)[1]
        if not re.fullmatch(r"\d{12}", build_version):
            print("Invalid version format. Expected format: YYYYMMDDHHMM")
            sys.exit(1)
        download_specific(build_version)
    else:
        print("Unknown argument")
        sys.exit(1)
