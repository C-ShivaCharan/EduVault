import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

load_dotenv()
cloudinary.config(secure=True)

try:
    # Create a dummy 12MB file to test upload_large
    print("Creating dummy file...")
    dummy_file = "test_large_upload.txt"
    with open(dummy_file, "wb") as f:
        f.write(os.urandom(12 * 1024 * 1024))
    
    print("Uploading to Cloudinary using upload_large...")
    result = cloudinary.uploader.upload_large(
        dummy_file,
        resource_type="raw",
        folder="EduVault/Test"
    )
    print("Upload successful!")
    print("URL:", result.get("secure_url"))
    
    # Cleanup
    cloudinary.uploader.destroy(result.get("public_id"), resource_type="raw")
    os.remove(dummy_file)
    print("Cleanup successful!")
except Exception as e:
    print(f"Error: {e}")
