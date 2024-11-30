import requests
from geopy.distance import geodesic, distance
from geopy.point import Point
from faker import Faker
import random
import math
import time
from nltk.corpus import wordnet as wn

# Get a list of adjectives from WordNet
adjectives = list(set([word.name().split('.')[0] for word in wn.all_synsets('a')]))

# Initialize Faker
fake = Faker()

# Constants
DAILY_DISTANCE_RANGE = (5, 9)  # Miles per day
API_SLEEP_TIME = 0  # Seconds to wait between API calls to respect rate limits
ARRIVAL_THRESHOLD = 0.2  # miles

# User-Agent for API requests
USER_AGENT = 'LongWalkScript/1.0 (savetz@gmail.com)'

# Start and Destination Place Names
start_place_name = 'Caribou, Maine'
end_place_name = 'Bend, Oregon'

# Generate a name for the walker
walker_name = fake.first_name_male()

# Debug flag for optional output
DEBUG = False  # Set to True to include debug information

# Compass bearings mapping
COMPASS_BEARINGS = {
    'north': 0,
    'north-northeast': 22.5,
    'northeast': 45,
    'east-northeast': 67.5,
    'east': 90,
    'east-southeast': 112.5,
    'southeast': 135,
    'south-southeast': 157.5,
    'south': 180,
    'south-southwest': 202.5,
    'southwest': 225,
    'west-southwest': 247.5,
    'west': 270,
    'west-northwest': 292.5,
    'northwest': 315,
    'north-northwest': 337.5
}

def get_location_name(lat, lon):
    """
    Uses Nominatim reverse geocoding to get the location name.
    """
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {
        'format': 'jsonv2',
        'lat': lat,
        'lon': lon
    }
    headers = {
        'User-Agent': USER_AGENT
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        address = data.get('address', {})
        location_name = (
            address.get('city') or
            address.get('town') or
            address.get('village') or
            address.get('hamlet') or
            address.get('county') or
            'an unknown place'
        )
        return location_name
    except requests.exceptions.RequestException as e:
        print(f"Error fetching location name at ({lat}, {lon}): {e}")
        return 'an unknown place'

def get_coordinates(place_name):
    """
    Gets the latitude and longitude for a given place name using Nominatim's search API.
    """
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'format': 'jsonv2',
        'q': place_name,
        'limit': 1
    }
    headers = {
        'User-Agent': USER_AGENT
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return (lat, lon)
        else:
            print(f"No coordinates found for '{place_name}'.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates for '{place_name}': {e}")
        return None

def calculate_bearing(start_lat, start_lon, end_lat, end_lon):
    """
    Calculates the bearing between two points.
    """
    lat1 = math.radians(start_lat)
    lat2 = math.radians(end_lat)
    diff_long = math.radians(end_lon - start_lon)

    x = math.sin(diff_long) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2) -
         (math.sin(lat1) * math.cos(lat2) * math.cos(diff_long)))
    initial_bearing = math.atan2(x, y)

    # Normalize the bearing
    initial_bearing = (math.degrees(initial_bearing) + 360) % 360
    return initial_bearing
    
def bearing_to_compass(bearing):
    """
    Converts a bearing in degrees to a compass direction.
    """
    compass_sectors = [
        'north', 'north-northeast', 'northeast', 'east-northeast',
        'east', 'east-southeast', 'southeast', 'south-southeast',
        'south', 'south-southwest', 'southwest', 'west-southwest',
        'west', 'west-northwest', 'northwest', 'north-northwest'
    ]
    sector_size = 360 / len(compass_sectors)
    sector_index = int((bearing + sector_size / 2) % 360 / sector_size)
    return compass_sectors[sector_index]
    
def calculate_next_point(current_point, bearing, daily_distance):
    """
    Calculates the next point given the current point, bearing, and distance.
    """
    origin = Point(current_point)
    destination = distance(miles=daily_distance).destination(origin, bearing)
    return (destination.latitude, destination.longitude)
    
def fix_occupation(occupation):
    """
    Fixes the occupation string if it contains a comma.
    Converts 'specific, general' format to 'general specific'.
    """
    if ',' in occupation:
        parts = occupation.split(',')
        parts = [part.strip() for part in parts]
        # Swap the parts and join them
        occupation = ' '.join(parts[::-1])
    return occupation

    
def generate_introspection(day):
    """
    Generates an introspective thought, occasionally mentioning the walker's name.
    """
    thoughts = [
        "He reflects on the distance he's covered and the journey ahead.",
        "The road behind him feels both distant and immediate.",
        "Memories of past conversations linger in his mind.",
        "He ponders the purpose of his journey.",
        "The changing landscapes mirror his shifting thoughts.",
        "Silence accompanies him, yet his mind is loud with contemplation.",
        "Each step feels heavier than the last, but he presses on.",
        "He wonders if the destination will bring the closure he seeks.",
        "The vastness of the world makes him feel both insignificant and empowered.",
        f"{walker_name} recalls the promise he made that set him on this path."
    ]
    # Occasionally include the walker's name
    if day % 5 == 0:
        thought = random.choice(thoughts[-2:])
    else:
        thought = random.choice(thoughts[:-2])
    return thought

