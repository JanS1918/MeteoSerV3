"""Generate self-signed CA and MQTT server certificates for Mosquitto.

Outputs files under tools/certs/ so they can be copied to C:/mosquitto/conf/certs.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

BASE_DIR = Path(__file__).resolve().parent
CERT_DIR = BASE_DIR / "certs"
CERT_DIR.mkdir(parents=True, exist_ok=True)

CA_KEY_PATH = CERT_DIR / "ca.key.pem"
CA_CERT_PATH = CERT_DIR / "ca.cert.pem"
SERVER_KEY_PATH = CERT_DIR / "server.key.pem"
SERVER_CERT_PATH = CERT_DIR / "server.cert.pem"

VALIDITY_DAYS = 3650


def _write_private_key(path: Path, key: rsa.RSAPrivateKey) -> None:
    data = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(data)


def _write_certificate(path: Path, cert: x509.Certificate) -> None:
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def generate_ca() -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MeteoSer"),
            x509.NameAttribute(NameOID.COMMON_NAME, "MeteoSer MQTT Root CA"),
        ]
    )
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=VALIDITY_DAYS))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            key_cert_sign=True,
            crl_sign=True,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            encipher_only=False,
            decipher_only=False,
        ), critical=True)
        .sign(private_key=key, algorithm=hashes.SHA256())
    )
    return key, cert


def generate_server_cert(ca_key: rsa.RSAPrivateKey, ca_cert: x509.Certificate) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MeteoSer"),
            x509.NameAttribute(NameOID.COMMON_NAME, "MeteoSer MQTT Server"),
        ]
    )
    now = datetime.now(timezone.utc)
    san = x509.SubjectAlternativeName(
        [
            x509.DNSName("localhost"),
            x509.DNSName("meteoser.local"),
            x509.DNSName("meteoser"),
            x509.IPAddress(IPv4Address("127.0.0.1")),
            x509.IPAddress(IPv6Address("::1")),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=VALIDITY_DAYS))
        .add_extension(san, critical=False)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key=ca_key, algorithm=hashes.SHA256())
    )
    return key, cert


def main() -> None:
    ca_key, ca_cert = generate_ca()
    _write_private_key(CA_KEY_PATH, ca_key)
    _write_certificate(CA_CERT_PATH, ca_cert)

    server_key, server_cert = generate_server_cert(ca_key, ca_cert)
    _write_private_key(SERVER_KEY_PATH, server_key)
    _write_certificate(SERVER_CERT_PATH, server_cert)

    print(f"Generated CA: {CA_CERT_PATH}")
    print(f"Generated server certificate: {SERVER_CERT_PATH}")


if __name__ == "__main__":
    main()
