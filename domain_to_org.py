import matplotlib.pyplot as plt
import numpy as np
import pyasn
from operator import itemgetter
import scipy.stats
import random

def cdf(x, xlabel, ylabel, title):
    x, y = sorted(x), np.arange(len(x)) / len(x)
    plt.scatter(x, y)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()


asndb = pyasn.pyasn('analysis-data/ipasn.dat')
asn_org_id = {}
org_id_name = {}
with open('analysis-data/20190401.as-org2info.txt', 'r') as caida_file:
    for line in caida_file.readlines():
        if not line.startswith("#"):
            items = line.strip().split("|")
            if len(items) == 5:
                org_id_name[items[0]] = items[2]
            elif len(items) == 6:
                asn_org_id[int(items[0])] = items[3]
            else:
                assert False


def ip_to_asn(ip):
    return asndb.lookup(ip)[0]


def asn_to_org_name(asn):
    return org_id_name[asn_org_id[asn]]


names = {}
hosts_asn = {}
fail = 0
files = ["analysis-data/mappingresults.txt", "analysis-data/v2Results/bottom10k/bt-mappingresults.txt"]
for f in files:
    with open(f) as doms_ip_file:
        for line in doms_ip_file.readlines():
            try:
                name = asn_to_org_name(ip_to_asn(line.strip().split(" *** ")[1]))
            except:
                fail += 1
                continue
            if name not in names:
                names[name] = []
            names[name].append(line.strip().split(" *** ")[0])
            hosts_asn[line.strip().split(" *** ")[0].strip().replace("www.", "")] = name

print("Failed domains: ", fail)
names_len = {}
for name in names:
    names[name] = list(set(names[name]))
    names_len[name] = len(names[name])
print("Total ASNs: ", len(names))
sorted_names = [x[0] for x in sorted(names_len.items(), key=itemgetter(1))]
print(sorted(names_len.items(), key=itemgetter(1)))
self_managed = 0
for name in names:
    if(len(names[name]) == 1):
        self_managed += 1
print("ASNs with 1 domain:", self_managed)

inac_doms = set()
files = ["analysis-data/v2Results/top100k/inacresults-without-timeout.txt", "analysis-data/v2Results/bottom10k/inacresults-without-timeout.txt"]
#files = ["analysis-data/v3-impresults/inacresults-contd-v3-without-timeout-without-connection.txt"]
for f in files:
    with open(f) as diff_r:
        for line in diff_r.readlines():
            items = line.split("***")
            domain = items[0].strip()
            inac_doms.add(domain)

cd_doms = set()
files = ["analysis-data/v2Results/top100k/top-diffresults-contd.txt", "analysis-data/v2Results/bottom10k/bt-diffresults-contd.txt"]
#files = ["analysis-data/v3-impresults/top-diffresults-contd-v3.txt"]
for f in files:
    with open(f) as diff_r:
        for line in diff_r.readlines():
            items = line.split("***")
            domain = items[0].strip()
            cd_doms.add(domain)

# https_avail = set()
# dom = 0
# with open("/Users/talhaparacha/Downloads/impresults-top100k/all_data.txt") as cf_https:
#     lines = cf_https.readlines()
#     for line in lines:
#         host = line.split(":nakedTest:")[0].split(":")[0].split("/")[0].split("?")[0]
#         items = line.split(":nakedTest:")[1].split("***")
#         assert len(items) == 16
#         dom += 1
#         host = host.replace("www.", "")
#         if items[0] == "True" or items[1] == "True":
#             https_avail.add(host)
https_avail = set()
dom = 0
#files = ["analysis-data/v3-impresults/numpagesresults-v3.txt"]
files = ["analysis-data/v2Results/top100k/numpagesresults.txt", "analysis-data/v2Results/bottom10k/numpagesresults.txt"]
for f in files:
    with open(f) as cf_https:
        lines = cf_https.readlines()
        for line in lines:
            items = line.split(" *** ")
            assert len(items) == 2
            dom += 1
            if items[1].strip() != "0":
                https_avail.add(items[0].replace("www.", "").strip())

print()
print("All websites", dom)
print("HTTPS supporting websites", len(https_avail))
print("% of inac errors", len(inac_doms) / len(https_avail) * 100)
print("% of cd errors", len(cd_doms) / len(https_avail) * 100)
print()

