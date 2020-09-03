import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import random
import time
from multiprocessing import Process
import sys
from bs4.element import Comment
import fcntl
from string import digits, punctuation

# Custom user agent to notify the destination about purpose of crawl
uaCustom = "HTTP/S content consistency crawl"

# Time to sleep (seconds) after processing each link, so to not overwhelm the destination
sleepTime = 0

# Maximum number of unique links to fetch
totalLinks = 250

# Timeout set during GET requests
timeOut = 30

# Number of parallel requests allowed to sent
parallelization = 32

# Where to store results
inconsistentResults = '/tmp/content-differences.txt'
inaccessibleResults = '/tmp/content-unavailabilities.txt'

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


def text_from_html(body, just_tags=False):
    soup = BeautifulSoup(body, 'html.parser')
    if just_tags:
        return u" ".join([tag.name for tag in soup.find_all()])
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


# Checks for HTTP vs HTTPS content inconsistency
def content_inconsistent(url, success_http, success_https, content_http, content_https):
    if success_http == success_https == True:
        if content_http != content_https:
            try:
                content_http = find_ngrams(
                    text_from_html(content_http).lower().translate(remove_digits).split(), 5)
                content_https = find_ngrams(
                    text_from_html(content_https).lower().translate(remove_digits).split(), 5)
            except Exception as e:
                return False

            dist1 = 1 - jaccard_similarity(content_http, content_https)
            if dist1 > 0.1:
                time.sleep(sleepTime)
                try:
                    again_https_req = requests.get("https://" + url, timeout=timeOut).content
                    again_https = find_ngrams(
                        text_from_html(again_https_req).lower().translate(remove_digits).split(), 5)
                    time.sleep(sleepTime)
                    again_http_requ = requests.get("http://" + url, timeout=timeOut).content
                    again_http2 = find_ngrams(
                        text_from_html(again_http_requ).lower().translate(remove_digits).split(), 5)
                except Exception as e:
                    # print(repr(e))
                    # print("excepting at again_http...")
                    return False
                dist2 = 1 - jaccard_similarity(again_http2, again_https)
                # Confirm that the difference in http / https still exists
                if dist2 > 0.1:

                    # Confirm that difference is greater than baseline http / http difference
                    dist_base = 1 - jaccard_similarity(again_http2, content_http)
                    if dist_base + 0.1 < dist2:

                        again_https_struct = find_ngrams(
                            text_from_html(again_https_req, just_tags=True).lower().translate(
                                remove_digits).split(), 5)
                        again_http_struct = find_ngrams(
                            text_from_html(again_http_requ, just_tags=True).lower().translate(
                                remove_digits).split(), 5)

                        # Check for http / https page structure distance
                        dist3 = 1 - jaccard_similarity(again_http_struct, again_https_struct)
                        if dist3 > 0.4:
                            print("Found a content difference: ", url)
                            with open(inconsistentResults, 'a') as resultsf:
                                fcntl.flock(resultsf, fcntl.LOCK_EX)
                                resultsf.write(url + "\n")
                                fcntl.flock(resultsf, fcntl.LOCK_UN)
                            return True
        else:
            return False
    else:
        return False


# Checks for HTTP vs HTTPS content inaccessibility
def content_inaccessible(url, http_success, https_success):
    if http_success and not https_success:
        if True:
            success_https = True
            success_http = True

            try:
                again_https_req = requests.get("https://" + url, timeout=timeOut)
                again_https_req.raise_for_status()
            except Exception as e:
                success_https = False
                error = repr(e)

            time.sleep(sleepTime)

            try:
                again_http_req = requests.get("http://" + url, timeout=timeOut)
                again_http_req.raise_for_status()
            except Exception as e:
                success_http = False

            if success_http and not success_https:
                error_stripped = error[:error.find('(')]
                if error_stripped == "HTTPError":
                    error_stripped = error[error.find('(') + 2:error.find(':')]

                if "Timeout" not in error_stripped and "Connection" not in error_stripped:
                    print("Found a content unavailability: ", url)
                    with open(inaccessibleResults, 'a') as resultsf:
                        fcntl.flock(resultsf, fcntl.LOCK_EX)
                        resultsf.write(url + " *** " + error_stripped + "\n")
                        fcntl.flock(resultsf, fcntl.LOCK_UN)
                    return True

            time.sleep(sleepTime)

    return False


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

    return True, ''


# Accesses the given domain over both HTTP and HTTPS ports, returns True if success
def is_domain_https(domain):
    headers = {'User-Agent': uaCustom}
    # Try retrieving the page HTTP
    try:
        response = requests.get('http://' + domain, timeout=timeOut, headers=headers,
                                allow_redirects=True)
        response.raise_for_status()
    # Page not found etc.
    except requests.exceptions.RequestException as e:
        # print 'Error for HTTP: ' + domain
        # print e
        return False

    time.sleep(sleepTime)

    # Try retrieving the page HTTPS
    try:
        response = requests.get('https://' + domain, timeout=timeOut, headers=headers,
                                allow_redirects=True)
        response.raise_for_status()
    # Page not found etc.
    except requests.exceptions.RequestException as e:
        # print 'Error for HTTPs: ' + domain
        # print e
        return False
    return True


