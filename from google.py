import streamlit as st
import folium
from geopy.geocoders import Nominatim
from html2image import Html2Image
import requests
import os
import time
from google.transit import gtfs_realtime_pb2
from dotenv import load_dotenv
import cv2

# Load environment variables from .env file
load_dotenv()

# API key from .env
API_KEY = os.getenv("API_KEY")

# Ensure the required directories exist
html_dir = "htmlfiles"
image_dir = "images_directory"
if not os.path.exists(html_dir):
    os.makedirs(html_dir)
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Streamlit application to display real-time bus map
def get_map(current_time):
    # Assuming you have a valid URL for fetching vehicle positions
    feed = gtfs_realtime_pb2.FeedMessage()
    k = f"https://opendata.iiitd.edu.in/api/realtime/VehiclePositions.pb?key={API_KEY}"
    response = requests.get(k)
    feed.ParseFromString(response.content)

    from google.protobuf.json_format import MessageToJson
    json_string = MessageToJson(feed)
    d = eval(json_string)
    l = []

    # Extract latitude and longitude for buses
    for i in d["entity"]:
        try:
            lat = i["vehicle"]["position"]["latitude"]
            lon = i["vehicle"]["position"]["longitude"]
            l.append([lat, lon])
        except KeyError:
            continue  # Skip invalid entries

    # Get the location of New Delhi
    geolocator = Nominatim(user_agent="location_details")
    location = geolocator.geocode("New Delhi")
    latitude = location.latitude
    longitude = location.longitude

    # Create a map centered around New Delhi
    m = folium.Map(location=[latitude, longitude], zoom_start=10)

    # Add markers to the map for each bus location
    for lat, lon in l:
        folium.CircleMarker(location=[lat, lon], radius=0.01, color='red', fill=True, fill_color='red', fill_opacity=1).add_to(m)

    map_filename = f"{html_dir}/map_{current_time}.html"
    m.save(map_filename)

# Convert HTML map to images
def convert_html_to_images():
    hti = Html2Image()
    cnt = 1

    for i in os.listdir(html_dir):
        html_file = os.path.join(html_dir, i)
        with open(html_file, "r") as f:
            html_str = f.read()
        hti.screenshot(html_str=html_str, save_as=f"{image_dir}/time_{cnt}.png")
        cnt += 1

# Convert images to video
def convert_images_to_video():
    image_files = sorted([f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))])

    if not image_files:
        print("No images found for video conversion.")
        return

    width, height = 1920, 1080
    fps = 28
    video_writer = cv2.VideoWriter('output_video.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    for image_file in image_files:
        image_path = os.path.join(image_dir, image_file)
        image = cv2.imread(image_path)
        image = cv2.resize(image, (width, height))
        video_writer.write(image)

    video_writer.release()

# Main loop that runs every 30 seconds
def main():
    while True:
        try:
            current_time = time.time()
            get_map(current_time)
            convert_html_to_images()
            convert_images_to_video()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(30)

if __name__ == "__main__":
    main()
