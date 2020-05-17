# HTTP/S Content Differences Crawler

Crawler and data analysis code for the paper "A Deeper Look at Web Content Availability and Consistency over HTTP/S" presented at Network Traffic Measurement and Analysis Conference (TMA) 2020.

The structure of the repository is as follows:

## Crawler code

    .
    ├── chrome_fetch/chrome_fetch.py          # Script for accessing a page content using Chromium, via remote debug protocol
    ├── inaccessible.py          # Script for processing a single website (Python-based pipelines)
    ├── inaccessibleJS.py          # Script for processing a single website (Chromium based pipeline)
    ├── parallelProcessing.py    # Script for parallelizing processing for a set of websites
    ├── cleanup.py    # Script for archiving results for a set of websites

    ├── content*.py    # Script for further processing archived results generated using parallelProcessing.py and cleanup.py. Parallelizes on multiple .zip files for faster processing.   
        .
        ├── contentInacParallel.py # Script for getting final list of content unavailabilities (i.e. a slow follow-up crawl)
        ├── contentDiffParallel.py # Script for getting final list of content differences (i.e. a slow follow-up crawl using parameters alpha, beta and gamma)
        └── others/* # Other scripts

### Usage

Configure the parameters in parallelProcessing.py to tune the crawl speed / websites list and launch it with Python 3. Crawl depth can be controlled via the totalLinks parameter in inaccessible*.py. Requirements.txt file is available for configuring dependencies.

The structure of the generated results directory will be:
    .
    ├── links/                   # Internal links saved for each domain
    ├── logs/                    # Logs for each domain to record crawler activity
    ├── summary/                 # Content crawled for each domain
    ├── doneDomains.txt          # List of successfully processed domains
    └── time-dist.txt            # Cumulative time taken for processing domains

Each file in the summary directory will correspond to results for a single website. Each line within the file will correspond to results
for a particular internal link. Results are delimited with *** chars and include:

         ├── internal link URL
         ├── URL for where the internal link was referenced  
         ├── success over HTTP (bool)              
         ├── success over HTTPS (bool)
         ├── error, if any, over HTTP             
         ├── error, if any, over HTTPS
         ├── final URL over HTTP
         ├── final URL over HTTPS             
         ├── time taken for HTTP
         ├── time taken for HTTPS
         ├── headers received over HTTP
         ├── headers received over HTTPS
         ├── base64-encoded body received over HTTP (only if byte-wise different than https)
         ├── base64-encoded body received over HTTPS (only if byte-wise different than https)

## Data analysis code for results in the paper

    .
    ├── strictThreshold.py    # Script for filtering content differences results using a stricter threshold
    ├── comparisonCheck.py    # Script for comparing HTTPS adoption metrics (Table III)
    ├── figures.py    # Script for generating all paper figures
    ├── final_urls_analysis.py    # Script for analyzing misconfigured redirections (Table I and II)
    ├── find_chrome_doms.py    # Script for finding 100 sample websites to use during cross-validation of results (Section IV-A)
    ├── verifyBrowser.py    # Script for validating which results from Python-based pipeline also appear in Chromium-based pipeline
    ├── verify_intersection.py    # Script for validating missing results in Chromium-based pipeline still appear in Python-based pipeline
    └── analysis-data/    # All results used in the analysis


### Dataset

We have data crawled for ~68k HTTPS supporting websites, which includes their internal links (at most 250) as well as content retrieved over HTTP/S (only if different). It is around ~500GB in size, and we can make it available upon request. For ethical concerns, the data can only be used for research purposes. Please contact us at paracha.m@husky.neu.edu for support. 
