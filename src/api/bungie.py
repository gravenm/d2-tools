# src/api/bungie.py

import requests
from core.constants import *
import zipfile
import os
import io

def get_access_token(auth_code):
    payload = {"grant_type": "authorization_code", "code": auth_code, "client_id": CLIENT_ID}
    return _request_token(payload)

def refresh_access_token(refresh_token):
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    return _request_token(payload)

def _request_token(payload):
    """Handles both initial token requests and refreshes."""
    try:
        res = requests.post(TOKEN_URL, data=payload, headers=HEADERS)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        # Using a generic error here as st.error is a UI function
        print(f"Error requesting token: {e}")
        return None

def get_destiny_profile(token_data):
    headers = {"X-API-Key": API_KEY, "Authorization": f"Bearer {token_data['access_token']}"}
    url = f"{API_ROOT_PATH}/User/GetMembershipsById/{token_data['membership_id']}/254/"
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()['Response']['destinyMemberships'][0]
    except Exception as e:
        print(f"Error getting profile: {e}")
        return None

def get_profile_with_components(profile, token_data):
    headers = {"X-API-Key": API_KEY, "Authorization": f"Bearer {token_data['access_token']}"}
    url = f"{API_ROOT_PATH}/Destiny2/{profile['membershipType']}/Profile/{profile['membershipId']}/?components=102,201,205,304,305"
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Error getting components: {e}")
        return None

def get_manifest():
    try:
        manifest_response = requests.get(MANIFEST_URL, headers=HEADERS)
        manifest_response.raise_for_status()
        manifest_data = manifest_response.json()
        manifest_path = manifest_data['Response']['mobileWorldContentPaths']['en']
        manifest_db_url = f"https://www.bungie.net{manifest_path}"
        version_file = f"{MANIFEST_FILE_NAME}.version"
        if os.path.exists(MANIFEST_FILE_NAME) and os.path.exists(version_file) and open(version_file).read() == manifest_path:
            return MANIFEST_FILE_NAME
        else:
            db_response = requests.get(manifest_db_url)
            db_response.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(db_response.content)) as z:
                file_name_in_zip = os.path.basename(manifest_path)
                with z.open(file_name_in_zip) as zf, open(MANIFEST_FILE_NAME, "wb") as f:
                    f.write(zf.read())
            with open(version_file, "w") as f: f.write(manifest_path)
        return MANIFEST_FILE_NAME
    except Exception as e:
        print(f"Error getting manifest: {e}")
        return None