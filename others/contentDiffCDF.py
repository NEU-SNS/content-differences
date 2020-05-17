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

results_file = "/tmp/resultsDetailed/bt-diff-cdf.txt"

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


def text_from_html(body, just_tags=False):
    soup = BeautifulSoup(body, 'html.parser')
    if just_tags:
        return u" ".join([tag.name for tag in soup.find_all()])
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


# Process domain file for content difference results
def process_domain_file(summarylines, dname):
        #print(len(summarylines))
        for line in summarylines:
            try:
                line = line.decode()
            except Exception as e:
                print(dname, e)
                pass
            results = line.strip().split("***")
            try:
                assert len(results) == 14
            except:
                continue

            url = results[0]
            http_success = results[2]
            https_success = results[3]

            if http_success == https_success == "True":
                content_http = results[12]
                content_https = results[13]

                #if True:
                if content_http != content_https:
                    try:
                        content_http = base64.b64decode(content_http.encode())
                        content_https = base64.b64decode(content_https.encode())
                        content_http_vis = find_ngrams(
                            text_from_html(content_http).lower().translate(remove_digits).split(), 5)
                        content_https_vis = find_ngrams(
                            text_from_html(content_https).lower().translate(remove_digits).split(), 5)
                        
                        content_http_style = find_ngrams(text_from_html(content_http, just_tags=True).lower().translate(remove_digits).split(), 5)
                 
                        content_https_style = find_ngrams(text_from_html(content_https, just_tags=True).lower().translate(remove_digits).split(), 5)

                    except Exception as e:
                        #print(repr(e))
                        #print("excepting at decoding/shingling/ngrams...")
                        continue

                    dist1 = 1 - jaccard_similarity(content_http_vis, content_https_vis)
                    dist2 = 1 - jaccard_similarity(content_http_style, content_https_style)
                    
                    #print(url, abs(dist1 - dist2), dist_base, dist3)
                    with open(results_file, 'a') as resultsf:
                        fcntl.flock(resultsf, fcntl.LOCK_EX)
                        resultsf.write(dname + " * " + str(dist1) + " * " + str(dist2) + "\n") 
                        fcntl.flock(resultsf, fcntl.LOCK_UN)
                    return

# DO IT ON TOP 10k ONLY
#from os import listdir
#from os.path import isfile, join
#mypath = "/net/data/contentdifferences/resultsDetailedtop10k/summary/"
#onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
#count = 0
#for f in onlyfiles:	
#    with open(join(mypath, f)) as s_file:
#        lines = s_file.readlines()
#        process_domain_file(lines, f)
#    print("Done with ", count, "...")
#    count += 1
#exit(0)

def process_zip_file(zip_file):
    time.sleep(randint(1,10))
    empty_count = 0
    with ZipFile(zip_file, 'r') as zfile:
        slines = []
        processes_summary = []
        for name in zfile.namelist():
            if "summary/summary-" in name:
                print(name)
                dname = name[name.find("summary/summary-")+16:name.rfind('.txt')].strip()
                if dname.startswith("www."):
                    dname = dname.replace("www.", "", 1)
                #flag = False
                #for spd in second_pass_domains:
                #    if spd.endswith(dname):
                #        flag = True
                #        print(spd, dname)
                #        break
                #if not flag:
                #    continue

                try:
                    with zfile.open(name) as sfile:
                        sline = sfile.readlines()
                        if not sline:
                            empty_count += 1
                except:
                    continue
                slines.append(0)
                if len(sline) == 0:
                    #print("empty file...")
                    continue
                sp = Process(target=process_domain_file, args=(sline,dname,))
                processes_summary.append(sp)
                sp.start()
                while len(processes_summary) >= 100:
                    for xp in processes_summary:
                        xp.join(0.1)
                        if not xp.is_alive():
                            processes_summary.remove(xp)
        for xp in processes_summary:
            xp.join()
    
    return

#second_pass_domains = []
#with open(doms_file, "r") as f:
#    second_pass_domains = f.read().splitlines()
#    second_pass_domains = [d.strip() for d in second_pass_domains]
#print(len(second_pass_domains))

zip_files = []
for zfile in os.listdir("/"):
    if zfile.endswith(".zip"):
        zip_files.append(os.path.join("/", zfile))
count = 200
print(len(zip_files))
shuffle(zip_files)
processes = []
for zip_file in zip_files:
    #print("Entering zip ", zip_file)
    p = Process(target=process_zip_file, args=(zip_file,))
    processes.append(p)
    p.start()
    while len(processes) >= 100:
        for p in processes:
            p.join(0.1)
            if not p.is_alive():
                processes.remove(p)
    count -= 1
    if count <= 0:
        break
for p in processes:
    p.join()
