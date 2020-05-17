import matplotlib.pyplot as plt
import numpy as np
import parallelProcessing
import math
import statistics

alexa_hosts = parallelProcessing.fetch_domains(type = "alexa", n = 100000)
alexa_hosts = [host.decode().replace("www.", "") for host in alexa_hosts]

plt.rcParams['figure.figsize'] = 9, 8
# plt.rcParams['figure.figsize'] = 7, 5
plt.rcParams['figure.dpi'] = 100
# plt.rcParams['axes.labelsize']=34
plt.rcParams['axes.labelsize']=34
plt.rcParams['xtick.labelsize']=30
plt.rcParams['ytick.labelsize']=30
plt.rcParams['legend.fontsize']=28


def find_rank(host):
    return alexa_hosts.index(host) + 1

fig = None


def cdf(x, xlabel, ylabel, title, save=False, name="figure.pdf", label=None):
    global fig
    x, y = sorted(x), np.arange(len(x)) / len(x)
    fig = plt.figure()
    plt.plot(x, y, linewidth=3, label=label, ls="solid")

    # For Figure 3B
    # plt.plot([0.1, 0.1], [0, 1], c='r', linestyle='solid')
    # plt.plot([0.4, 0.4], [0, 1], c='g', linestyle='solid')

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.margins(0.001)
    ax = fig.gca()
    ax.xaxis.set_tick_params(width=2)
    ax.yaxis.set_tick_params(width=2)
    # ax.set_yscale('log')
    # ax.set_xticks(np.arange(0, 260, 50))
    # ax.set_xlim([0, 255])

    # Remove ticks if desired
    # ax.xaxis.get_major_ticks()[0].draw = lambda *args: None

    plt.xticks(rotation=35)
    plt.grid(linestyle='dotted',  c="#393b3d")
    if not save:
        # plt.title(title)
        # plt.show()
        pass
    else:
        fig.savefig(name, bbox_inches="tight")

# FIGURE 3A - NUMBER OF INTERNAL LINKS THAT WERE CRAWLED
num_pages = []
hosts_num_pages = {}
files = ["analysis-data/v2Results/top100k/numpagesresults.txt",
         "analysis-data/v2Results/bottom10k/numpagesresults.txt"]
for f in files:
    with open(f) as pages_file:
        lines = pages_file.readlines()
        for line in lines:
            x = int(line.strip().split(" *** ")[1])
            if x == 0:
                continue
            hosts_num_pages[line.strip().split(" *** ")[0].strip()] = min(250, x)
            num_pages.append(min(250,x))
print(statistics.mean(num_pages))
print(len(hosts_num_pages))
cdf(num_pages, "Number of internal links", "CDF", "CDF for internal links crawled", save=True, name="ratio_internal_links.pdf")
index = 0
for el in sorted(num_pages):
    if el >= 250:
        print("err:", index, el)
        break
    else:
        index+=1
print(len(num_pages))
index = 0
print("SAVING ratio_internal_links.pdf...")
# exit(0)

# FIGURE 3B - CDF VISIBLE DISTANCE
results = {}
with open("analysis-data/v2Results/diff-cdf.txt") as cd_file:
    for line in cd_file.readlines():
        items = line.strip().split(" * ")
        if items[0] not in results:
            results[items[0]] = []
        results[items[0]].append(float(items[1]))
num = []
count = 0
for r in results:
    count += 1
    for x in (results[r]):
        num.append(x)
    # if count == 10000:
    #     break
print((num))
cdf(num, "Visible-text distance", "CDF", "", save=True, name="alpha.pdf")

sorted_arr = sorted(num)
print("Total", len(sorted_arr))
index = 0
for el in sorted_arr:
    if el >= 0.1:
        print(index)
        break
    else:
        index+=1
print(num.count(0.0))
print("SAVING alpha.pdf...")
# exit(0)

# FIGURE 3C - NOT CRAWL REASONS
hosts_reasons = {}
with open("analysis-data/v2Results/top100k/numreasonsresults.txt") as pages_file:
    lines = pages_file.readlines()
    for line in lines:
        reason = (line.strip().split(" *** ")[1])
        hosts_reasons[line.strip().split(" *** ")[0]] = reason
bins_wanted = 10
div_num = len(alexa_hosts) / bins_wanted
bins = {}
for i in range(1, bins_wanted + 1):
    bins[i] = []
for host in hosts_reasons:
    rank = find_rank(host.replace("www.", ""))
    bins[ math.ceil(rank/div_num)].append(hosts_reasons[host])
