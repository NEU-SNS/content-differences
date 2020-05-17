import ssl
import OpenSSL
import os
from collections import Counter
import OpenSSL

# Define paths
certs_dir = "/tmp/resultsDetailed/v2_certs_fetch_top100k/"

# Load certs
issuers = []
for filename in os.listdir(certs_dir):
    if len(issuers) > 100000:
        break
    with open(os.path.join(certs_dir, filename), "rb") as data:
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, data.read())
        cmps = x509.get_issuer().get_components()
        for c in cmps:
            if c[0] == b'O':
                try:
                    issuers.append(c[1].decode())
                    #if "Let's Encrypt" == c[1].decode():
                    #print(c[1], filename, cmps)
                except:
                    print("excepted...")
print("Total certificates", len(issuers))
#for issuer in Counter(issuers):
#    print(issuer)
print("Distribution of issuers:", Counter(issuers))


