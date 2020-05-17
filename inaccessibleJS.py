from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import random
import time
from multiprocessing import Process
import tldextract
import sys
import pickle
import signal
from reppy.robots import Robots
import fcntl, os
import base64
from chrome_fetch.chrome_fetch import fetch_content_with_status

from bs4.element import Comment
from string import digits, punctuation

# Custom user agent to notify the destination about purpose of crawl
uaCustom = "Custom user agent"

# Time to sleep after processing each link, so to not overwhelm the destination
sleepTime = 0

# Stop after fetching this many unique links
totalLinks = 250

# Give up processing after finishing the current thread
giveProcess = True

# Timeout set during requests functions
timeOut = 30

# Helper functions
remove_digits = str.maketrans('', '', digits + punctuation)

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

def text_from_html(body):
    soup = BeautifulSoup(body, 'html5lib')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

# Technique using shingling + jaccard_distance + threshold found by CDF for top10k domains
def similar_body(content_http, content_https):
    if content_http == content_https:
        return True
    else:
        return False
    
    content_http = find_ngrams(text_from_html(content_http).lower().translate(remove_digits).split(), 5)
    content_https = find_ngrams(text_from_html(content_https).lower().translate(remove_digits).split(), 5) 
    if (1 - jaccard_similarity(content_http, content_https)) <= 0.05:
        return True
    else:
        return False

# Naked HTTPS test
def naked_test(domain):
    success_https_naked = True
    success_https = True
    success_http = True
    success_http_naked = True

    final_url_https_naked = "_"
    final_url_https = "_"
    final_url_http = "_"
    final_url_http_naked = "_"
    error_https_naked = "_"
    error_https = "_"
    error_http = "_"
    error_http_naked = "_"

    headers = {'User-Agent': uaCustom}

    # Try retrieving the domain naked HTTP
    try:
        response_http_naked = requests.get('http://' + domain, timeout=timeOut, headers=headers)
        response_http_naked.raise_for_status()
        final_url_http_naked = response_http_naked.url
    # Any error i.e. ssl validation, 404 etc.
    except requests.exceptions.RequestException as e:
        success_http_naked = False
        error_http_naked = repr(e)

    # Try retrieving the domain HTTP
    try:
        response_http = requests.get('http://www.' + domain, timeout=timeOut, headers=headers)
        response_http.raise_for_status()
        final_url_http = response_http.url
    # Any error i.e. ssl validation, 404 etc.
    except requests.exceptions.RequestException as e:
        success_http = False
        error_http = repr(e)

    time.sleep(sleepTime)
    if giveProcess:
        os.kill(os.getpid(), signal.SIGSTOP)

    # Try retrieving the domain naked HTTPS
    try:
        response_https_naked = requests.get('https://' + domain, timeout=timeOut, headers=headers)
        response_https_naked.raise_for_status()
        final_url_https_naked = response_https_naked.url
    # Any error i.e. ssl validation, 404 etc.
    except requests.exceptions.RequestException as e:
        success_https_naked = False
        error_https_naked = repr(e)

    # Try retrieving the domain (www) HTTPS
    try:
        response_https = requests.get('https://www.' + domain, timeout=timeOut, headers=headers)
        response_https.raise_for_status()
        final_url_https = response_https.url
    # Any error i.e. SSL validation, 404 etc.
    except requests.exceptions.RequestException as e:
        success_https = False
        error_https = repr(e)

    # Write results
    fileh = open(results_dir + "/nakedTest/" + domain + '.txt', 'a+')
    fileh.write(str(success_https_naked) + "***" +
                str(success_https) + "***" +
                str(success_http_naked) + "***" +
                str(success_http) + "***" +
                final_url_https_naked + "***" +
                final_url_https + "***" +
                final_url_http_naked + "***" +
                final_url_http + "***" +
                error_https_naked + "***" +
                error_https + "***" +
                error_http_naked + "***" +
                error_http + "\n")
    fileh.close()


