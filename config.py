import os
from dotenv import load_dotenv
import json_utils

script_path = os.path.realpath(os.path.dirname(__file__))


class ConfigFastAPI:
    """Class for API configuration."""

    def __init__(self) -> None:
        load_dotenv()
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
        self.FASTAPI.update(
            {
                "FASTAPI_URL": f"https://{self.FASTAPI['SUBDOMAIN']}:{self.FASTAPI['PORT']}"
            }
        )
        if os.getenv("CORS_ORIGINS"):
            self.FASTAPI.update({"CORS_ORIGINS": os.getenv("CORS_ORIGINS").split(" ")})

        self.API_KEYS = {}
        self.API_SECRETS = {}
        self.API_URLS = {}
        for k, v in os.environ.items():
            self.API_KEYS.update({k.replace("_APIKEY", ""): v})
            self.API_SECRETS.update({k.replace("_SECRET", ""): v})
            if k.endswith("_URL"):
                if "atom" in k and not v.endswith("/"):
                    v = f"{v}/"
                elif v.endswith("/"):
                    v = v[:-1]
                network = k.split("_")[0].lower()
                proto = k.split("_")[1].lower()
                if network not in self.API_URLS:
                    self.API_URLS.update({network.lower(): {"rpc": None, "wss": None}})
                if proto == "rpc":
                    self.API_URLS[network]["rpc"] = v
                if proto == "wss":
                    self.API_URLS[network]["wss"] = v

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
