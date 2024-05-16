import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from datetime import datetime, timedelta

def generate_self_signed_cert(cert_path, key_path):
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        public_key = private_key.public_key()

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"CountryCode"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"StateCode"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"CityCode"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Wellknown"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"API_v2"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).sign(private_key, hashes.SHA256(), default_backend())

        with open(cert_path, 'wb') as cert_file:
            cert_file.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, 'wb') as key_file:
            key_file.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))