print("**** Under Cloudflare, Inc. Hosting (which manages SSL for customers) ****")
sites_exclude = set([x.replace("www.", "") for x in names['Cloudflare, Inc.']])
print("All websites:", len(sites_exclude))
print("HTTPS supporting websites:", len(https_avail & sites_exclude))
print("% of inac errors", len(inac_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print("% of cd errors", len(cd_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print()

# Statistical tests..
print("Statistical tests...")
print("Number of cloudflare https domains with incons", len(https_avail.intersection(sites_exclude).intersection(cd_doms.union(inac_doms))))
print("Number of cloudflare https domains without incons", len(https_avail.intersection(sites_exclude).difference(cd_doms.union(inac_doms))))
print("Number of non-cloudflare https domains with incons", len(https_avail.difference(sites_exclude).intersection(cd_doms.union(inac_doms))))
print("Number of non-cloudflare https domains without incons", len(https_avail.difference(sites_exclude).difference(cd_doms.union(inac_doms))))
obs = np.array\
    ([[len(https_avail.intersection(sites_exclude).intersection(cd_doms.union(inac_doms))),
       len(https_avail.difference(sites_exclude).intersection(cd_doms.union(inac_doms)))],
      [len(https_avail.intersection(sites_exclude).difference(cd_doms.union(inac_doms))),
       len(https_avail.difference(sites_exclude).difference(cd_doms.union(inac_doms)))]])
g, p, dof, expctd = scipy.stats.chi2_contingency(obs)
print(obs)
print(p)
print(g)
print()

print("**** Under Amazon, Inc. Hosting ****")
sites_exclude = set([x.replace("www.", "") for x in names['Amazon.com, Inc.']])
print("All websites:", len(sites_exclude))
print("HTTPS supporting websites:", len(https_avail & sites_exclude))
print("% of inac errors", len(inac_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print("% of cd errors", len(cd_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print()
print("**** Under Top 10 Hosting Providers (excluding Cloudflare) ****")
all = []
providers = ["SAKURA Internet Inc.", "DigitalOcean, LLC", "Microsoft Corporation", "Google LLC", "Hetzner Online GmbH", "Fastly", "Amazon.com, Inc.", "Akamai Technologies, Inc.", "OVH SAS", "Hangzhou Alibaba Advertising Co.,Ltd."]
for name in names:
    if name in providers:
        all.extend(names[name])
sites_exclude = set([x.replace("www.", "") for x in all])
print("All websites:", len(sites_exclude))
print("HTTPS supporting websites:", len(https_avail & sites_exclude))
print("% of inac errors", len(inac_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print("% of cd errors", len(cd_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print()
# print("**** Under Top 5 ASNs ****")
# all = []
# sorted_list = sorted(names_len.items(), key=itemgetter(1), reverse=True)
# providers = [x[0] for x in sorted_list][:5]
# for name in names:
#     if name in providers:
#         all.extend(names[name])
# sites_exclude = set([x.replace("www.", "") for x in all])
# print("All websites:", len(sites_exclude))
# print("HTTPS supporting websites:", len(https_avail & sites_exclude))
# print("% of inac errors", len(inac_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
# print("% of cd errors", len(cd_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
#
# print()
print("**** Under Bottom 3977 ASNs ****")
all = []
sorted_list = sorted(names_len.items(), key=itemgetter(1))
providers = [x[0] for x in sorted_list][:3977]
for name in names:
    if name in providers:
        all.extend(names[name])
count = 0
for y in ([x for x in sorted_list]):
    if y[1] == 1:
        count += 1
print(count)
random.shuffle(providers)
print("Sample providers from ", len(providers), providers[:20])
sites_exclude = set([x.replace("www.", "") for x in all])
print("All websites:", len(sites_exclude))
print("HTTPS supporting websites:", len(https_avail & sites_exclude))
print("% of inac errors", len(inac_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print("% of cd", len(cd_doms & sites_exclude) / len(https_avail & sites_exclude) * 100)
print()

# Statistical tests...
print("Statistical tests...")
print("Number of self-hosted https domains with incons", len(https_avail.intersection(sites_exclude).intersection(cd_doms.union(inac_doms))))
print("Number of self-hosted https domains without incons", len(https_avail.intersection(sites_exclude).difference(cd_doms.union(inac_doms))))
print("Number of non-self-hosted https domains with incons", len(https_avail.difference(sites_exclude).intersection(cd_doms.union(inac_doms))))
print("Number of non-self-hosted https domains without incons", len(https_avail.difference(sites_exclude).difference(cd_doms.union(inac_doms))))

obs = np.array\
    ([[len(https_avail.intersection(sites_exclude).intersection(cd_doms.union(inac_doms))),
       len(https_avail.difference(sites_exclude).intersection(cd_doms.union(inac_doms)))],
      [len(https_avail.intersection(sites_exclude).difference(cd_doms.union(inac_doms))),
       len(https_avail.difference(sites_exclude).difference(cd_doms.union(inac_doms)))]])
g, p, dof, expctd = scipy.stats.chi2_contingency(obs)
print(obs)
print("{:%1.20f}" % p)
print(g)

print()
