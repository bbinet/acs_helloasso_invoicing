import json
import os

import pytest


@pytest.fixture
def sample_helloasso_item():
    """A realistic HelloAsso API item dict."""
    return {
        "id": 12345,
        "name": "Adhesion a l'ACS avec acces a la salle Emile Allais",
        "user": {
            "firstName": "Jean-Pierre",
            "lastName": "De La Fontaine"
        },
        "payer": {
            "email": "jp.fontaine@example.com"
        },
        "order": {
            "date": "2024-09-15T10:30:00+02:00",
            "formName": "Adhesion ACS 2024-2025"
        },
        "customFields": [
            {
                "name": "Soci\u00e9t\u00e9",
                "answer": "Ma Petite Entreprise"
            },
            {
                "name": "T\u00e9l\u00e9phone",
                "answer": "06 12 34 56 78"
            }
        ],
        "options": [
            {"name": "Football"},
            {"name": "Tennis"},
            {"name": "N'oubliez pas de venir"}
        ],
        "payments": [
            {
                "amount": 15000,
                "refundOperations": []
            }
        ],
        "amount": 15000
    }


@pytest.fixture
def sample_config():
    """A minimal conf.json-style dict with credentials and conf sections."""
    return {
        "credentials": {
            "helloasso": {
                "id": "test-client-id",
                "secret": "test-client-secret"
            }
        },
        "conf": {
            "helloasso": {
                "api_url": "https://api.helloasso.com",
                "organization_name": "acs-test",
                "formType": "MemberShip",
                "formSlug": "adhesion-2024-2025"
            },
            "sendemail": {
                "from": "test@example.com"
            }
        }
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """Write sample_config to a file and return its path."""
    config_path = tmp_path / "conf.json"
    config_path.write_text(json.dumps(sample_config, indent=4))
    return str(config_path)
