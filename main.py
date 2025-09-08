import streamlit as st
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import WeatherData, TrackedCity
from config import DATABASE_URL, TRACKED_CITIES
from weather_api import ingest_one, get_latest

# Database setup
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def add_city(city):
    session = Session()
    try:
        if city not in TRACKED_CITIES:
            st.error(f"❌ {city} not supported")
            return
        session.add(TrackedCity(city=city))
        session.commit()
        st.success(f"✅ Added {city}")
    except:
        st.error(f"❌ Failed to add {city}")
    finally:
        session.close()

def remove_city(city):
    session = Session()
    try:
        city_obj = session.query(TrackedCity).filter_by(city=city).first()
        if city_obj:
            session.delete(city_obj)
            session.commit()
            st.success(f"✅ Removed {city}")
    finally:
        session.close()

def get_tracked_cities():
    session = Session()
    try:
        return [city[0] for city in session.query(TrackedCity.city).all()]
    finally:
        session.close()

def get_weather_data(city=None, limit=20):
    session = Session()
    try:
        query = session.query(WeatherData).order_by(WeatherData.timestamp.desc())
        if city:
            query = query.filter(WeatherData.city == city)
        data = query.limit(limit).all()
        return pd.DataFrame([(d.city, d.temperature, d.timestamp) for d in data], 
                          columns=['City', 'Temperature (°C)', 'Timestamp'])
    finally:
        session.close()

def fetch_data(city):
    if city in TRACKED_CITIES:
        lat, lon = TRACKED_CITIES[city]["lat"], TRACKED_CITIES[city]["lon"]
        return ingest_one(city, lat, lon)
    return 0

# Main App
st.title("🌤️ Weather Data Tracker")

# City Management
tracked_cities = get_tracked_cities()
col1, col2 = st.columns(2)

with col1:
    st.subheader("➕ Add City")
    untracked = [city for city in TRACKED_CITIES.keys() if city not in tracked_cities]
    if untracked:
        new_city = st.selectbox("Select city", untracked)
        if st.button("Add City"):
            add_city(new_city)
            st.rerun()

with col2:
    st.subheader("➖ Remove City")
    if tracked_cities:
        city_to_remove = st.selectbox("Select city", tracked_cities)
        if st.button("Remove City"):
            remove_city(city_to_remove)
            st.rerun()

# Status Overview
st.subheader("📊 Current Status")
if tracked_cities:
    status_data = []
    for city in tracked_cities:
        latest = get_latest(city)
        if latest:
            _, temp, timestamp = latest
            status_data.append({
                'City': city,
                'Temp (°C)': f"{temp:.1f}",
                'Updated': timestamp.strftime("%m-%d %H:%M")
            })
        else:
            status_data.append({'City': city, 'Temp (°C)': 'No data', 'Updated': 'No data'})
    
    st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True)
    
    if st.button("🔄 Refresh All Data"):
        total = sum(fetch_data(city) for city in tracked_cities)
        st.success(f"✅ Fetched {total} new records!")
        st.rerun()

# Weather Data Display
st.subheader("🌡️ Recent Weather Data")
col1, col2 = st.columns(2)

with col1:
    session = Session()
    unique_cities = [city[0] for city in session.query(WeatherData.city).distinct().all()]
    session.close()
    selected_city = st.selectbox("Filter by city", ["All Cities"] + unique_cities)

with col2:
    limit = st.selectbox("Show records", [10, 20, 50], index=1)

city_filter = selected_city if selected_city != "All Cities" else None
weather_data = get_weather_data(city=city_filter, limit=limit)

if not weather_data.empty:
    st.dataframe(weather_data, use_container_width=True, hide_index=True)
    
    # Simple temperature chart
    if len(weather_data) > 1:
        st.subheader("📈 Temperature Trend")
        for city in weather_data['City'].unique():
            city_data = weather_data[weather_data['City'] == city]
            if len(city_data) > 1:
                chart_data = city_data.set_index('Timestamp')['Temperature (°C)'].sort_index()
                st.line_chart(chart_data, height=200)
else:
    st.info("No weather data found. Add cities and refresh data to get started!")