print("*bins*")
x = []
https_not = []
robots_not  = []
misc = []
for bin in bins:
    x.append(bin)
    https_not.append(bins[bin].count("<domain not https friendly>"))
    robots_not.append(bins[bin].count("<robots.txt check>"))
    misc.append(bins[bin].count("unknown"))

# ADD BOTTOM 10k RESULTS
bottom_reasons = []
with open("analysis-data/v2Results/bottom10k/numreasonsresults.txt") as pages_file:
    lines = pages_file.readlines()
    for line in lines:
        reason = (line.strip().split(" *** ")[1])
        bottom_reasons.append(reason)
x.append(11)
https_not.append(bins[bin].count("<domain not https friendly>"))
robots_not.append(bins[bin].count("<robots.txt check>"))
misc.append(bins[bin].count("unknown"))

fig = plt.figure()
p1 = plt.plot(x, https_not, linewidth=3, ls="dashdot")
p3 = plt.plot(x, misc, linewidth=3, ls="dotted")
p2 = plt.plot(x, robots_not, linewidth=3, ls="dashed")
plt.ylabel('Number of sites')
plt.xlabel('Alexa rank')
plt.grid(linestyle='dotted', c="#393b3d")
# plt.title('Distribution of reasons for not crawling')
ticks = []
for x in np.arange(1,12,1):
    if x == 11:
        ticks.append("100k+")
    ticks.append(str(x) + "0k")
plt.xticks(np.arange(1,12,1), ticks, rotation=35)
# plt.yticks(np.arange(0, 81, 10))
# plt.margins(0.001)
ax = fig.gca()
# Bound legend if desired
ax.xaxis.set_tick_params(width=2)
ax.yaxis.set_tick_params(width=2)
# ax.set_xticks(np.arange(0, 12, 1))
# ax.set_yticks(np.arange(0, 12., 1))
plt.legend((p1[0], p2[0], p3[0]), ('HTTPS not available', 'Robots.txt restriction', 'Miscellaneous'))
plt.ylim((0, 5000))
#plt.legend(bbox_to_anchor=(0,4010,20,20), loc="lower left",
                # mode="expand", borderaxespad=0, ncol=3)
fig.savefig('not_crawl_reasons.pdf', bbox_inches="tight")
print("Done saving...")
print("SAVING not_crawl_reasons.pdf...")
# exit(0)

# FIGURE 4A: CDF FOR # OF INCONSISTENCIES
error_num = {}
files = ["analysis-data/v2Results/diffresultsALL.txt"]
urls_proc = set()
for f in files:
    with open(f) as diff_r:
        for line in diff_r.readlines():
            items = line.split("***")
            domain = items[0].strip()
            url = items[1].strip()
            if not url in urls_proc:
                if domain not in error_num:
                    error_num[domain] = 1
                else:
                    error_num[domain] += 1
                urls_proc.add(url)

# Correction for duplicate results for a handful of sites
err = []
for dom in error_num:
    if error_num[dom] > 250:
        error_num[dom] = 250
    err.append(error_num[dom])

print(statistics.mean(err), "hi-cd")
print(len(err))
cdf(err, "Number of content-differences", "CDF", "CDF for errors found", save=False)
diffs_cdf = err[:]

# Find point > 50 pages
# sorted_arr = sorted(diffs_cdf)
# print(len(sorted_arr))
# index = 0
# for el in sorted_arr:
#     if el == 51:
#         print("point", index)
#         break
#     else:
#         index+=1

error_num = {}
files = ["analysis-data/v2Results/inacresultsALL-withouTIMEOUTwithoutCONNECTION.txt"]
for f in files:
    with open(f) as diff_r:
        for line in diff_r.readlines():
            items = line.split("***")
            domain = items[0].strip()
            if domain not in error_num:
                error_num[domain] = 1
            else:
                error_num[domain] += 1
err = []
for dom in error_num:
    err.append(error_num[dom])
print(statistics.mean(err), "hi-ca")
print(err)
print(len(err))
cdf(err, "Number of content inconsistencies", "CDF", "CDF for errors found", save=False, label="Content unavailabilities")
x = diffs_cdf
x, y = sorted(x), np.arange(len(x)) / len(x)
plt.plot(x, y, linewidth =3, ls="dashdot", label="Content differences")
plt.legend(loc='lower right')
ax = fig.gca()
ax.xaxis.set_tick_params(width=2)
ax.yaxis.set_tick_params(width=2)
plt.grid(linestyle='dotted', c="#393b3d")
plt.xticks(rotation=35)
fig.savefig('cdf_inconsistencies.pdf', bbox_inches="tight")
print("SAVING cdf_inconsistencies.pdf...")
# exit(0)

