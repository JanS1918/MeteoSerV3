from cryptography import x509

paths = [
    r"C:\mosquitto\conf\certs\ca.crt",
    r"C:\mosquitto\conf\certs\server.crt",
    r"C:\mosquitto\conf\certs\server.key",
]
for p in paths:
    print("FILE:", p)
    try:
        data = open(p, "rb").read()
    except Exception as e:
        print("  Missing or unreadable:", e)
        continue
    # show first bytes hex
    print("  size:", len(data))
    print("  header hex:", " ".join(["%02X" % b for b in data[:16]]))
    if b"-----BEGIN" in data:
        print("  contains PEM header")
    else:
        print("  no PEM header")
    if p.endswith(".key"):
        print("  skipping x509 load for key")
        continue
    try:
        cert = x509.load_pem_x509_certificate(data)
        print("  loaded as PEM subject:", cert.subject)
    except Exception as e:
        try:
            cert = x509.load_der_x509_certificate(data)
            print("  loaded as DER subject:", cert.subject)
        except Exception as e2:
            print("  failed to parse cert:", e, e2)
print("done")
