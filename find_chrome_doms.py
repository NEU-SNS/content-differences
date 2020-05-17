import os
import signal
import random
from bs4 import BeautifulSoup
import requests
from subprocess import Popen
import time
import math
import psutil
import zipfile
from io import BytesIO
from datetime import datetime
import tldextract


# Python 3 refactored version of https://github.com/davedash/Alexa-Top-Sites
def alexa_etl():
    f = open("top-1m.csv.zip", "rb")
    buf = BytesIO(f.read())
    zfile = zipfile.ZipFile(buf)
    buf = BytesIO(zfile.read('top-1m.csv'))
    for line in buf:
        (rank, domain) = line.split(b',')
        yield (int(rank), domain.strip())


def alexa_top_list(num = 100):
    a = alexa_etl()
    return [a.__next__() for x in range(num)]


def fetch_domains(type = "alexa", n = 1000):
    if type is "alexa":
        domainsListAlexa = alexa_top_list(n)

        # Remove the tuple formatting
        for i in range(len(domainsListAlexa)):
            domainsListAlexa[i] = domainsListAlexa[i][1]

        return domainsListAlexa[:n]
    elif type is "httpseverywhere":
        # Fetch all domains from the HTTPSEverywhere list
        chars = "abcdefghijklmnopqrstuvwxyz"
        allDomains = []
        for c in chars:
            domainsList = 'https://www.eff.org/https-everywhere/atlas/letters/' + c + '.html'
            res = requests.get(domainsList)
            soup = BeautifulSoup(res.text, 'html.parser')
            allDomains.extend(soup.findAll("li"))

        # Select only the domain name from each HTML element
        for i in range(len(allDomains)):
            allDomains[i] = allDomains[i].get_text()

        # Shuffle domains to discard the alphabetical fetch order
        # random.shuffle(allDomains)

        return allDomains[1:n]
    elif type is "universities":
        lines = [line.rstrip('\n') for line in open('university-sites.txt')]
        random.shuffle(lines)
        return lines[1:n]
    else:
        return []


allDomains = fetch_domains("alexa", 100000)
allDomainsFormatted = []
for d in allDomains:
    df = d.decode()
    if df.startswith("www."):
        df = df.replace("www.", "", 1)
    allDomainsFormatted.append(df.replace("www.", "", 1))

# Find 100 domains with 0 inconsistencies of both types
inconsistencyDomains = []
with open("analysis-data/v2Results/inacresultsALL-withouTIMEOUTwithoutCONNECTION.txt") as inac_f:
    for line in inac_f.readlines():
        if line.split("***")[0].strip() not in inconsistencyDomains:
            inconsistencyDomains.append(line.split("***")[0].strip())
with open("analysis-data/v2Results/diffresultsALL.txt") as inac_f:
    for line in inac_f.readlines():
        if line.split("***")[0].strip() not in inconsistencyDomains:
            inconsistencyDomains.append(line.split("***")[0].strip())

# Also make sure the domains are those for which original pipeline crawled 250 links
sizeDomains = {}
with open("analysis-data/v2Results/top100k/numpagesresults.txt") as inac_f:
    for line in inac_f.readlines():
        if int(line.split(" *** ")[1].strip()) >= 250:
            d = line.split(" *** ")[0].strip()
            if d.startswith("www."):
                d = d.replace("www.", "", 1)
            sizeDomains[d] = line.split(" *** ")[1].strip()

# Bucket into popularity
numBuckets = 100
buckets = {}
for i in range(0, numBuckets):
    buckets[i] = []

counter = 100
while True:
    if counter == 100100:
        break

    if allDomainsFormatted[counter] in inconsistencyDomains or allDomainsFormatted[counter] not in sizeDomains.keys():
        counter += 1
        continue
    else:
        buckets[math.floor(counter / 1000)].append(allDomainsFormatted[counter])
        counter = round(counter, -3) + 1000 + 100

with open("chrome_doms", "w") as cd:
    for i in buckets:
        print(i, buckets[i][0], allDomainsFormatted.index(buckets[i][0]), sizeDomains[buckets[i][0]])
        assert buckets[i][0] not in inconsistencyDomains
        cd.write(buckets[i][0] + "\n")