# FIGURE 4B - POPULARITY VS PRESENCE
def host_included(host, exact_match = True, bottom = False):
    if bottom:
        alex_hosts = parallelProcessing.fetch_domains(type="alexa", n=1000000)
        alex_hosts = [host.decode() for host in alex_hosts]
    else:
        alex_hosts = alexa_hosts
    for rank in range(0, len(alex_hosts)):
        if host.strip() == alex_hosts[rank].strip():
            return True, rank + 1
        if not exact_match:
            if host.endswith("." + alex_hosts[rank]):
                return True, rank + 1
    return False, -1

https_avail = set()
dom = 0
with open("analysis-data/v2Results/top100k/numpagesresults.txt") as cf_https:
    lines = cf_https.readlines()
    for line in lines:
        items = line.split(" *** ")
        assert len(items) == 2
        dom += 1
        if items[1].strip() != "0":
            https_avail.add(items[0].replace("www.", "").strip())

https_avail_bottom = set()
dom = 0
with open("analysis-data/v2Results/bottom10k/numpagesresults.txt") as cf_https:
    lines = cf_https.readlines()
    for line in lines:
        items = line.split(" *** ")
        assert len(items) == 2
        dom += 1
        if items[1].strip() != "0":
            https_avail_bottom.add(items[0].replace("www.", "").strip())

inac_hosts = {}
reasons = {}
with open("analysis-data/v2Results/top100k/inacresults-without-timeout.txt") as cf_inac:
    lines = cf_inac.readlines()
    for line in lines:
        if ":80" in line.split(" *** ")[0].split("/")[0]:
            continue
        host = line.split(" *** ")[0].strip().split(":")[0].split("/")[0].split("?")[0]
        host.replace("www.", "")
        if host.startswith("www."):
            host = host.replace("www.", "", 1)
        error = line.split(" *** ")[2]
        inac_hosts[host] = (line.split(" *** ")[0], error)
        if error not in reasons:
            reasons[error] = 0
        reasons[error] += 1
bins_wanted = 100
div_num = len(alexa_hosts) / bins_wanted
bins = {}
bins_supp = {}
for i in range(1, bins_wanted + 1):
    bins[i] = []
    bins_supp[i] = 0
# Compute bins HTTPS support
for host in https_avail:
    bins_supp[math.ceil(find_rank(host)/div_num)] += 1
count = 0
for host in inac_hosts:
    inc, rank = host_included(host, exact_match=True)
    if inc:
        bins[ math.ceil(rank/div_num)].append(host)
    else:
        count += 1
        print(host)
print("cu check inc fail: ", count)
print("*inac bins*")
x2 = []
y2 = []
for bin in bins:
    x2.append(bin)
    y2.append((len(bins[bin]) / (bins_supp[bin])))


cd_hosts = {}
with open("analysis-data/v2Results/top100k/top-diffresults-contd.txt") as cf_inac:
    lines = cf_inac.readlines()
    for line in lines:
        if ":80" in line.split("***")[0].strip().split("/")[0]:
            continue
        host = line.split("***")[0].strip().split(":")[0].split("/")[0].split("?")[0]
        host.replace("www.", "")
        if host.startswith("www."):
            host = host.replace("www.", "", 1)
        error = line.split("***")[1]
        cd_hosts[host] = (line.split(" *** ")[0], error)

bins_wanted = 100
div_num = len(alexa_hosts) / bins_wanted
bins = {}
for i in range(1, bins_wanted + 1):
    bins[i] = []
# bins[11] = []

print("cd check")
count = 0
for host in cd_hosts:
    inc, rank = host_included(host, exact_match=True)
    if inc:
        bins[ math.ceil(rank/div_num)].append(host)
    else:
        count += 1
print("cd check inc fail: ", count)

print("*cd bins*")
x = []
y = []
for bin in bins:
    x.append(bin)
    y.append((len(bins[bin]) / (bins_supp[bin])))
fig = plt.figure()
ax = fig.gca()
ax.xaxis.set_tick_params(width=2)
ax.yaxis.set_tick_params(width=2)
plt.grid(linestyle='dotted', c="#393b3d")
plt.xticks(rotation=35)
#circle1=plt.Circle((101,53 / len(https_avail_bottom)),0.002,color='r')
#plt.gcf().gca().add_artist(circle1)
plt.plot(x2, y2, label="Content unavailabilities", linewidth=2, zorder=1)
plt.plot(x, y, label="Content differences", linewidth=2, zorder=1)
plt.scatter(110, 58 / len(https_avail_bottom), s=80, c='#1f77b4', marker="o", zorder=2)
plt.scatter(110, 166 / len(https_avail_bottom), s=80, c='#ff7f0e', marker="o", zorder=2)

