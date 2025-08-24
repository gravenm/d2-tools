import requests
from core.constants import *
import zipfile
import os
import io

def get_access_token(auth_code):
    payload = {"grant_type": "authorization_code", "code": auth_code, "client_id": CLIENT_ID}
    try:
        res = requests.post(TOKEN_URL, data=payload, headers=HEADERS)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        # st.error(f"Error getting access token: {e}")
        return None

def get_destiny_profile(token_data):
    headers = {"X-API-Key": API_KEY, "Authorization": f"Bearer {token_data['access_token']}"}
    url = f"{API_ROOT_PATH}/User/GetMembershipsById/{token_data['membership_id']}/254/"
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()['Response']['destinyMemberships'][0]
    except Exception as e:
        # st.error(f"Error getting profile: {e}")
        return None

def get_profile_with_components(profile, token_data):
    headers = {"X-API-Key": API_KEY, "Authorization": f"Bearer {token_data['access_token']}"}
    url = f"{API_ROOT_PATH}/Destiny2/{profile['membershipType']}/Profile/{profile['membershipId']}/?components=102,304,305"
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        # st.error(f"Error getting components: {e}")
        return None

def get_manifest():
    # st.write("Checking for Destiny 2 Manifest...")
    try:
        manifest_response = requests.get(MANIFEST_URL, headers=HEADERS)
        manifest_response.raise_for_status()
        manifest_data = manifest_response.json()
        manifest_path = manifest_data['Response']['mobileWorldContentPaths']['en']
        manifest_db_url = f"https://www.bungie.net{manifest_path}"
        version_file = f"{MANIFEST_FILE_NAME}.version"
        if os.path.exists(MANIFEST_FILE_NAME) and os.path.exists(version_file) and open(version_file).read() == manifest_path:
        #     st.success("Manifest is up to date.")
            return MANIFEST_FILE_NAME
        # with st.spinner("Downloading new manifest..."):
        else:
            db_response = requests.get(manifest_db_url)
            db_response.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(db_response.content)) as z:
                file_name_in_zip = os.path.basename(manifest_path)
                with z.open(file_name_in_zip) as zf, open(MANIFEST_FILE_NAME, "wb") as f:
                    f.write(zf.read())
            with open(version_file, "w") as f: f.write(manifest_path)
        # st.success("Manifest downloaded.")
        return MANIFEST_FILE_NAME
    except Exception as e:
        # st.error(f"Error getting manifest: {e}")
        return None