def generate_weather():
    """
    Simulates weather conditions.
    """
    weather_conditions = [
        "The sun beats down relentlessly.",
        "A gentle breeze makes the journey pleasant.",
        "Clouds gather, hinting at rain.",
        "A light drizzle accompanies him.",
        "A storm forces him to seek shelter temporarily.",
        "The crisp air invigorates his steps.",
        "Fog envelops the path ahead, obscuring his view.",
        "Snowflakes begin to fall, covering the ground in white.",
        "The humidity makes each step more taxing.",
        "A rainbow appears after a brief shower."
    ]
    return random.choice(weather_conditions)
    
def generate_local_interaction(distance_remaining, total_distance, current_coords, end_coords, destination_name):
    """
    Generates a local character and their response.
    """
    percentage_remaining = (distance_remaining / total_distance) * 100

    # Calculate correct bearing
    correct_bearing = calculate_bearing(
        current_coords[0], current_coords[1],
        end_coords[0], end_coords[1]
    )
    correct_direction = bearing_to_compass(correct_bearing)

    # Determine locals' accuracy
    if percentage_remaining > 75:
        # High chance of incorrect direction
        accuracy = 0.3
        points = [
            'looks confused, pointing',"doesn't seem to understand but points toward",
            'tilts their head to the','vaguely points' 
        ]

    elif percentage_remaining > 50:
        accuracy = 0.5
        points = [
            'shrugs and motions to the','looks off to the','waves sort of to the '
        ]
    elif percentage_remaining > 25:
        accuracy = 0.65
        points = [
            'looks unsure but points','motions towards the','smiles and gestures'
        ]
    else:
        accuracy = 0.9
        points = [
            'self-assuredly points','directs him to the'
        ]

    if random.random() < accuracy:
        # Local gives correct direction
        direction = correct_direction
        is_correct = True
    else:
        # Local gives random incorrect direction
        possible_directions = list(COMPASS_BEARINGS.keys())
        possible_directions.remove(correct_direction)
        direction = random.choice(possible_directions)
        is_correct = False

    # Generate local character
    name = fake.first_name()
    occupation = fix_occupation(fake.job())
    # Expanded demeanors list
    demeanor = random.choice(adjectives)
    point = random.choice(points)
    
    if demeanor[0].lower() in "aeiou":
        article = "an"
    else:
        article = "a"

    # Destination reference phrases
    destination_phrases = [
        destination_name,
        'his destination',
        'the place he seeks',
        'where he is headed',
        'the city ahead',
        'the place he longs to reach'
    ]
    destination_reference = random.choice(destination_phrases)

    # Compose interaction
    interaction = (
        f"He asks a local {occupation.lower()}, {article} {demeanor} person named {name}, "
        f"which way to {destination_reference}. The {occupation.lower()} {point} {direction}."
    )

    if DEBUG:
        interaction += f" [Correct direction: {correct_direction}]"

    return interaction, direction, is_correct
    
