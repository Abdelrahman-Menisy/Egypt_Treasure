from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
import random

app = FastAPI()

# Load database from JSON file
def load_database(file_path: str):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)

# Load data
db = load_database(r"data.json")

class PlaceRequest(BaseModel):
    places: List[str]
    lang_res: str

@app.post("/places/")
async def get_places(request: PlaceRequest):
    if request.lang_res not in ["en", "ar"]:
        raise HTTPException(status_code=400, detail="Invalid lang_res code. Use 'en' or 'ar'.")

    governorates_set = set()

    # Identify governorates for the input places
    for governorate in db:
        historical_sites = governorate.get("HistoricalSites", [])
        recreational_sites = governorate.get("RecreationalSites", [])
        
        for site in historical_sites + recreational_sites:
            site_name = site.get(f"{request.lang_res}_Site_Name")
            if site_name in request.places:
                governorates_set.add(governorate["governorateName"])

    if not governorates_set:
        raise HTTPException(status_code=404, detail="No sites matched the provided names.")

    # Collect all places from the identified governorates
    all_sites = []
    for governorate in db:
        if governorate["governorateName"] in governorates_set:
            print(governorate)
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

    # Shuffle the list and limit the number of places
    random.shuffle(all_sites)
    limited_sites = all_sites[:30]

    return {"number_of_places": len(limited_sites), "sites": limited_sites}