# Do our policies allow us to access a particular url
# Return a bool with error, if any
def allowed_to_crawl(url, visit_check=True):
    # First check if we did not already visit the url
    if visit_check:
        if url not in visitedLinks:
            visitedLinks.add(url)
        else:
            return False, '<url visited already>'

    # Then check if the domain / sub-domain even support https, save result in cache for later use
    parsed = urlparse(url)
    domain_or_subdomain = parsed.hostname
    scheme = parsed.scheme
    if domain_or_subdomain not in httpsDomains:
        httpsDomains[domain_or_subdomain] = is_domain_https(domain_or_subdomain)

    # No need to parse the link if the host is not https friendly
    if not httpsDomains[domain_or_subdomain]:
        return False, '<domain not https friendly>'

    # Get the relevant robots.txt file for the url, save result in cache for later use
    if domain_or_subdomain not in robotParsers:
        try:
            rp = Robots.fetch(scheme + "://" + domain_or_subdomain + "/robots.txt", timeout=timeOut)
            robotParsers[domain_or_subdomain] = rp
        except:
            robotParsers[domain_or_subdomain] = None

    # Finally check if robots.txt allow crawling for this url
    if robotParsers[domain_or_subdomain] is not None:
        try:
            return robotParsers[domain_or_subdomain].allowed(url, "*"), '<robots.txt check>'
        except:
            pass

    # If we don't have robots.txt or any other misc error occurs
    return True, ''


# Accesses the given domain over both HTTP and HTTPS ports, returns True if success
def is_domain_https(domain):
    headers = {'User-Agent': uaCustom}
    # Try retrieving the page HTTP
    try:
        response = requests.get('http://' + domain, timeout=timeOut, headers=headers, proxies=proxies, allow_redirects=True)
        response.raise_for_status()
    # Page not found etc.
    except requests.exceptions.RequestException as e:
        # print 'Error for HTTP: ' + domain
        # print e
        return False

    time.sleep(sleepTime)
    if giveProcess:
        os.kill(os.getpid(), signal.SIGSTOP)

    # Try retrieving the page HTTPS
    try:
        response = requests.get('https://' + domain, timeout=timeOut, headers=headers, proxies=proxies, allow_redirects=True)
        response.raise_for_status()
    # Page not found etc.
    except requests.exceptions.RequestException as e:
        # print 'Error for HTTPs: ' + domain
        # print e
        return False
    return True


# Assess if the page is different over any one of the two ports i.e. HTTP or HTTPS
# For now we are only assessing differences in the response headers / status_code
def is_page_different(url, domain):
    try:
        allowed, err_msg = allowed_to_crawl(url, visit_check=False)
        if not allowed:
            logfile.write("url not allowed to crawl during is_page_different() phase: " + url + ", " + err_msg + "\n")
            return 0

        # Remove the protocol from the url
        url = url.replace("http://", "", 1)
        url = url.replace("https://", "", 1)

        success_http = True
        success_https = True

        # 2.0: Try retrieving the page HTTP
        success_http, error_http, response_http_url, headers_http, body_http = \
            fetch_content_with_status('http://' + url)

        time.sleep(sleepTime)
        if giveProcess:
            os.kill(os.getpid(), signal.SIGSTOP)

        # 2.0: Try retrieving the page HTTPS
        success_https, error_https, response_https_url, headers_https, body_https = \
            fetch_content_with_status('https://' + url)

        # Don't store entire response if there's no indication of content-difference
        if similar_body(body_http, body_https):
            body_http = "<similar body>"
            body_https = "<similar body>"
        else:
            # base64 encoding makes storing in a txt file easy
            body_http = base64.b64encode(body_http).decode()
            body_https = base64.b64encode(body_https).decode()

        # Store all results
        fileh = open(results_dir + "/summary/summary-" + domain + '.txt', 'a')
        fileh.write(
             url + "***" +
             references[link] + "***" +
             str(success_http) + "***" +
             str(success_https) + "***" +
             repr(error_http) + "***" +
             repr(error_https) + "***" +
             repr(response_http_url) + "***" +
             repr(response_https_url) + "***" +
             # @todo: If we want timing info; did not find meaningful results earlier
             "" + "***" +
             "" + "***" +
             # time_http + "***" +
             # time_https + "***" +
             repr(headers_http) + "***" +
             repr(headers_https) + "***" +
             body_http + "***" +
             body_https + "\n")
        fileh.close()

        return success_http != success_https
    except Exception as e:
        raise(e)