import numpy as np
x.append(110)
y.append(166 / len(https_avail_bottom))
x2.append(110)
y2.append(58 / len(https_avail_bottom))

x_ticks_org = list(np.arange(0, 120, 20))
x_ticks_org.append(110)
x_ticks_mod = list(np.arange(0, 120, 20))
x_ticks_mod.append("(LT)")
plt.xticks(x_ticks_org, x_ticks_mod)

plt.legend(loc='upper right')
# plt.suptitle('How website popularity influences results?')
plt.xlabel('Number of bins')
plt.ylabel('Presence of inconsistencies')
fig.savefig('scatter_error_presence.pdf', bbox_inches="tight")
print(np.corrcoef(x, y), "--cd")
print(np.corrcoef(x2, y2), "--inac")
print("SAVING scatter_error_presence.pdf...")

# FIGURE 4C - POPULARITY VS PREVALENCE
error_num = {}
files = ["analysis-data/v2Results/top100k/top-diffresults-contd.txt"]
for f in files:
    with open(f) as diff_r:
        for line in diff_r.readlines():
            items = line.split("***")
            domain = items[0].strip()
            if domain not in error_num:
                error_num[domain] = 1
            else:
                error_num[domain] += 1
bins_wanted = 100
div_num = len(alexa_hosts) / bins_wanted
bins = {}
for i in range(1, bins_wanted + 1):
    bins[i] = []
for host in error_num:
    rank = find_rank(host.replace("www.", ""))
    bins[ math.ceil(rank/div_num)].append(error_num[host])
print("*bins*")

x_cd = []
y_cd = []
y_err = []
for bin in bins:
    x_cd.append(bin)
    y_cd.append(statistics.mean(bins[bin]))
    try:
        y_err.append(statistics.stdev(bins[bin]))
    except:
        print(bin)
err = []
for dom in error_num:
    err.append(error_num[dom])
print(statistics.mean(err), "hi-cd")

error_num = {}
files = ["analysis-data/v2Results/top100k/inacresults-without-timeout.txt"]
for f in files:
    with open(f) as diff_r:
        for line in diff_r.readlines():
            items = line.split("***")
            domain = items[0].strip()
            if domain not in error_num:
                error_num[domain] = 1
            else:
                error_num[domain] += 1
err = []
for dom in error_num:
    err.append(error_num[dom])
print(statistics.mean(err), "hi-ca")
print(err)
print(len(err))
bins_wanted = 100
div_num = len(alexa_hosts) / bins_wanted
bins = {}
for i in range(1, bins_wanted + 1):
    bins[i] = []
for host in error_num:
    rank = find_rank(host.replace("www.", ""))
    bins[ math.ceil(rank/div_num)].append(error_num[host])
print("*bins*")
x = []
y = []
y_err = []
for bin in bins:
    x.append(bin)
    y.append(statistics.mean(bins[bin]))
    try:
        y_err.append(statistics.stdev(bins[bin]))
    except:
        print(bin)
# cdf(err, "Number of content-unavailability errors", "Ratio", "CDF for errors found", save=False)
fig = plt.figure()
ax = fig.gca()
ax.xaxis.set_tick_params(width=2)
ax.yaxis.set_tick_params(width=2)
plt.grid(linestyle='dotted', c="#393b3d")
plt.xticks(rotation=35)
plt.plot(x, y, label="Content unavailabilities", linewidth=2, zorder=1)
plt.plot(x_cd, y_cd, label="Content differences", linewidth=2, zorder=1)
plt.scatter(110, 2120/58, s=80, c='#1f77b4', marker="o", zorder=2)
plt.scatter(110, 7372/166, s=80, c='#ff7f0e', marker="o", zorder=2)
x_ticks_org = list(np.arange(0, 120, 20))
x_ticks_org.append(110)
x_ticks_mod = list(np.arange(0, 120, 20))
x_ticks_mod.append("(LT)")
plt.xticks(x_ticks_org, x_ticks_mod)
# locs, labels = plt.xticks()
# plt.setp(labels[6], rotation=90)
# plt.errorbar(x, y, yerr=y_err, label="", fmt='o', ecolor='black',capsize=1, capthick=1)
plt.legend(loc='upper left')
# plt.title('How many inaccessibility errors found?')
plt.xlabel('Number of bins')
plt.ylabel('Avg. inconsistencies per bin')
fig.savefig('scatter_error_prevalence.pdf', bbox_inches="tight")
x.append(110)
x_cd.append(110)
y.append(2120/58)
y_cd.append(7372/166) # cat bt-diffresults-contd.txt | awk -F* {'print $1'} | uniq -c | sort | awk {'print $1'} | python -c "import sys; print(sum(int(l) for l in sys.stdin))"
print(np.corrcoef(x,y), "--inac")
print(np.corrcoef(x_cd,y_cd), "--cd")
print(statistics.mean(y_cd), "cd")
print(statistics.mean(y), "ca")
print("SAVING scatter_error_prevalence.pdf...")
# exit(0)

