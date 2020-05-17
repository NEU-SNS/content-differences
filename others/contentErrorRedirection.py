from random import shuffle
from random import randint

import os
from multiprocessing import Process
import base64
from bs4 import BeautifulSoup
from bs4.element import Comment
import requests
from string import digits, punctuation
remove_digits = str.maketrans('', '', digits + punctuation)
import time
import fcntl
from zipfile import ZipFile

results_file = "/tmp/resultsDetailed/error-redirection.txt"
count_file = "/tmp/resultsDetailed/error-redirection-zips.txt"

# Helper functions
def find_ngrams(s, n):
      input_list = s
      return [''.join(elem) for elem in list(zip(*[input_list[i:] for i in range(n)]))]


def jaccard_similarity(list1, list2):
    s1 = set(list1)
    s2 = set(list2)
    x = len(s1.union(s2))
    if x == 0:
        return 1
    return len(s1.intersection(s2)) / x


def tag_visible(element):
        if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
            return False
        if isinstance(element, Comment):
            return False
        return True


def text_from_html(body, just_tags = False):
        soup = BeautifulSoup(body, 'html.parser')
        if just_tags: 
            return u" ".join([tag.name for tag in soup.find_all()])
        texts = soup.findAll(text=True)
        visible_texts = filter(tag_visible, texts)
        return u" ".join(t.strip() for t in visible_texts)


# Process domain file for results
def process_domain_file(summarylines):
        time.sleep(randint(1,10))
        for line in summarylines:
            line = line.decode()
            results = line.strip().split("***")
            try:
                assert len(results) == 14
            except:
                continue

            url = results[0]
            if url.startswith("www."):
                url.replace("www.", "", 1)
            url = url.split("?")[0]
            url_path = [z for z in url.split("/", 1) if z]
            if len(url_path) < 2:
                continue
            else:
                url_path = url_path[1]

            http_success = results[2]
            https_success = results[3]            

            if http_success == https_success and http_success == "True":
                url_http = results[6][1:-1]
                url_https = results[7][1:-1]
                if "https://" in url_http and "https://" in url_https and url_path in url_https:
                    #print("entering,,,")
                    url_http = url_http.replace('https://', '')
                    url_https = url_https.replace('https://', '')
                    elem_http = [z for z in url_http.split('/') if z]
                    elem_https = [z for z in url_https.split('/') if z]
                    if len(elem_http) == 1 and len(elem_https) > 1:
                        print(results[0], results[6], results[7])
                        with open(results_file, 'a') as resultsf:
                            fcntl.flock(resultsf, fcntl.LOCK_EX)
                            resultsf.write(results[0] + " *** " + results[6] + " *** " + results[7] + "\n")
                            fcntl.flock(resultsf, fcntl.LOCK_UN)                                                         
                        return
                        
def process_zip_file(zip_file):
    time.sleep(randint(1,10))
    empty_count = 0
    with ZipFile(zip_file, 'r') as zfile:
        slines = []
        processes_summary = []
        for name in zfile.namelist():
            if "summary/summary-" in name:
                with zfile.open(name) as sfile:
                    sline = sfile.readlines()
                    if not sline:
                        empty_count += 1
                slines.append(0)
                if len(sline) == 0:
                    #print("empty file...")
                    continue
                sp = Process(target=process_domain_file, args=(sline,))
                processes_summary.append(sp)
                sp.start()
                while len(processes_summary) >= 156:
                    for xp in processes_summary:
                        xp.join(0.1)
                        if not xp.is_alive():
                            processes_summary.remove(xp)
        for xp in processes_summary:
            xp.join()

        with open(count_file, 'a') as countf:
             fcntl.flock(countf, fcntl.LOCK_EX)
             countf.write(str(zip_file) + " " + str(len(slines)) + " " + str(empty_count) + "\n")
             fcntl.flock(countf, fcntl.LOCK_UN)
    return

def process_zip_file_slow(zip_file):
    empty_count = 0
    with ZipFile(zip_file, 'r') as zfile:
        slines = []
        for name in zfile.namelist():
            if "summary/summary-" in name:
                with zfile.open(name) as sfile:
                    sline = sfile.readlines()
                    if not sline:
                        empty_count += 1
                        continue
                slines.append(sline)
        with open(count_file, 'a') as countf:
            fcntl.flock(countf, fcntl.LOCK_EX)
            countf.write(str(zip_file) + " " + str(len(slines)) + " " + str(empty_count) + "\n")
            fcntl.flock(countf, fcntl.LOCK_UN)

        shuffle(slines)
        processes_summary = []
        for sline in slines:
            if (len(sline)) == 0:
                continue
            sp = Process(target=process_domain_file, args=(sline, ))
            processes_summary.append(sp)
            sp.start()
            while len(processes_summary) >= 64:
                for xp in processes_summary:
                    xp.join(0.1)
                    if not xp.is_alive():
                        processes_summary.remove(xp)
        for xp in processes_summary:
            xp.join()
    return

zip_files = []
for zfile in os.listdir("/"):
    if zfile.endswith(".zip"):
        zip_files.append(os.path.join("/", zfile))
count = 300
shuffle(zip_files)
processes = []
for zip_file in zip_files:
    # print("Entering domain ", domain_file)
    p = Process(target=process_zip_file, args=(zip_file, ))
    processes.append(p)
    p.start()
    while len(processes) >= 18:
        for p in processes:
            p.join(0.1)
            if not p.is_alive():
                processes.remove(p)
    count -= 1
    if count <= 0:
        break
for p in processes:
    p.join()
