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

results_file = "/tmp/resultsDetailed/numreasonsresults.txt"
count_file = "/tmp/resultsDetailed/numreasonscount.txt"
with open(results_file, 'w') as rf:
    rf.write("")
with open(count_file, 'w') as cf:
    cf.write("")

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
def process_log_file(summarylines, dname):
    for line in summarylines:
        if " from a set of " in line.decode() and line.decode().split(" from a set of ")[1].strip() == "0":        
            if "url not allowed to crawl during get_all_anchor_links() phase" in summarylines[1].decode():
                reason = summarylines[1].decode().split(",")[1].strip()
            else:
                reason = "unknown"

            with open(results_file, 'a') as resultsf:
                fcntl.flock(resultsf, fcntl.LOCK_EX)
                resultsf.write(dname + " *** " + reason + "\n")
                fcntl.flock(resultsf, fcntl.LOCK_UN)
            return

def process_zip_file(zip_file):
    time.sleep(randint(1,10))
    empty_count = 0
    with ZipFile(zip_file, 'r') as zfile:
        slines = []
        processes_summary = []
        for name in zfile.namelist():
            if ".log" in name:
                print(name)
                dname = name[name.find("/logs/")+6:name.rfind('.log')].strip()

                try:
                    with zfile.open(name) as sfile:
                        sline = sfile.readlines()
                        if not sline:
                            empty_count += 1
                except:
                    print("excepting at zfile open...")
                    continue
                slines.append(0)
                if len(sline) == 0:
                    print("empty file...")
                    continue
                sp = Process(target=process_log_file, args=(sline,dname,))
                processes_summary.append(sp)
                sp.start()
                while len(processes_summary) >= 150:
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

zip_files = []
for zfile in os.listdir("/"):
    if zfile.endswith(".zip"):
        zip_files.append(os.path.join("/", zfile))
count = 1000
shuffle(zip_files)
print(len(zip_files))
processes = []
for zip_file in zip_files:
    print("Entering zip ", zip_file)
    p = Process(target=process_zip_file, args=(zip_file, ))
    processes.append(p)
    p.start()
    while len(processes) >= 70:
        for p in processes:
            p.join(0.1)
            if not p.is_alive():
                processes.remove(p)
    count -= 1
    if count <= 0:
        break
for p in processes:
    p.join()
