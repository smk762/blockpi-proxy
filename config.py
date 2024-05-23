import os
from dotenv import load_dotenv
import json_utils

script_path = os.path.realpath(os.path.dirname(__file__))

class ConfigFastAPI:
    """Class for API configuration."""

    def __init__(self) -> None:
        load_dotenv()
        print("Loading environment variables...")
        # FastAPI Environment Variables
        self.FASTAPI = {
            "HOST": os.getenv("HOST") or "127.0.0.1",
            "SUBDOMAIN": os.getenv("SUBDOMAIN"),
            "PORT": self.int_or_none(os.getenv("FASTAPI_PORT")) or 8528,
            "USE_MIDDLEWARE": os.getenv("USE_MIDDLEWARE") == "True",
            "CORS_ORIGINS": "*",
            "TAGS": self.get_FASTAPI_TAGS(),
            "METADATA": self.get_FASTAPI_METADATA(),
            "SSL_KEY": os.getenv("SSL_KEY") or None,
            "SSL_CERT": os.getenv("SSL_CERT") or None,
        }
        print(f"FASTAPI Environment Variables: {self.FASTAPI}")
        self.FASTAPI.update(
            {
                "FASTAPI_URL": f"https://{self.FASTAPI['SUBDOMAIN']}:{self.FASTAPI['PORT']}"
            }
        )
        if os.getenv("CORS_ORIGINS"):
            self.FASTAPI.update({"CORS_ORIGINS": os.getenv("CORS_ORIGINS").split(" ")})

        self.COSMOS_RPC_URL = os.getenv("COSMOS_RPC_URL")
        self.API_KEYS = {}
        self.API_SECRETS = {}
        self.API_URLS = {}
        for k, v in os.environ.items():
            self.API_KEYS.update({k.replace("_APIKEY", ""): v})
            self.API_SECRETS.update({k.replace("_SECRET", ""): v})
            if "_BASEURL" in k:
                if v.endswith("/"):
                    v = v[:-1]
                self.API_URLS.update({k.replace("_BASEURL", ""): v})

    def int_or_none(self, value):
        """Returns an integer or None."""
        try:
            return int(value)
        except:
            return None

    def get_FASTAPI_METADATA(self):
        """Returns the API metadata tags"""
        return {
            "title": "API Template",
            "description": "Template for FastAPI",
            "version": "0.1.0",
            "contact": {
                "name": "Komodo Platform",
                "url": "https://komodoplatform.com",
                "email": "smk@komodoplatform.com",
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT",
            },
        }

    def get_FASTAPI_TAGS(self):
        """Returns the API tags"""
        return [
            {
                "name": "data",
                "description": "Returns data from json file.",
            }
        ]


if __name__ == "__main__":
    pass