# Function to query the local LLM
def query_gpt(prompt, api_key, model="gpt-4-turbo"):
    """
    Queries the local LLM for a response based on the given prompt.
    """
    url = "http://localhost:1234/v1/completions".format(model)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    json_data = {
        "prompt": prompt,
        "max_tokens": 200
    }

    try:
        response = requests.post(url, headers=headers, json=json_data, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("text", "").strip()
    except requests.exceptions.Timeout:
        print("LLM query timed out. Returning fallback text.")
        return "The details of the location remain a mystery."
    except requests.RequestException as e:
        print(f"Error querying the LLM: {e}")
        return "Unable to retrieve additional details about this place."
        
def compose_daily_entry(day, location_name, interaction, distance_covered, introspection, weather, rest_day=False, api_key=None):
    """
    Creates the narrative for the day, including introspection and weather.
    Uses the local LLM to enhance the narrative with location-specific descriptions.
    """
    if rest_day:
        entry = (
            f"Day {day}:\n"
            f"{weather} {walker_name} decides to rest in {location_name}.\n"
            f"{introspection}\n"
            f"Distance covered today: 0 miles.\n"
        )
    else:
        # Use LLM to generate location description
        location_description = ""
        if api_key:
            prompt = f"Write a maximum of 25 words about how a walking traveler might feel about visiting {location_name} for the first time. Write in third perosn, referring to the walker as {walker_name} or he. Write no other commentary about this task. Do not describe your thought process or steps."
            location_description = query_gpt(prompt, api_key)
        
        entry = (
            f"Day {day}:\n"
            f"{weather} {walker_name} arrives in {location_name}. "
            f"{interaction}\n\n"
            f"{location_description}"
            f"{introspection}\n"
            f"Distance covered today: {distance_covered:.2f} miles.\n"
        )
    return entry
    
def write_conclusion(novel_file, day_count, destination_name):
    """
    Writes the final entry when the walker reaches the destination, the last Blockbuster store.
    """
    conclusion = (
        f"Day {day_count}:\n"
        f"{walker_name} finally arrives at his destination: the last Blockbuster store in {destination_name}.\n"
        f"He stands outside the iconic blue and yellow sign, feeling the weight of the journey lift from his shoulders.\n"
        f"From his pocket, he pulls out a weathered videotape—its label faded but still legible. With a sense of ceremony, "
        f"he walks to the return bin and drops the tape inside. The soft clink of the tape hitting the metal feels like "
        f"the final note in a long, unfinished symphony.\n"
        f"For a moment, he lingers. "
        f"With a deep breath, he turns around and begins the long walk home.\n"
    )
    novel_file.write(conclusion + '\n')

def main():
    # Example API key for the local LLM
    api_key = ""  # put anything here to use the LLM

    try:
        # Get coordinates for start and end locations
        start_coords = get_coordinates(start_place_name)
        end_coords = get_coordinates(end_place_name)

        if not start_coords or not end_coords:
            print("Error: Could not retrieve coordinates for the specified locations.")
            return

        # Initialize variables
        current_coords = start_coords
        day_count = 1
        total_distance = geodesic(start_coords, end_coords).miles
        distance_remaining = total_distance
        last_rest_day = 0  # To track when the last rest day occurred
        days_without_progress = 0 

        print(f"Total distance to cover: {total_distance:.2f} miles.")

        # Open a file to write the novel
        with open('long_walk_novel.txt', 'w', encoding='utf-8') as novel_file:
            while distance_remaining > ARRIVAL_THRESHOLD:
                print(f"Starting Day {day_count} with {distance_remaining:.2f} miles remaining.")

                # Decide if today is a rest day
                rest_day = False
                days_since_last_rest = day_count - last_rest_day
                if day_count > 7 and days_since_last_rest >= 7:
                    if random.random() < 0.1:  # 10% chance of rest day
                        rest_day = True
                        last_rest_day = day_count

                if rest_day:
                    print(f"Day {day_count} is a rest day.")
                    # Get current location name
                    location_name = get_location_name(*current_coords)
                    # Generate introspection and weather
                    introspection = generate_introspection(day_count)
                    weather = generate_weather()
                    # Compose daily entry
                    rest_entry = compose_daily_entry(
                        day_count, location_name, '', 0, introspection, weather, rest_day=True, api_key=api_key
                    )
                    # Write entry to the novel
                    novel_file.write(rest_entry + '\n')
                else:
                    # Save previous distance
                    previous_distance = distance_remaining

                    # Calculate daily walking distance
                    daily_distance = random.uniform(*DAILY_DISTANCE_RANGE)

                    # Generate local interaction and get the direction provided
                    interaction, direction_given, is_correct_direction = generate_local_interaction(
                        distance_remaining, total_distance, current_coords, end_coords, end_place_name
                    )

                    # Adjust daily_distance if close to the destination and moving correctly
                    if distance_remaining <= daily_distance and is_correct_direction:
                        daily_distance = distance_remaining

                    # Convert the direction given by the local to a bearing
                    bearing = COMPASS_BEARINGS[direction_given]

                    # Calculate next point based on the bearing from the local's direction
                    next_coords = calculate_next_point(current_coords, bearing, daily_distance)

                    # Get location name
                    location_name = get_location_name(*next_coords)

                    # Generate introspection and weather
                    introspection = generate_introspection(day_count)
                    weather = generate_weather()

                    # Compose daily entry
                    daily_entry = compose_daily_entry(
                        day_count, location_name, interaction,
                        daily_distance, introspection, weather, api_key=api_key
                    )

                    # Write entry to the novel
                    novel_file.write(daily_entry + '\n')

                    # Update variables for next iteration
                    current_coords = next_coords

                    # Recalculate the distance remaining based on the new position
                    distance_remaining = geodesic(current_coords, end_coords).miles

                    # Update days_without_progress counter
                    if distance_remaining >= previous_distance:
                        days_without_progress += 1
                    else:
                        days_without_progress = 0  # Reset if progress is made

                print(f"Day {day_count} walking {daily_distance:.2f} miles.")
                print(f"Distance remaining after Day {day_count}: {distance_remaining:.2f} miles.")

                # Update day count
                day_count += 1

                # Respect API rate limits
                time.sleep(API_SLEEP_TIME)

            # Write the conclusion once the journey is complete
            write_conclusion(novel_file, day_count, end_place_name)

        print("Novel generation complete.")

        # Count the number of words in the novel
        with open('long_walk_novel.txt', 'r', encoding='utf-8') as novel_file:
            content = novel_file.read()
            word_count = len(content.split())
            print(f"The novel contains {word_count} words.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()