# FIGURE 4C - POPULARITY VS PREVALENCE - BOXPLOT
# error_num = {}
# files = ["analysis-data/v2Results/top100k/top-diffresults-contd.txt"]
# for f in files:
#     with open(f) as diff_r:
#         for line in diff_r.readlines():
#             items = line.split("***")
#             domain = items[0].strip()
#             if domain not in error_num:
#                 error_num[domain] = 1
#             else:
#                 error_num[domain] += 1
# bins_wanted = 50
# div_num = len(alexa_hosts) / bins_wanted
# bins = {}
# for i in range(1, bins_wanted + 1):
#     bins[i] = []
# for host in error_num:
#     rank = find_rank(host.replace("www.", ""))
#     bins[ math.ceil(rank/div_num)].append(error_num[host])
# print("*bins*")
#
# x_cd = []
# y_cd = []
# box_plot_data_cd = []
# y_err = []
# for bin in bins:
#     x_cd.append(bin)
#     y_cd.append(statistics.mean(bins[bin]))
#     box_plot_data_cd.append(bins[bin])
#     try:
#         y_err.append(statistics.stdev(bins[bin]))
#     except:
#         print(bin)
# err = []
# for dom in error_num:
#     err.append(error_num[dom])
# print(statistics.mean(err), "hi-cd")
#
# error_num = {}
# files = ["analysis-data/v2Results/top100k/inacresults-without-timeout.txt"]
# for f in files:
#     with open(f) as diff_r:
#         for line in diff_r.readlines():
#             items = line.split("***")
#             domain = items[0].strip()
#             if domain not in error_num:
#                 error_num[domain] = 1
#             else:
#                 error_num[domain] += 1
# err = []
# for dom in error_num:
#     err.append(error_num[dom])
# print(statistics.mean(err), "hi-ca")
# print(err)
# print(len(err))
# bins_wanted = 50
# div_num = len(alexa_hosts) / bins_wanted
# bins = {}
# for i in range(1, bins_wanted + 1):
#     bins[i] = []
# for host in error_num:
#     rank = find_rank(host.replace("www.", ""))
#     bins[ math.ceil(rank/div_num)].append(error_num[host])
# print("*bins*")
#
# box_plot_data_inc = []
#
# x = []
# y = []
# y_err = []
# for bin in bins:
#     x.append(bin)
#     y.append(statistics.mean(bins[bin]))
#     box_plot_data_inc.append(bins[bin])
#     try:
#         y_err.append(statistics.stdev(bins[bin]))
#     except:
#         print(bin)
# # cdf(err, "Number of content-unavailability errors", "Ratio", "CDF for errors found", save=False)
# fig = plt.figure()
# ax = fig.gca()
#
# plt.boxplot(box_plot_data_inc, showfliers=False)
#
# ax.xaxis.set_tick_params(width=2)
# #ax.yaxis.set_tick_params(width=2)
# #plt.grid(linestyle='dotted', c="#393b3d")
# #plt.xticks(rotation=35)
# #plt.plot(x, y, label="Content unavailabilities", linewidth=2, zorder=1)
# #plt.plot(x_cd, y_cd, label="Content differences", linewidth=2, zorder=1)
# #plt.scatter(110, 2120/58, s=80, c='#1f77b4', marker="o", zorder=2)
# #plt.scatter(110, 7372/166, s=80, c='#ff7f0e', marker="o", zorder=2)
# x_ticks_org = list(np.arange(0, 50, 25))
# x_ticks_org.append(50)
# x_ticks_mod = list(np.arange(0, 50, 25))
# x_ticks_mod.append(50)
# plt.xticks(x_ticks_org, x_ticks_mod)
# # locs, labels = plt.xticks()
# # plt.setp(labels[6], rotation=90)
# # plt.errorbar(x, y, yerr=y_err, label="", fmt='o', ecolor='black',capsize=1, capthick=1)
# plt.legend(loc='upper left')
# plt.title('Alexa rank vs inconsistencies prevalence')
# plt.xlabel('Number of bins')
# plt.ylabel('Content unavailabilities')
# fig.savefig('boxplot_error_prevalence_un.pdf', bbox_inches="tight")
# exit(0)
