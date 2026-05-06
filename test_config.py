import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()
print("URL from env:", os.environ.get("CLOUDINARY_URL"))

# Let's configure it explicitly just to be bulletproof
url = os.environ.get("CLOUDINARY_URL")
if url:
    # Set the config using the parsed URL details
    import re
    # cloudinary://api_key:api_secret@cloud_name
    match = re.match(r"cloudinary://([^:]+):([^@]+)@(.+)", url)
    if match:
        cloudinary.config(
            api_key=match.group(1),
            api_secret=match.group(2),
            cloud_name=match.group(3),
            secure=True
        )

try:
    print("Testing config:", cloudinary.config().api_key)
except Exception as e:
    print(f"Error: {e}")
