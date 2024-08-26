from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import random
from motor.motor_asyncio import AsyncIOMotorClient
import os

app = FastAPI()


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_CLUSTER = os.getenv("DB_CLUSTER")

MONGO_URL = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@{DB_CLUSTER}.mongodb.net/{DB_NAME}?retryWrites=true&w=majority"

# Create a MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

class PlaceRequest(BaseModel):
    places: List[str]
    lang_res: str

@app.post("/places/")
async def get_places(request: PlaceRequest):
    if request.lang_res not in ["en", "ar"]:
        raise HTTPException(status_code=400, detail="Invalid lang_res code. Use 'en' or 'ar'.")

    try:
        # Query MongoDB for all governorates
        cursor = db.governorates.find()
        
        all_sites = []
        async for governorate in cursor:
            for site in governorate.get("HistoricalSites", []) + governorate.get("RecreationalSites", []):
                    
                    # Include only the fields in the requested language and additional fields
                    site_res = {key.replace(f"{request.lang_res}_", ""): value
                                for key, value in site.items()
                                if key.startswith(f"{request.lang_res}_")}
                    site_res["Photo_URL"] = site.get("Photo_URL")
                    site_res["Entry_Fee"] = site.get("Entry_Fee")
                    
                    # Extract and add the location coordinates to the site response
                    if "Location" in site: 
                        site_res["Location"] = site["Location"]

                    else:
                        site_res["Location"] = {
                            "Coordinates": []
                        }
                    site_res["siteId"]=site["siteId"]
                    all_sites.append(site_res)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while accessing the database: {str(e)}")

    if not all_sites:
        raise HTTPException(status_code=404, detail="No sites matched the provided names.")

    # Shuffle the list and limit the number of places
    random.shuffle(all_sites)
    limited_sites = all_sites[:30]

    return {"number_of_places": len(limited_sites), "sites": limited_sites}
