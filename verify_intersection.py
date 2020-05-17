import requests
import time
from multiprocessing import Process
import random
from bs4 import BeautifulSoup
from bs4.element import Comment
from string import digits, punctuation
remove_digits = str.maketrans('', '', digits + punctuation)

domains_found = []
with open("v2Results/cd-verify-results-strict.txt") as in_f:
    for line in in_f.readlines():
        items = line.split("***")
        assert len(items) == 5
        domains_found.append(items[0].strip())

missing_results = {}
with open("v2Results/diffresultsALL-strict.txt") as in_f:
    for line in in_f.readlines():
        items = line.split("***")
        assert len(items) == 6
        if items[0].strip() not in domains_found:
            if items[0].strip() not in missing_results:
                missing_results[items[0].strip()] = []
            missing_results[items[0].strip()].append(items[1].strip())

print(len(missing_results))


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


def cd_verify(urls):
    time.sleep(random.randint(1,10))
    for url in urls:
        time.sleep(5)
        try:
            again_https_req = requests.get("https://" + url, timeout=60).content
            again_https = find_ngrams(
                text_from_html(again_https_req).lower().translate(remove_digits).split(), 5)
            time.sleep(5)
            again_http_requ = requests.get("http://" + url, timeout=60).content
            #print('http-equiv=\"refresh\"'.decode() in again_http_requ, 'http-equiv=\"refresh\"'.decode() in again_https_req)
            again_http2 = find_ngrams(
                text_from_html(again_http_requ).lower().translate(remove_digits).split(), 5)
        except Exception as e:
            #print(repr(e))
            print("excepting at again_http...")
            continue
        dist2 = 1 - jaccard_similarity(again_http2, again_https)
        # Confirm that the difference in http / https still exists
        if dist2 > 0.1:

            # Skip the step for comparing baseline http / http difference
            dist_base = 1 - jaccard_similarity(again_http2, again_http2)
            if dist_base + 0.1 < dist2:

                again_https_struct = find_ngrams(
                    text_from_html(again_https_req, just_tags=True).lower().translate(
                        remove_digits).split(), 5)
                again_http_struct = find_ngrams(
                    text_from_html(again_http_requ, just_tags=True).lower().translate(
                        remove_digits).split(), 5)

                dist3 = 1 - jaccard_similarity(again_http_struct, again_https_struct)
                if dist3 > 0.4:
                    with open("/data-analysis/v2Results/verify_intersection_results_diff2-strict.txt", "a") as out_f:
                        out_f.write(dom + "*-*-*" + url + "*-*-*" + repr(again_http_requ) + "*-*-*" + repr(again_https_req) + "\n")
                    return


def inac_verify(urls):
    time.sleep(random.randint(1,10))
    for url in urls:
        success_https = True
        success_http = True

        time.sleep(5)
        try:
            again_https_req = requests.get("https://" + url, timeout=45, verify=False)
            again_https_req.raise_for_status()
        except Exception as e:
            success_https = False
            error = repr(e)

        time.sleep(5)
        try:
            again_http_req = requests.get("http://" + url, timeout=45, verify=False)
            again_http_req.raise_for_status()
        except Exception as e:
            success_http = False

        if success_http and not success_https:
            with open("/data-analysis/v2Results/verify_intersection_results.txt", "a") as out_f:
                out_f.write(dom + "***" + url + "\n")
            return


processes = []
count = 0
for dom in missing_results:
    p = Process(target=cd_verify, args=(missing_results[dom],))
    processes.append(p)
    p.start()
    while len(processes) >= 50:
        for px in processes:
            px.join(0.1)
            if not px.is_alive():
                processes.remove(px)
                count += 1
                print("DONE #", count)
for p in processes:
    p.join()
    processes.remove(p)
