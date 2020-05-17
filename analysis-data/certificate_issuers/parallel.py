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

# Must not have more than this many processes open
OPEN_LIMIT = 100

# Must not have more than this many fraction of open processes run in parallel
PARALLEL_LIMIT = 1

# Time in seconds to let parallel processes continue running before switching to a different batch
BATCH_RUN_TIME = 2

# Python 3 path
python3_path = "python"

# Experiment type
experimentType = "nakedHTTPS"


# Python 3 refactored version of https://github.com/davedash/Alexa-Top-Sites
def alexa_etl():
    f = open("../top-1m.csv.zip", "rb")
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


# DIRECTORIES FOR STORING RESULTS
base_dir = "/tmp/"
folders = ["resultsDetailed", "resultsDetailed/logs", "resultsDetailed/links", "resultsDetailed/summary",
           "resultsDetailed/nakedTest" ]
for folder in folders:
    if not os.path.exists(base_dir + folder):
        os.makedirs(base_dir + folder)

# FETCH DOMAINS
#allDomains = fetch_domains("alexa", 100000)
#allDomains = []
import pickle
with open('/net/data/contentdifferences/v2/bottom10k/allDomains', 'rb') as f:
    allDomains = pickle.load(f)

processes = []
done = 0
tstart = datetime.now()
# START PROCESSING

#allDomains = []
#with open("/tmp/resultsDetailed/doms_with_pagesALLs.txt") as df:
#    lines = df.readlines()
#    for line in lines:
#        allDomains.append(line.strip())

numDomainsProcess = len(allDomains)
print(numDomainsProcess)
for i in range(0, numDomainsProcess):
    if "northerntool".encode() in allDomains[i]:
        continue
    #print("Doing " + allDomains[i].decode())
    #this_p = Popen([python3_path, "certs_fetch.py", allDomains[i]])
    this_p = Popen([python3_path, "inaccessible.py", allDomains[i], experimentType, base_dir + "resultsDetailed"])
    os.kill(this_p.pid, signal.SIGSTOP)
    processes.append(this_p)
    while len(processes) >= OPEN_LIMIT or (i == numDomainsProcess-1 and len(processes) != 0):
        # Find out # of new processes to run
        TEMP_LIMIT = int(math.ceil(PARALLEL_LIMIT * OPEN_LIMIT))
        if len(processes) < TEMP_LIMIT:
            TEMP_LIMIT = len(processes)

        for p in processes:
            if psutil.Process(p.pid).status() != psutil.STATUS_STOPPED:
                TEMP_LIMIT -= 1

        # Run new processes, make sure we don't exhaust the same domain by randomly selecting processes
        if TEMP_LIMIT > 0:
            random.shuffle(processes)
            [os.kill(p.pid, signal.SIGCONT) for p in processes[:TEMP_LIMIT]]

        # If our processes don't give up control by default
        # if experimentType == "nakedTest":
        #     # Continue running
        #     time.sleep(BATCH_RUN_TIME)
        #
        #     # Stop all
        #     [os.kill(p.pid, signal.SIGSTOP) for p in processes[:]]

        # Clean-up if necessary
        for p in processes:
            if p.poll() is not None:
                processes.remove(p)
                done += 1
                #print("Done # " + str(done))
                #tend = datetime.now()
                #print(tend - tstart)
                #with open(base_dir + "resultsDetailed" + "/time-dist.txt", "a") as tfile:
                #    tfile.write(str(done) + "," + str((tend - tstart).total_seconds()) + "\n")
