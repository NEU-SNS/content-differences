import requests
from urllib.parse import urlparse, urljoin
import random
import time
from multiprocessing import Process
import tldextract
from bs4 import BeautifulSoup
import sys
import pickle
import signal
from reppy.robots import Robots
import fcntl, os
import base64

# Custom user agent to notify the destination about purpose of crawl
uaCustom = "NortheasternSysNetBot/1.0 (Bot for academic research purposes; please" \
           " visit https://www.ccs.neu.edu/home/talhaparacha/sysnetbot1.html for more details)"

# Time to sleep after processing each link, so to not overwhelm the destination
sleepTime = 5

# Stop after fetching this many unique links
totalLinks = 250

# Stop after visiting this many links
totalTryLinks = 100

# Stop after getting this many results, in terms of inaccessible links
maxResults = 5

# Give up processing after finishing the current thread
giveProcess = True

# Timeout set during requests functions
timeOut = 20


# Write to a file but acquire lock first
def write_with_lock(file_handle, content_to_write):
    fcntl.flock(file_handle, fcntl.LOCK_EX)
    file_handle.write(content_to_write)
    fcntl.flock(file_handle, fcntl.LOCK_UN)


# Naked HTTPS test
def naked_test(domain):
    time.sleep(random.randint(1,10))
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

    in_between_http_redirection_naked = "_"
    in_between_http_redirection = "_"

    hsts_naked = "_"
    hsts = "_"

    headers = {'User-Agent': uaCustom}

    # Try retrieving the domain naked HTTP
    try:
        response_http_naked = requests.get('http://' + domain, timeout=timeOut, headers=headers)
        final_url_http_naked = response_http_naked.url
        response_http_naked.raise_for_status()
    # Any error i.e. ssl validation, 404 etc.
    except Exception as e:
        success_http_naked = False
        error_http_naked = repr(e)

    time.sleep(sleepTime)
    if giveProcess:
        os.kill(os.getpid(), signal.SIGSTOP)

    # Try retrieving the domain HTTP
    try:
        response_http = requests.get('http://www.' + domain, timeout=timeOut, headers=headers)
        final_url_http = response_http.url
        response_http.raise_for_status()
    # Any error i.e. ssl validation, 404 etc.
    except Exception as e:
        success_http = False
        error_http = repr(e)

    time.sleep(sleepTime)
    if giveProcess:
        os.kill(os.getpid(), signal.SIGSTOP)

    # Try retrieving the domain naked HTTPS
    try:
        response_https_naked = requests.get('https://' + domain, timeout=timeOut, headers=headers)
        final_url_https_naked = response_https_naked.url
        for hist in response_https_naked.history:
            if "http://" in hist.url:
                in_between_http_redirection_naked = "True"
                break
        if in_between_http_redirection_naked == "_":
            in_between_http_redirection_naked = "False"

        if 'strict-transport-security' in response_https_naked.headers:
            hsts_naked = "True"
        else:
            hsts_naked = "False"

        response_https_naked.raise_for_status()
    # Any error i.e. ssl validation, 404 etc.
    except Exception as e:
        success_https_naked = False
        error_https_naked = repr(e)

    time.sleep(sleepTime)
    if giveProcess:
        os.kill(os.getpid(), signal.SIGSTOP)

    # Try retrieving the domain (www) HTTPS
    try:
        response_https = requests.get('https://www.' + domain, timeout=timeOut, headers=headers)
        final_url_https = response_https.url
        for hist in response_https.history:
            if "http://" in hist.url:
                in_between_http_redirection = "True"
                break
        if in_between_http_redirection == "_":
            in_between_http_redirection = "False"

        if 'strict-transport-security' in response_https.headers:
            hsts = "True"
        else:
            hsts = "False"

        response_https.raise_for_status()
    # Any error i.e. SSL validation, 404 etc.
    except Exception as e:
        success_https = False
        error_https = repr(e)

    # Write results
    write_with_lock(data_file, domain + ":nakedTest:" +
                    str(success_https_naked) + "***" +
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
                    error_http + "***" +
                    in_between_http_redirection_naked + "***" +
                    in_between_http_redirection + "***" +
                    hsts_naked + "***" +
                    hsts + "\n"
                    )


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
            write_with_lock(data_file, domain_name + ":log:" +
                            "url not allowed to crawl during is_page_different() phase: " + url + ", " + err_msg + "\n")
            exit(0)

        headers = {'User-Agent': uaCustom}
        # Remove the protocol from the url
        url = url.replace("http://", "", 1)
        url = url.replace("https://", "", 1)

        success_http = True
        success_https = True
        # Try retrieving the page HTTP
        try:
            response_http = requests.get('http://' + url, timeout=timeOut, headers=headers, proxies=proxies,
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
            response_https = requests.get('https://' + url, timeout=timeOut, headers=headers, proxies=proxies,
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
            body_http = base64.b64encode(response_http.content).decode()
        except:
            response_http_url = "<url not available>"
            headers_http = "<headers not available>"
            time_http = "<time not available>"
            body_http = "<body not available>"

        try:
            response_https_url = repr(response_https.url)
            headers_https = repr(response_https.headers)
            time_https = repr(response_https.elapsed.total_seconds())
            body_https = base64.b64encode(response_https.content).decode()
        except:
            response_https_url = "<url not available>"
            headers_https = "<headers not available>"
            time_https = "<time not available>"
            body_https = "<body not available>"

        # Don't store entire response if there's no indication of content-difference
        if body_http == body_https and "not" not in body_https:
            body_http = "<same body>"
            body_https = "<same body>"

        # Store all results
        write_with_lock(data_file, domain + ":summary:" +
                        url + "***" +
                        references[link] + "***" +
                        str(success_http) + "***" +
                        str(success_https) + "***" +
                        repr(error_http) + "***" +
                        repr(error_https) + "***" +
                        response_http_url + "***" +
                        response_https_url + "***" +
                        time_http + "***" +
                        time_https + "***" +
                        headers_http + "***" +
                        headers_https + "***" +
                        body_http + "***" +
                        body_https + "\n"
                        )
        exit(success_http != success_https)
    except Exception as e:
        print("error for " + domain + " with url " + url)
        print(e)
        exit(0)


# Returns the list of all href and img src in html pages, starting from a root url
def get_all_anchor_links(page_url, domain):
    global all_links, totalTryLinks, references
    totalTryLinks -= 1
    if totalTryLinks <= 0:
        return

    allowed, err_msg = allowed_to_crawl(page_url, visit_check=True)
    if allowed:
        headers = {'User-Agent': uaCustom}
        try:
            page = requests.get(page_url, timeout=timeOut, headers=headers, proxies=proxies)
            page.raise_for_status()
        except requests.exceptions.RequestException as e:
            write_with_lock(data_file, domain_name + ":log:" + "visited: " + page_url + ", requests exception" + "\n")
            # print e
            return

        if "html" not in page.headers['content-type']:
            # Log
            write_with_lock(data_file, domain_name + ":log:" + "visited: " + page_url + ", content-type not html" + "\n")
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
        write_with_lock(data_file, domain_name + ":log:" + "visited: " + page_url + ", found: " + str(len(this_page_links)) + " links" + "\n")

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
        write_with_lock(data_file, domain_name + ":log:" +
                        "url not allowed to crawl during get_all_anchor_links() phase: " + page_url + ", " + err_msg + "\n")


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

# DATA FILE
data_file = open(results_dir + '/all_data.txt', 'a')

# START
# Don't crawl hosts, just study differences at the index pages
if experiment_type == "nakedHTTPS":
    naked_test(domain_name)

# For other experiments, we append www reference for robustness
if tldextract.extract(domain_name).subdomain == '':
    domain_name = "www." + domain_name

# In phase 1, we crawl the links that we'd be doing our analysis over
if experiment_type == "inDepth-Phase1" or experiment_type == "inDepth-allPhases":
    write_with_lock(data_file, domain_name + ":log:" + "started crawling..." + "\n")
    get_all_anchor_links("http://" + domain_name, domain_name)
    write_with_lock(data_file, domain_name + ":log:" + "finding inaccessible links from a set of " +
                    str(len(all_links)) + "\n")
    print("domain: ", domain_name, " ", " length: ", str(len(all_links)))

    write_with_lock(data_file, domain_name + ":links:" +
                    base64.b64encode(pickle.dumps(all_links)).decode()
                    )
    write_with_lock(data_file, domain_name + ":references:" +
                    base64.b64encode(pickle.dumps(references)).decode()
                    )

# In phase 2, we use the recorded links and access them over HTTPvsHTTPS ports to study differences
if experiment_type == "inDepth-Phase2" or experiment_type == "inDepth-allPhases":
    results = {domain_name: []}
    # @TODO LOAD FROM DATA FILE
    # with open(results_dir + "/links/" + domain_name + "-links.txt", 'rb') as al:
    #     all_links = pickle.load(al)
    # with open(results_dir + "/links/" + domain_name + "-references.txt", 'rb') as ref:
    #     references = pickle.load(ref)

    # Respect the limits set
    while len(all_links) > totalLinks:
        all_links.pop()
    processes = []
    for link in all_links:
        p = Process(target=is_page_different, args=(link, domain_name))
        processes.append([p, link])
        p.start()
        # Value intentionally hard-coded to be 1; we must not run more than one process for a single host
        while len(processes) >= 1:
            for p in processes:
                p[0].join(0.1)
                if not p[0].is_alive():
                    if p[0].exitcode is not 0:
                        results[domain_name].append('')
                    processes.remove(p)
        if len(results[domain_name]) > maxResults:
            break
        time.sleep(sleepTime)
        if giveProcess:
            os.kill(os.getpid(), signal.SIGSTOP)
    for p in processes:
        p[0].join()
        if not p[0].is_alive():
            if p[0].exitcode is not 0:
                results[domain_name].append('')
            processes.remove(p)

    write_with_lock(data_file, domain_name + ":log:" + "# of inaccessible links: " + str(len(results[domain_name])) + "\n")

    # Write to the list of done domains, so a cleanup process can zip the resulting files
    with open(results_dir + '/doneDomains.txt', 'a') as dd:
        write_with_lock(dd, domain_name + "\n")

data_file.close()
