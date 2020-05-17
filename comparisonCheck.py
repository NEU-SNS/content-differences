import tldextract
import parallelProcessing

alexa_hosts = parallelProcessing.fetch_domains(type = "alexa", n = 100000)
alexa_hosts = [host.decode() for host in alexa_hosts]


def alexa_host_name(host):
    for rank in range(0, len(alexa_hosts)):
        # if host == alexa_hosts[rank]:
        #     return alexa_hosts[rank]
        if host.endswith(alexa_hosts[rank]):
            return alexa_hosts[rank]
    return host

inacResultsPath = "analysis-data/v2Results/inacresultsALL-withouTIMEOUTwithoutCONNECTION.txt"
diffResultsPath = "analysis-data/v2Results/diffresultsALL.txt"

inac_hosts = {}
# reasons = {}
with open(inacResultsPath) as cf_inac:
    lines = cf_inac.readlines()
    for line in lines:
        if ":80" in line.split(" *** ")[0].split("/")[0]:
            continue
        host = line.split(" *** ")[0].split(":")[0].split("/")[0].split("?")[0]
        if host.startswith("www."):
            host = host.replace("www.", "", 1)
        # host = alexa_host_name(host)
        # error = line.split(" *** ")[1]
        inac_hosts[host] = (line.split(" *** ")[0], '')
        # if error not in reasons:
        #     reasons[error] = 0
        # reasons[error] += 1
cd_hosts = {}
with open(diffResultsPath) as cf_inac:
    lines = cf_inac.readlines()
    for line in lines:
        if ":80" in line.split("***")[0].split("/")[0]:
            continue
        host = line.split("***")[0].split(":")[0].split("/")[0].split("?")[0]
        if host.startswith("www."):
            host = host.replace("www.", "", 1)
        # host = alexa_host_name(host)
        # error = line.split(" *** ")[1]
        cd_hosts[host] = (line.split("***")[0], '')

# MOZILLA HTTPS AVAILABLE + HTTPSWatch HTTPS AVAILABLE
https_avail_mozilla = {}
with open("analysis-data/v2Results/all_data_naked.txt") as cf_https:
    lines = cf_https.readlines()
    for line in lines:
        host = line.split(":nakedTest:")[0].split(":")[0].split("/")[0]
        if host.startswith("www."):
            host = host.replace("www.", "", 1)

        items = line.split(":nakedTest:")[1].split("***")
        assert len(items) == 16
        if items[0] == "True":
            https_avail_mozilla[host] = items
count_inac = 0
count_cd = 0
print("HTTPS available", len(https_avail_mozilla))
for host in https_avail_mozilla:
    if host in inac_hosts:
        count_inac += 1
    if host in cd_hosts:
        count_cd += 1
print("U", count_inac)
print("D", count_cd)
# exit(0)
#
# # MOZILLA DEFAULT HTTPS + GOOGLE DEFAULT HTTPS
https_default_mozilla = {}
with open("analysis-data/v2Results/all_data_naked.txt") as cf_https:
    lines = cf_https.readlines()
    for line in lines:
        host = line.split(":nakedTest:")[0].split(":")[0].split("/")[0]
        if host.startswith("www."):
            host = host.replace("www.", "", 1)

        items = line.split(":nakedTest:")[1].split("***")
        assert len(items) == 16
        if items[2] == "True" and items[6].startswith("https://"):
            https_default_mozilla[host] = items
count_inac = 0
count_cd = 0
print("Default HTTPS", len(https_default_mozilla))
for host in https_default_mozilla:
    if host in inac_hosts:
        count_inac += 1
    if host in cd_hosts:
        count_cd += 1
print("U", count_inac)
print("D", count_cd)
#
# # MOZILLA HSTS HTTPS
https_hsts_mozilla = {}
with open("analysis-data/v2Results/all_data_naked.txt") as cf_https:
    lines = cf_https.readlines()
    for line in lines:
        host = line.split(":nakedTest:")[0].split(":")[0].split("/")[0]
        if host.startswith("www."):
            host = host.replace("www.", "", 1)

        items = line.split(":nakedTest:")[1].split("***")
        assert len(items) == 16
        if items[14].strip() == "True":
            https_hsts_mozilla[host] = items
count_inac = 0
count_cd = 0
print("HSTS avail", len(https_hsts_mozilla))
for host in https_hsts_mozilla:
    if host in inac_hosts:
        count_inac += 1
    if host in cd_hosts:
        count_cd += 1
print(count_inac)
print(count_cd)
#
# GOOGLE HTTPS AVAILABLE
https_avail_google = {}
with open("analysis-data/v2Results/all_data_naked.txt") as cf_https:
    lines = cf_https.readlines()
    for line in lines:
        host = line.split(":nakedTest:")[0].split(":")[0].split("/")[0]
        if host.startswith("www."):
            host = host.replace("www.", "", 1)

        items = line.split(":nakedTest:")[1].split("***")
        assert len(items) == 16
        if items[0] == "True" and items[12] == "False" and "https://" in items[4]:
            https_avail_google[host] = items
count_inac = 0
count_cd = 0
print("Google HTTPS Available", len(https_avail_google))
for host in https_avail_google:
    if host in inac_hosts:
        count_inac += 1
    if host in cd_hosts:
        count_cd += 1
print(count_inac)
print(count_cd)
#
# # HTTPSWatch DEFAULT HTTPS
https_default_watch = {}
with open("analysis-data/v2Results/all_data_naked.txt") as cf_https:
    lines = cf_https.readlines()
    for line in lines:
        host = line.split(":nakedTest:")[0].split(":")[0].split("/")[0]
        if host.startswith("www."):
            host = host.replace("www.", "", 1)

        items = line.split(":nakedTest:")[1].split("***")
        assert len(items) == 16
        if items[0] == "True" and items[2] == "True" and \
                items[6].startswith("https://") and items[14].strip() == "True":
            https_default_watch[host] = items
count_inac = 0
count_cd = 0
print("HTTPS WATCH Default", len(https_default_watch))
for host in https_default_watch:
    if host in inac_hosts:
        count_inac += 1
    if host in cd_hosts:
        count_cd += 1
print(count_inac)
print(count_cd)
