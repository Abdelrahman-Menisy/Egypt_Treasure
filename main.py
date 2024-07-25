from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict
import json
from difflib import SequenceMatcher
import codecs

app = FastAPI()

def load_json_file(file_path: str):
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'ascii']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError:
            continue
    
    # If all encodings fail, try binary read
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            return json.loads(raw_data.decode('utf-8-sig'))
    except:
        raise ValueError(f"Unable to read or parse the file: {file_path}")

# Load the data
try:
    data = load_json_file("data.json")  # Adjust the path as necessary
except Exception as e:
    print(f"Error loading data: {str(e)}")
    data = []

# Extract all places
all_places = []
for governorate in data:
    for site_type in ["HistoricalSites", "RecreationalSites"]:
        if site_type in governorate:
            all_places.extend(governorate[site_type])

# Input model
class PlacesInput(BaseModel):
    places: List[str]

# Function to calculate similarity between two strings
def string_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Function to get recommendations
def get_recommendations(input_places: List[str], all_places: List[Dict], num_recommendations: int = 10) -> List[Dict]:
    recommendations = []
    for place in all_places:
        if place['en_Site_Name'] not in input_places:
            similarity = max(string_similarity(input_place, place['en_Site_Name']) for input_place in input_places)
            recommendations.append((place, similarity))
    
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [rec[0] for rec in recommendations[:num_recommendations]]

# Function to translate place data to the specified language
def translate_place(place: Dict, lang: str) -> Dict:
    translated = {}
    for key, value in place.items():
        if key.startswith(f"{lang}_"):
            translated[key[3:]] = value
        elif not key.startswith("en_") and not key.startswith("ar_"):
            translated[key] = value
    return translated

@app.post("/recommend/")
async def recommend_places(
    places_input: PlacesInput,
    num_recommendations: int = Query(default=10, ge=1, le=50, description="Number of recommendations to return"),
    lang: str = Query(default="en", regex="^(en|ar)$", description="Language for the response (en or ar)")
):
    if not places_input.places:
        raise HTTPException(status_code=400, detail="No input places provided")
    
    if not all_places:
        raise HTTPException(status_code=500, detail="No place data available")
    
    recommendations = get_recommendations(places_input.places, all_places, num_recommendations)
    
    # Translate recommendations to the specified language
    translated_recommendations = [translate_place(place, lang) for place in recommendations]
    
    return {"recommendations": translated_recommendations}

@app.get("/")
async def root():
    return {"message": "Welcome to the Tourism Recommendation System"}

@app.get("/places")
async def get_all_places(
    lang: str = Query(default="en", regex="^(en|ar)$", description="Language for the response (en or ar)")
):
    if lang == "en":
        return {"places": [place['en_Site_Name'] for place in all_places]}
    else:
        return {"places": [place['ar_Site_Name'] for place in all_places]}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
