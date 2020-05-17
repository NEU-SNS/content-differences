from random import randint

from multiprocessing import Process
from bs4 import BeautifulSoup
from bs4.element import Comment
from string import digits, punctuation

remove_digits = str.maketrans('', '', digits + punctuation)
import time
import fcntl

results_file = "/analysis-data/v2Results/cd-verify-results-strict.txt"
input_file = "/analysis-data/v2Results/diffresultsALL-strict.txt"

from chrome_fetch.chrome_fetch import fetch_content_with_status

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


# Process domain file for content diff results
def process_line_cd(dname, urls):
    time.sleep(randint(1, 5))
    for url in urls:
        time.sleep(2)
        try:
            success_http, error_http, response_http_url, headers_http, body_http = \
                fetch_content_with_status('http://' + url)
            again_http_requ = body_http
            again_http = find_ngrams(
                text_from_html(again_http_requ).lower().translate(remove_digits).split(), 5)
            if not success_http:
                continue
            time.sleep(2)

            success_https, error_https, response_https_url, headers_https, body_https = \
                fetch_content_with_status('https://' + url)
            again_https_req = body_https
            again_https = find_ngrams(
                text_from_html(again_https_req).lower().translate(remove_digits).split(), 5)
            if not success_https:
                continue
            time.sleep(2)

            success_http, error_http, response_http_url, headers_http, body_http = \
                fetch_content_with_status('http://' + url)
            again_http_requ = body_http
            again_http2 = find_ngrams(
                text_from_html(again_http_requ).lower().translate(remove_digits).split(), 5)
            if not success_http:
                continue
        except Exception as e:
            print(repr(e))
            print("excepting at again_http...")
            continue
        dist2 = 1 - jaccard_similarity(again_http2, again_https)
        # Confirm that the difference in http / https still exists
        if dist2 > 0.4:

            # Confirm that difference is greater than baseline http / http difference
            dist_base = 1 - jaccard_similarity(again_http2, again_http)
            if dist_base + 0.2 < dist2:

                again_https_struct = find_ngrams(
                    text_from_html(again_https_req, just_tags=True).lower().translate(
                        remove_digits).split(), 5)
                again_http_struct = find_ngrams(
                    text_from_html(again_http_requ, just_tags=True).lower().translate(
                        remove_digits).split(), 5)

                dist3 = 1 - jaccard_similarity(again_http_struct, again_https_struct)
                if dist3 > 0.6:
                    # print(url, abs(dist1 - dist2), dist_base, dist3)
                    with open(results_file, 'a') as resultsf:
                        fcntl.flock(resultsf, fcntl.LOCK_EX)
                        resultsf.write(dname + "***" + url + " *** " + str(dist2) + " *** " + str(dist_base) + " *** " + str(dist3) + "\n")
                        fcntl.flock(resultsf, fcntl.LOCK_UN)

                    # While verifying we want to return as soon as one inconsistency found for the domain
                    return


# Process domain file for content inac results
def process_line_inac(dname, urls):
    for url in urls:
        try:
            success_https, error_https, response_https_url, headers_https, body_https = \
                fetch_content_with_status('https://' + url)
        except Exception as e:
            success_https = False
            error_https = repr(e)

        # time.sleep(20)

        try:
            success_http, error_http, response_http_url, headers_http, body_http = \
                fetch_content_with_status('http://' + url)
        except Exception as e:
            success_http = False

        if success_http and not success_https:
            # print(url, error_stripped)

            # if "Timeout" not in error_stripped and "Connection" not in error_stripped:
            with open(results_file, 'a') as resultsf:
                fcntl.flock(resultsf, fcntl.LOCK_EX)
                resultsf.write(dname + " *** " + url + " *** " + repr(error_https) + "\n")
                fcntl.flock(resultsf, fcntl.LOCK_UN)

            return
        # time.sleep(20)


mapping = {}
with open(input_file) as in_f:
    lines = in_f.readlines()
    for line in lines:
        items = line.strip().split("***")
        assert len(items) == 6
        dname = items[0].strip()
        url = items[1].strip()
        if dname not in mapping:
            mapping[dname] = [url]
        else:
            mapping[dname].append(url)

doms_success = []
processes = []
for domain in mapping:
    p = Process(target=process_line_cd, args=(domain,mapping[domain],))
    processes.append(p)
    print(domain)
    p.start()
    while len(processes) >= 15:
        for p in processes:
            p.join(0.1)
            if not p.is_alive():
                processes.remove(p)
for p in processes:
    p.join()