# Assess if the page is different over HTTP vs HTTPS
def is_page_different(url, domain):
    try:
        allowed, err_msg = allowed_to_crawl(url, visit_check=False)
        if not allowed:
            print("url not allowed to crawl during is_page_different() phase: " + url + ", " + err_msg + "\n")
            return

        headers = {'User-Agent': uaCustom}
        # Remove the protocol from the url
        url = url.replace("http://", "", 1)
        url = url.replace("https://", "", 1)

        success_http = True
        success_https = True

        # Try retrieving the page HTTP
        try:
            response_http = requests.get('http://' + url, timeout=timeOut, headers=headers,
                                         allow_redirects=True)
            response_http.raise_for_status()
            error_http = '<no http error>'
        # Any error i.e. ssl validation, 404 etc.
        except requests.exceptions.RequestException as e:
            success_http = False
            error_http = e

        time.sleep(sleepTime)

        # Try retrieving the page HTTPS
        try:
            response_https = requests.get('https://' + url, timeout=timeOut, headers=headers,
                                          allow_redirects=True)
            response_https.raise_for_status()
            error_https = '<no https error>'
        # Any error i.e. SSL validation, 404 etc.
        except requests.exceptions.RequestException as e:
            success_https = False
            error_https = e

        # Store the results, if the URLs were successfully fetched
        try:
            response_http_url = repr(response_http.url)
            headers_http = repr(response_http.headers)
            time_http = repr(response_http.elapsed.total_seconds())
            # body_http = base64.b64encode(response_http.content).decode()
            body_http = response_http.content
        except:
            response_http_url = "<url not available>"
            headers_http = "<headers not available>"
            time_http = "<time not available>"
            body_http = "<body not available>"
        try:
            response_https_url = repr(response_https.url)
            headers_https = repr(response_https.headers)
            time_https = repr(response_https.elapsed.total_seconds())
            # body_https = base64.b64encode(response_https.content).decode()
            body_https = response_https.content
        except:
            response_https_url = "<url not available>"
            headers_https = "<headers not available>"
            time_https = "<time not available>"
            body_https = "<body not available>"

        # Check for inaccessible and inconsistent URLs
        content_inaccessible(url, success_http, success_https)
        content_inconsistent(url, success_http, success_https, body_http, body_https)

    except Exception as e:
        raise (e)


# Returns the list of all href and img src in html pages, starting from a root url
def get_all_anchor_links(page_url, domain):
    global all_links, references

    allowed, err_msg = allowed_to_crawl(page_url, visit_check=True)
    if allowed:
        headers = {'User-Agent': uaCustom}
        try:
            page = requests.get(page_url, timeout=timeOut, headers=headers)
            page.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("visited: " + page_url + ", requests exception" + "\n")
            # print e
            return

        if "content-type" in page.headers:
            if "html" not in page.headers['content-type']:
                # Log
                print("visited: " + page_url + ", content-type not html" + "\n")
                return
        else:
            print("visited: " + page_url + ", content-type field not found" + "\n")
            return

        bs = BeautifulSoup(page.content, features='html5lib')
        this_page_links = set()

        # <a> links
        for link in bs.findAll('a'):
            temp = link.get('href')
            if temp is not None \
                    and temp.startswith("#") is not True \
                    and "mailto" not in temp:
                temp = urljoin(page.url, temp)
                if domain.replace("www.", "") in urlparse(temp)[1]:
                    all_links.add((temp.strip()))
                    this_page_links.add(temp.strip())
                    references[temp.strip()] = repr(page.url)

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
        print("visited: " + page_url + ", found: " + str(len(this_page_links)) + " links" + "\n")

        # Traverse recursively until a threshold number of links have been retrieved
        list_links = list(all_links)
        random.shuffle(list_links)
        for link in list_links:
            if len(all_links) < totalLinks:
                time.sleep(sleepTime)
                get_all_anchor_links(link, domain)
    else:
        print(
            "url not allowed to crawl during get_all_anchor_links() phase: " + page_url + ", " + err_msg + "\n")


# ARGUMENTS
domain_name = sys.argv[1].strip()

# GLOBALS
references = {}
robotParsers = {}
httpsDomains = {}
visitedLinks = set()
all_links = set()


# START
try:
    print("started crawling " + domain_name + "..." + "\n")

    get_all_anchor_links("http://" + domain_name, domain_name)

    results = {domain_name: []}

    # Respect the limits set
    while len(all_links) > totalLinks:
        all_links.pop()

    print("finding HTTP/S issues for " + domain_name + " from a set of " + str(len(all_links)) + "\n")

    processes = []
    for link in all_links:
        p = Process(target=is_page_different, args=(link, domain_name))
        processes.append([p, link])
        p.start()
        # Value intentionally hard-coded to be 1; we must not run more than one process for a single host
        while len(processes) >= parallelization:
            for p in processes:
                p[0].join(0.1)
                if not p[0].is_alive():
                    processes.remove(p)
        time.sleep(sleepTime)
    for p in processes:
        p[0].join()
        if not p[0].is_alive():
            processes.remove(p)

except Exception as e:
    print("misc error for " + domain_name + ": " + repr(e) + "\n")