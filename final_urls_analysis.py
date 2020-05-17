import requests as r
import fcntl, os
from multiprocessing import Process

# Custom user agent to notify the destination about purpose of crawl
# uaCustom = "NortheasternSysNetBot/1.0 (Bot for academic research purposes; please" \
#            " visit https://www.ccs.neu.edu/home/talhaparacha/sysnetbot1.html for more details)"
#
# inputFile = "analysis-data/v2Results/inacresultsALL-withouTIMEOUTwithoutCONNECTION.txt"
# outputFile = "final_urls-inacresultsALL.txt"
#
# mapping_doms_urls = {}
# with open(inputFile) as in_f:
#     for line in in_f.readlines():
#         items = line.split("***")
#         assert len(items) == 3
#         if items[0].strip() not in mapping_doms_urls:
#             mapping_doms_urls[items[0].strip()] = []
#         mapping_doms_urls[items[0].strip()].append(items[1].strip())
#
#
# # Write to a file but acquire lock first
# def write_with_lock(file_handle, content_to_write):
#     fcntl.flock(file_handle, fcntl.LOCK_EX)
#     file_handle.write(content_to_write)
#     fcntl.flock(file_handle, fcntl.LOCK_UN)
#
#
# def proc_url(urls):
#     for url in urls:
#         try:
#             http_url = r.head('http://' + url, allow_redirects=True,
#                               headers={'User-Agent': uaCustom}).url.replace("http://", "", 1)
#         except:
#             http_url = "<url not available>"
#
#         try:
#             https_url = r.head('https://' + url, allow_redirects=True,
#                                headers={'User-Agent': uaCustom}).url.replace("https://", "", 1)
#         except:
#             https_url = "<url not available>"
#
#         out_f = open(outputFile, "a")
#         write_with_lock(out_f, dom + "***" + url + "***" + http_url + "***" + https_url + "\n")
#         out_f.close()
#
#
# processes = []
# for dom in mapping_doms_urls:
#     p = Process(target=proc_url, args=(mapping_doms_urls[dom],))
#     processes.append(p)
#     p.start()
#     while len(processes) >= 20:
#         for px in processes:
#             px.join(0.1)
#             if not px.is_alive():
#                 processes.remove(px)
# for p in processes:
#     p.join()
#     processes.remove(p)
#
# exit(0)

count = 0
total = 0
seen = set()
all_h = set()
input_file = "analysis-data/v2Results/final_urls-diffresultsALL.txt"
with open(input_file) as in_f:
    for line in in_f.readlines():
        items = line.split("***")
        assert len(items) == 4
        total += 1
        all_h.add(items[0].strip())
        final_http_url = items[2].strip().replace("https://", "", 1).replace("http://", "", 1).replace("/", "", 1)
        final_https_url = items[3].strip().replace("https://", "", 1).replace("http://", "", 1).replace("/", "", 1)
        if "<url not available>" not in final_http_url and "<url not available>" not in final_https_url:
            print(items[1].strip(), final_https_url, final_http_url, final_http_url != final_https_url)
            if final_http_url != final_https_url:
                # if items[0].strip() not in seen:
                #     seen.add(items[0].strip())
                    count += 1
print(count, total, len(all_h))
