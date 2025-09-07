# scheduler.py
# Run this periodically (e.g., via cron) to ingest hourly temps for all tracked cities.

import sys
from typing import Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import TrackedCity, Base
from config import DATABASE_URL
from sqlalchemy import create_engine
from weather_api import ensure_all_cities_tracked
from weather_api import ingest_one
from config import TRACKED_CITIES

#map cities to coordinates
def main() -> int:
    engine = create_engine(DATABASE_URL, future=True)
    Base.metadata.create_all(engine)
    
    #use ensure_all_cities_tracked instead of ingest_one
    ensure_all_cities_tracked()
    #use ingest_one to ingest data for all cities
    for city in TRACKED_CITIES.keys():
        coords = TRACKED_CITIES[city]
        lat, lon = coords["lat"], coords["lon"]
        ingest_one(city, lat, lon)
    return 0

    # get all tracked cities from DB
    with Session(engine, future=True) as session:
        db_cities = [c.city for c in session.execute(select(TrackedCity)).scalars().all()]

    if not db_cities:
        print("No tracked cities yet. Add at least one row to tracked_cities and rerun.")
        return 0

    status = 0



if __name__ == "__main__":
    sys.exit(main())