# Returns the list of all href and img src in html pages, starting from a root url
def get_all_anchor_links(page_url, domain):
    global all_links, totalTryLinks, references

    allowed, err_msg = allowed_to_crawl(page_url, visit_check=True)
    if allowed:
        success, error, response_url, headers, body = \
            fetch_content_with_status(page_url)

        if not success:
            logfile.write("visited: " + page_url + ", page fetch exception: " + repr(error) + "\n")
            # print e
            return

        if "content-type" in headers:
            if "html" not in headers['content-type']:
                # Log
                logfile.write("visited: " + page_url + ", content-type not html" + "\n")
                return
        else:
            logfile.write("visited: " + page_url + ", content-type field not found" + "\n")
            return

        bs = BeautifulSoup(body, features='html5lib')
        this_page_links = set()

        # <a> links
        for link in bs.findAll('a'):
            temp = link.get('href')
            if temp is not None \
                    and temp.startswith("#") is not True \
                    and "mailto" not in temp:
                temp = urljoin(response_url, temp)
                if domain.replace("www.", "") in urlparse(temp)[1]:
                    all_links.add((temp.strip()))
                    this_page_links.add(temp.strip())
                    references[temp.strip()] = repr(response_url)

        # <img> links
        '''
        for image in bs.findAll('img'):
            img = image.get('src')
            if img is not None:
                img = urljoin(page.url, img)
                if domain.replace("www.", "") in urlparse(img)[1]:
                    all_links.add((img.strip()))
                    this_page_links.add(img)
                    references[img] = page.url
        '''

        # Log
        logfile.write("visited: " + page_url + ", found: " + str(len(this_page_links)) + " links" + "\n")

        # Traverse recursively until a threshold number of links have been retrieved
        list_links = list(all_links)
        random.shuffle(list_links)
        for link in list_links:
            if len(all_links) < totalLinks:
                time.sleep(sleepTime)
                if giveProcess:
                    os.kill(os.getpid(), signal.SIGSTOP)
                get_all_anchor_links(link, domain)
    else:
        logfile.write("url not allowed to crawl during get_all_anchor_links() phase: " + page_url + ", " + err_msg + "\n")


# ARGUMENTS
domain_name = sys.argv[1].strip()
experiment_type = sys.argv[2]
results_dir = sys.argv[3]

# GLOBALS
references = {}
robotParsers = {}
httpsDomains = {}
visitedLinks = set()
all_links = set()

# FOR ENABLING TOR ROUTING
proxies = {
    # 'http': 'socks5h://localhost:9050',
    # 'https': 'socks5h://localhost:9050'
}

# START
try:
    # Don't crawl hosts, just study differences at the index pages
    if experiment_type == "nakedHTTPS":
        naked_test(domain_name)

    # For other experiments, we append www reference for robustness
    if tldextract.extract(domain_name).subdomain == '' and not domain_name.startswith("www."):
        domain_name = "www." + domain_name
    logfile = open(results_dir + "/logs/" + domain_name + ".log", 'a+')

    # In phase 1, we crawl the links that we'd be doing our analysis over
    if experiment_type == "inDepth-Phase1" or experiment_type == "inDepth-allPhases":
        logfile.write("started crawling " + domain_name + "..." + "\n")
        get_all_anchor_links("http://" + domain_name, domain_name)
        logfile.write("finding inaccessible links for " + domain_name + " from a set of " + str(len(all_links)) + "\n")
        # print("domain: ", domain_name, " ", " length: ", str(len(all_links)))

        with open(results_dir + "/links/" + domain_name + "-links.txt", 'wb') as al:
           pickle.dump(all_links, al)
        with open(results_dir + "/links/" + domain_name + "-references.txt", 'wb') as ref:
           pickle.dump(references, ref)

    # In phase 2, we use the recorded links and access them over HTTPvsHTTPS ports to study differences
    if experiment_type == "inDepth-Phase2" or experiment_type == "inDepth-allPhases":
        results = {domain_name: []}
        #with open(results_dir + "/links/" + domain_name + "-links.txt", 'rb') as al:
        #    all_links = pickle.load(al)
        #with open(results_dir + "/links/" + domain_name + "-references.txt", 'rb') as ref:
        #    references = pickle.load(ref)

        # Respect the limits set
        while len(all_links) > totalLinks:
            all_links.pop()
        processes = []
        for link in all_links:
            if is_page_different(link, domain_name):
                results[domain_name].append('')
            time.sleep(sleepTime)
            if giveProcess:
                os.kill(os.getpid(), signal.SIGSTOP)

        logfile.write("# of inaccessible links for " + domain_name + ": " + str(len(results[domain_name])) + "\n")

        # Make sure we have a summary file even if no links were processed for the domain
        with open(results_dir + "/summary/summary-" + domain_name + '.txt', 'a') as fileh:
            pass

        # Write to the list of done domains, so a cleanup process can zip the resulting files
        with open(results_dir + '/doneDomains.txt', 'a') as dd:
            fcntl.flock(dd, fcntl.LOCK_EX)
            dd.write(domain_name + "\n")
            fcntl.flock(dd, fcntl.LOCK_UN)

        logfile.close()

except Exception as e:
    with open(results_dir + '/misce.txt', 'a') as misce:
        misce.write("misc error for " + domain_name + ": " + repr(e) + "\n")
