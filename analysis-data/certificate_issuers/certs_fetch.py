import ssl
#import OpenSSL
import os
from collections import Counter
import sys
import socket
import OpenSSL

# Define paths
#df = "/Users/talhaparacha/Downloads/impresults-top100k/diffresults-contd.txt"
certs_dir = "/tmp/resultsDetailed/v2_certs_fetch_top100k/"
m = sys.argv[1].strip()

if os.path.isfile(certs_dir + m + ".crt"):
    print("skipping...")
else:
    print("processing...")

# Fetch and save certs
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((m, 443))
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    s = ctx.wrap_socket(s, server_hostname=m)
    cert_bin = s.getpeercert(True)
    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_bin)
    #print(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode())
    with open(certs_dir + m + ".crt", "w") as cf:
        cf.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode())
    #cert = ssl.get_server_certificate((m, 443), ssl_version=ssl.PROTOCOL_TLSv1_2)
    #with open(certs_dir + m + ".crt", "w") as cf:
    #    cf.write(cert)
except Exception as e:
        print(repr(e), m)

