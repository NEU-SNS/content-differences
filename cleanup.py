import fcntl, time, zipfile, random, os
random.seed(time.time())

base_dir = "/net/data/contentdifferences/v2/JS/"
base_dir_temp = "/tmp/resultsDetailed/"

while True:
    # Get the list of domains processed so far
    dd = open(base_dir_temp + 'doneDomains.txt', 'r+')
    fcntl.flock(dd, fcntl.LOCK_EX)
    lines = dd.readlines()
    if len(lines) > 1:
        while True:
            possible_name = base_dir + 'data-js' + str(random.randint(1, 1000000)) + '.zip'
            if not os.path.exists(possible_name):
                break
        zipf = zipfile.ZipFile(possible_name, 'w', zipfile.ZIP_DEFLATED)

        # Clear the list
        dd.seek(0)
        dd.truncate()
        fcntl.flock(dd, fcntl.LOCK_UN)
        dd.close()

        # Archive the files into zip
        for line in lines:
            domain = line.strip()
            zipf.write(base_dir_temp + "logs/" + domain + ".log")
            zipf.write(base_dir_temp + "summary/summary-" + domain + '.txt')
            #zipf.write("resultsDetailed/links/" + domain + "-links.txt")
            #zipf.write("resultsDetailed/links/" + domain + "-references.txt")
        zipf.close()

        # Delete the files
        for line in lines:
            domain = line.strip()
            os.remove(base_dir_temp + "logs/" + domain + ".log")
            os.remove(base_dir_temp + "summary/summary-" + domain + '.txt')
            #os.remove("resultsDetailed/links/" + domain + "-links.txt")
            #os.remove("resultsDetailed/links/" + domain + "-references.txt")
    
        with open(base_dir_temp + 'doneZipped.txt', 'a') as f:
            for line in lines:
                f.write(line.strip() + "\n")
    
    else:
        fcntl.flock(dd, fcntl.LOCK_UN)
        dd.close()
    time.sleep(2)
