"""
Upload portraits for EN memorials to Supabase Storage.
Looks up memorials by name, downloads portrait, uploads to S3/Supabase.
"""
import os, io, requests, boto3, sqlalchemy as sa
from sqlalchemy.orm import Session
from app.models import Memorial, Media
from app.db import SessionLocal

DB_URL = os.environ["DATABASE_URL"]
S3_ENDPOINT = os.environ.get("AWS_S3_ENDPOINT_URL", "")
S3_BUCKET = os.environ.get("AWS_S3_BUCKET_NAME", "memorial-media")
AWS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
PUBLIC_BUCKET_URL = os.environ.get("PUBLIC_BUCKET_URL", "")

# Portraits from randomuser.me — deterministic seed URLs
PORTRAITS = {
    # Kelly family (Irish-Australian, Sydney)
    "Sean Patrick Kelly":           "https://randomuser.me/api/portraits/men/62.jpg",
    "Brigid O'Brien Kelly":         "https://randomuser.me/api/portraits/women/62.jpg",
    "Thomas Michael Kelly":         "https://randomuser.me/api/portraits/men/63.jpg",
    "Rose Whitfield Kelly":         "https://randomuser.me/api/portraits/women/63.jpg",
    "James William Kelly":          "https://randomuser.me/api/portraits/men/64.jpg",
    "Helen Margaret Anderson Kelly":"https://randomuser.me/api/portraits/women/64.jpg",
    "Robert James Kelly":           "https://randomuser.me/api/portraits/men/65.jpg",
    # Anderson family (Scottish-Australian, Sydney)
    "Duncan Alasdair Anderson":     "https://randomuser.me/api/portraits/men/70.jpg",
    "Flora Mackenzie Anderson":     "https://randomuser.me/api/portraits/women/70.jpg",
    "William Duncan Anderson":      "https://randomuser.me/api/portraits/men/71.jpg",
    "Agnes Brown Anderson":         "https://randomuser.me/api/portraits/women/71.jpg",
    # Expanded branch
    "George William Anderson":      "https://randomuser.me/api/portraits/men/72.jpg",
    "Margaret Fraser Anderson":     "https://randomuser.me/api/portraits/women/72.jpg",
    "Ian George Anderson":          "https://randomuser.me/api/portraits/men/73.jpg",
    "Evelyn Parker Anderson":       "https://randomuser.me/api/portraits/women/73.jpg",
    # Chang family (Chinese-Australian, Sydney)
    "Wei Chang":                    "https://randomuser.me/api/portraits/men/80.jpg",
    "Mei Lin Chang":                "https://randomuser.me/api/portraits/women/80.jpg",
    "David Chang":                  "https://randomuser.me/api/portraits/men/81.jpg",
    "Sarah Chang":                  "https://randomuser.me/api/portraits/women/81.jpg",
    # Rossi family (Italian-Australian, Sydney)
    "Marco Rossi":                  "https://randomuser.me/api/portraits/men/90.jpg",
    "Elena Rossi":                  "https://randomuser.me/api/portraits/women/90.jpg",
    "Antonio Rossi":                "https://randomuser.me/api/portraits/men/91.jpg",
}

def get_s3_client():
    kwargs = dict(
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
        region_name=AWS_REGION,
    )
    if S3_ENDPOINT:
        kwargs["endpoint_url"] = S3_ENDPOINT
    return boto3.client("s3", **kwargs)

def upload_portrait(s3, name, url):
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        print(f"  ⚠️  Could not download portrait for {name}: {resp.status_code}")
        return None
    data = resp.content
    safe_name = name.lower().replace(' ', '_').replace("'", '')
    key = f"portraits/{safe_name}.jpg"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=data,
        ContentType="image/jpeg",
    )
    # Build public URL
    if PUBLIC_BUCKET_URL:
        file_url = f"{PUBLIC_BUCKET_URL.rstrip('/')}/{key}"
    elif S3_ENDPOINT:
        file_url = f"{S3_ENDPOINT.rstrip('/')}/{S3_BUCKET}/{key}"
    else:
        file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    return file_url, key, len(data)

def main():
    engine = sa.create_engine(DB_URL)
    s3 = get_s3_client()

    with Session(engine) as db:
        for name, portrait_url in PORTRAITS.items():
            memorial = db.query(Memorial).filter(Memorial.name == name).first()
            if not memorial:
                print(f"  ⏭️  Memorial not found: {name}")
                continue

            # Check if portrait already uploaded
            existing = db.query(Media).filter(
                Media.memorial_id == memorial.id,
            ).first()
            if existing and existing.file_url:
                print(f"  ⏭️  Portrait already exists for {name}")
                # Ensure cover is set
                if not memorial.cover_photo_id:
                    memorial.cover_photo_id = existing.id
                    db.commit()
                continue

            result = upload_portrait(s3, name, portrait_url)
            if not result:
                continue
            file_url, file_path, file_size = result

            media = Media(
                memorial_id=memorial.id,
                file_name=f"{name.lower().replace(' ', '_')}.jpg",
                file_path=file_path,
                file_url=file_url,
                media_type="PHOTO",
                file_size=file_size,
                mime_type="image/jpeg",
            )
            db.add(media)
            db.flush()

            if not memorial.cover_photo_id:
                memorial.cover_photo_id = media.id

            db.commit()
            print(f"  ✅ Portrait uploaded for {name} → {file_url[:60]}...")

    print("\n🏁 Portraits done.")

if __name__ == "__main__":
    main()
