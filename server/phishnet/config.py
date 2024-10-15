import os
from jwcrypto import jwk
import requests
from dotenv import load_dotenv

load_dotenv()

ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST')
ELASTICSEARCH_USER = os.getenv('ELASTICSEARCH_USER')
ELASTICSEARCH_PASSWORD = os.getenv('ELASTICSEARCH_PASSWORD')
PROPAGATE_EXCEPTIONS = True

oidc_config = requests.get('https://zitadel.databending.ca/.well-known/openid-configuration').json()
oidc_jwks_uri = requests.get(oidc_config['jwks_uri']).json()
JWT_PUBLIC_KEYS = oidc_jwks_uri['keys']
