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

results_file = "/tmp/resultsDetailed/inacresults.txt"
count_file = "/tmp/resultsDetailed/inaccount.txt"

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


# Process domain file for content difference results
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
            http_success = results[2]
            https_success = results[3]
            https_error = results[5]

            if http_success != https_success and http_success == "True":
                #error = https_error
                #error_stripped = error[:error.find('(')]
                #if error_stripped == "HTTPError":
                #    error_stripped = error[error.find('(') + 2:error.find(':')]
                if True:
                        success_https = True
                        success_http = True

                        try:
                            again_https_req = requests.get("https://" + url, timeout=15)
                            again_https_req.raise_for_status()
                        except Exception as e:
                            success_https = False
                            error = repr(e)

                        time.sleep(20)
                        
                        try:
                            again_http_req = requests.get("http://" + url, timeout=15)
                            again_http_req.raise_for_status()
                        except Exception as e:
                            success_http = False

                        if success_http and not success_https:
                            error_stripped = error[:error.find('(')]
                            if error_stripped == "HTTPError":
                                error_stripped = error[error.find('(') + 2:error.find(':')]
                            print(url, error_stripped)

                            if "Timeout" not in error_stripped and "Connection" not in error_stripped:
                                with open(results_file, 'a') as resultsf:
                                    fcntl.flock(resultsf, fcntl.LOCK_EX)
                                    resultsf.write(url + " *** " + error_stripped + "\n")
                                    fcntl.flock(resultsf, fcntl.LOCK_UN)
                                return
                        
                        time.sleep(20)

def process_zip_file(zip_file):
    empty_count = 0
    with ZipFile(zip_file, 'r') as zfile:
        slines = []
        for name in zfile.namelist():
            if "summary/summary-" in name:
                with open('/tmp/resultsDetailed/domains-info-in-zips.txt', 'a') as resultsf:
                    fcntl.flock(resultsf, fcntl.LOCK_EX)
                    resultsf.write(name[name.find("summary/summary-")+16:name.rfind('.txt')]  + "\n")
                    fcntl.flock(resultsf, fcntl.LOCK_UN)
                                                                                                                                        
                print(name[name.find("summary/summary-")+16:name.rfind('.txt')])
                #with zfile.open(name) as sfile:
                #    sline = sfile.readlines()
                #    if not sline:
                #        empty_count += 1
                #slines.append(sline)

zip_files = []
for zfile in os.listdir("/"):
    if zfile.endswith(".zip"):
        zip_files.append(os.path.join("/", zfile))
count = 500
shuffle(zip_files)
processes = []
for zip_file in zip_files:
    # print("Entering domain ", domain_file)
    p = Process(target=process_zip_file, args=(zip_file, ))
    processes.append(p)
    p.start()
    while len(processes) >= 12:
        for p in processes:
            p.join(0.1)
            if not p.is_alive():
                processes.remove(p)
    count -= 1
    if count <= 0:
        break
for p in processes:
    p.join()
