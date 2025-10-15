# attachment_utils.py

import os
import base64

def save_attachments(attachments, folder):
    os.makedirs(folder, exist_ok=True)
    for att in attachments:
        name = att["name"]
        url = att["url"]
        if url.startswith("data:"):
            # Parse data URI
            header, encoded = url.split(",", 1)
            data = base64.b64decode(encoded)
            with open(os.path.join(folder, name), "wb") as f:
                f.write(data)
    return folder
