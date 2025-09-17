#!/usr/bin/env python3
"""
METAR Reader - Aviation Weather Report Decoder

A Flask web application that fetches and decodes METAR (Meteorological Aerodrome Report)
weather data from airports worldwide. METAR reports are standardized aviation weather
reports that contain cryptic codes. This application converts them into human-readable format.

Author: Claude Code
License: MIT
"""

import requests
import re
from flask import Flask, render_template, request, jsonify
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)

class MetarDecoder:
    """
    A comprehensive METAR decoder that converts aviation weather reports into structured data.

    METAR (Meteorological Aerodrome Report) is a format for reporting weather information.
    A METAR weather report is predominantly used by aircraft pilots, and by meteorologists,
    who use aggregated METAR information to assist in weather forecasting.
    """

    def __init__(self):
        """Initialize the decoder with wind direction mappings."""
        # Mapping of compass directions from abbreviated to full names
        self.wind_directions = {
            'N': 'North', 'NNE': 'North-northeast', 'NE': 'Northeast',
            'ENE': 'East-northeast', 'E': 'East', 'ESE': 'East-southeast',
            'SE': 'Southeast', 'SSE': 'South-southeast', 'S': 'South',
            'SSW': 'South-southwest', 'SW': 'Southwest', 'WSW': 'West-southwest',
            'W': 'West', 'WNW': 'West-northwest', 'NW': 'Northwest', 'NNW': 'North-northwest'
        }

    def degrees_to_direction(self, degrees):
        """
        Convert wind direction from degrees to compass direction text.

        Args:
            degrees (int or None): Wind direction in degrees (0-360)

        Returns:
            str: Human-readable compass direction (e.g., "North", "Southwest")
        """
        if degrees is None:
            return "variable"

        # 16-point compass rose for precise direction mapping
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

        # Convert degrees to compass index (each direction covers 22.5 degrees)
        index = round(degrees / 22.5) % 16
        return self.wind_directions.get(directions[index], directions[index])

    def decode_visibility(self, visibility):
        """
        Convert numerical visibility to human-readable format.

        Args:
            visibility (float): Visibility distance in statute miles

        Returns:
            str: Formatted visibility description
        """
        if visibility >= 10:
            return "10+ miles"
        elif visibility >= 1:
            return f"{visibility} miles"
        else:
            return f"{visibility} mile"

    def decode_sky_condition(self, condition):
        """
        Decode METAR sky condition codes to readable descriptions.

        Args:
            condition (str): METAR sky condition code (CLR, SCT, BKN, etc.)

        Returns:
            str: Human-readable sky condition description
        """
        # METAR sky condition codes and their meanings
        sky_conditions = {
            'CLR': 'Clear skies',      # No clouds below 12,000 feet
            'SKC': 'Sky clear',        # No clouds or obscuring phenomena
            'FEW': 'Few clouds',       # 1/8 to 2/8 sky coverage
            'SCT': 'Scattered clouds', # 3/8 to 4/8 sky coverage
            'BKN': 'Broken clouds',    # 5/8 to 7/8 sky coverage
            'OVC': 'Overcast'          # 8/8 sky coverage
        }
        return sky_conditions.get(condition[:3], condition)

    def decode_weather_phenomenon(self, phenomenon):
        """
        Decode METAR weather phenomenon codes into readable descriptions.

        Weather phenomena in METAR reports can include intensity modifiers,
        descriptors, and precipitation/obscuration types.

        Args:
            phenomenon (str): METAR weather code (e.g., "-RA", "+TSRA", "FG")

        Returns:
            str: Human-readable weather description
        """
        # Intensity indicators
        intensity = {'-': 'Light ', '+': 'Heavy ', '': ''}

        # Weather descriptors
        descriptor = {
            'MI': 'Shallow ', 'PR': 'Partial ', 'BC': 'Patches of ', 'DR': 'Drifting ',
            'BL': 'Blowing ', 'SH': 'Showers of ', 'TS': 'Thunderstorms with ', 'FZ': 'Freezing '
        }

        # Precipitation types
        precipitation = {
            'DZ': 'drizzle', 'RA': 'rain', 'SN': 'snow', 'SG': 'snow grains',
            'IC': 'ice crystals', 'PL': 'ice pellets', 'GR': 'hail', 'GS': 'small hail'
        }

        # Obscuration types
        obscuration = {
            'BR': 'mist', 'FG': 'fog', 'FU': 'smoke', 'VA': 'volcanic ash',
            'DU': 'dust', 'SA': 'sand', 'HZ': 'haze', 'PY': 'spray'
        }

        result = ""
        i = 0

        # Parse intensity indicator (if present)
        if i < len(phenomenon) and phenomenon[i] in ['-', '+']:
            result += intensity[phenomenon[i]]
            i += 1

        # Parse weather codes in sequence
        while i < len(phenomenon):
            code = phenomenon[i:i+2]
            if code in descriptor:
                result += descriptor[code]
                i += 2
            elif code in precipitation:
                result += precipitation[code]
                i += 2
            elif code in obscuration:
                result += obscuration[code]
                i += 2
            else:
                i += 1

        return result or phenomenon

    def celsius_to_fahrenheit(self, celsius):
        """
        Convert temperature from Celsius to Fahrenheit.

        Args:
            celsius (float): Temperature in Celsius

        Returns:
            int: Temperature in Fahrenheit, rounded to nearest integer
        """
        return round((celsius * 9/5) + 32)

    def decode_metar(self, metar_text):
        """
        Parse and decode a complete METAR weather report.

        This is the main method that processes a raw METAR string and extracts
        all weather information into a structured dictionary format.

        Args:
            metar_text (str): Raw METAR weather report string

        Returns:
            dict: Structured weather data with the following keys:
                - wind: Wind speed, direction, and gusts
                - visibility: Visibility distance
                - temperature: Temperature in Celsius and Fahrenheit
                - dewpoint: Dewpoint in Celsius and Fahrenheit
                - sky_conditions: Cloud coverage and heights
                - weather_phenomena: Current weather conditions
                - pressure: Barometric pressure
                - time: Observation time
        """
        if not metar_text:
            return {"error": "No METAR data available"}

        # Split METAR into individual components
        parts = metar_text.split()

        # Initialize result structure with all possible weather elements
        result = {
            "wind": None,
            "visibility": None,
            "temperature": None,
            "dewpoint": None,
            "sky_conditions": [],
            "weather_phenomena": [],
            "pressure": None,
            "time": None
        }

        # Process each component of the METAR report
        for i, part in enumerate(parts):
            # Extract observation time (format: DDHHmmZ)
            time_match = re.match(r'(\d{6})Z', part)
            if time_match:
                time_str = time_match.group(1)
                day = time_str[:2]    # Day of month
                hour = time_str[2:4]  # Hour (UTC)
                minute = time_str[4:6] # Minute
                result["time"] = f"{day}th at {hour}:{minute} UTC"
                continue

            # Extract wind information (format: DDDSSGggKT)
            # DDD = direction in degrees, SS = speed, Ggg = gust speed, KT = knots
            wind_match = re.match(r'(\d{3}|VRB)(\d{2,3})(G\d{2,3})?KT', part)
            if wind_match:
                direction = wind_match.group(1)  # Wind direction or "VRB" for variable
                speed = int(wind_match.group(2))  # Wind speed in knots
                gust = wind_match.group(3)        # Gust speed (optional)

                if speed == 0:
                    result["wind"] = {
                        "description": "Calm",
                        "speed": 0,
                        "direction": None,
                        "gust": None
                    }
                else:
                    wind_direction = None if direction == 'VRB' else int(direction)
                    dir_text = self.degrees_to_direction(wind_direction)

                    result["wind"] = {
                        "description": f"From the {dir_text.lower()}",
                        "speed": speed,
                        "direction": dir_text,
                        "gust": int(gust[1:]) if gust else None
                    }

            # Extract visibility (format: VVVVSM where VVVV is visibility in statute miles)
            if re.match(r'\d+SM', part):
                vis_num = re.findall(r'\d+', part)[0]
                visibility = int(vis_num)
                result["visibility"] = {
                    "value": visibility,
                    "description": self.decode_visibility(visibility)
                }
            # Handle fractional visibility (e.g., "3/4SM")
            elif re.match(r'\d+/\d+SM', part):
                fraction = part.replace('SM', '')
                num, denom = map(int, fraction.split('/'))
                visibility = num / denom
                result["visibility"] = {
                    "value": visibility,
                    "description": self.decode_visibility(visibility)
                }

            # Extract temperature and dewpoint (format: TT/DD where M indicates below zero)
            if re.match(r'M?\d{2}/M?\d{2}', part):
                temp_dew = part.split('/')
                temp_str = temp_dew[0]  # Temperature string
                dew_str = temp_dew[1]   # Dewpoint string

                # Handle negative temperatures (prefix M indicates minus)
                temp_c = -int(temp_str[1:]) if temp_str.startswith('M') else int(temp_str)
                dew_c = -int(dew_str[1:]) if dew_str.startswith('M') else int(dew_str)

                result["temperature"] = {
                    "celsius": temp_c,
                    "fahrenheit": self.celsius_to_fahrenheit(temp_c)
                }
                result["dewpoint"] = {
                    "celsius": dew_c,
                    "fahrenheit": self.celsius_to_fahrenheit(dew_c)
                }

            # Extract sky conditions (format: CCCHHH where CCC is condition, HHH is height)
            sky_match = re.match(r'(CLR|SKC|FEW|SCT|BKN|OVC)(\d{3})?', part)
            if sky_match:
                condition = sky_match.group(1)  # Cloud condition code
                height = sky_match.group(2)     # Cloud height in hundreds of feet

                sky_data = {
                    "condition": condition,
                    "description": self.decode_sky_condition(condition),
                    "height": int(height) * 100 if height else None
                }
                result["sky_conditions"].append(sky_data)

            # Extract weather phenomena (rain, snow, fog, etc.)
            weather_match = re.match(r'[-+]?[A-Z]{2,}', part)
            if weather_match and part not in ['AUTO', 'COR', 'RMK']:
                # Exclude wind data and airport codes from weather phenomena
                if not re.match(r'\d{3}\d{2,3}', part) and not re.match(r'[A-Z]\d{4}', part):
                    result["weather_phenomena"].append({
                        "code": part,
                        "description": self.decode_weather_phenomenon(part)
                    })

            # Extract barometric pressure (format: APPPP where PPPP is pressure in hundredths of inches Hg)
            pressure_match = re.match(r'A(\d{4})', part)
            if pressure_match:
                pressure_raw = pressure_match.group(1)
                pressure_inhg = float(pressure_raw) / 100  # Convert to inches of mercury
                result["pressure"] = {
                    "inches_hg": pressure_inhg,
                    "description": f"{pressure_inhg:.2f} inches Hg"
                }

        return result

def fetch_metar(airport_code):
    """
    Fetch METAR weather data from the Aviation Weather Center API.

    This function retrieves current weather observations for a given airport
    using the FAA's Aviation Weather Center public API.

    Args:
        airport_code (str): 4-letter ICAO airport code (e.g., "KJFK", "EGLL")

    Returns:
        tuple: (metar_data, error_message)
            - metar_data (str): Raw METAR string if successful, None if error
            - error_message (str): Error description if failed, None if successful
    """
    try:
        # Aviation Weather Center METAR API endpoint
        url = f"https://aviationweather.gov/api/data/metar?ids={airport_code.upper()}"

        # Make HTTP request with timeout to prevent hanging
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Extract and validate response data
        metar_data = response.text.strip()
        if not metar_data:
            return None, "No METAR data found for this airport code"

        return metar_data, None
    except requests.RequestException as e:
        return None, f"Error fetching METAR data: {str(e)}"

# Flask Routes

@app.route('/')
def index():
    """
    Serve the main application page.

    Returns:
        str: Rendered HTML template for the main interface
    """
    return render_template('index.html')

@app.route('/get_metar', methods=['POST'])
def get_metar():
    """
    API endpoint to fetch and decode METAR data for a given airport.

    Accepts POST requests with airport code and returns both raw and
    decoded weather information in JSON format.

    Form Parameters:
        airport_code (str): 4-letter ICAO airport identifier

    Returns:
        JSON response containing:
            - airport_code: The requested airport code
            - raw_metar: Original METAR string from weather service
            - decoded_data: Structured weather information
            - error: Error message if request failed
    """
    # Extract and validate airport code from form data
    airport_code = request.form.get('airport_code', '').strip().upper()

    # Validate input
    if not airport_code:
        return jsonify({'error': 'Please enter an airport code'})

    if len(airport_code) != 4:
        return jsonify({'error': 'Airport code must be 4 characters (e.g., KTIG)'})

    # Fetch raw METAR data from weather service
    metar_raw, error = fetch_metar(airport_code)

    if error:
        return jsonify({'error': error})

    # Decode the METAR data into structured format
    decoder = MetarDecoder()
    decoded_data = decoder.decode_metar(metar_raw)

    # Return structured response
    return jsonify({
        'airport_code': airport_code,
        'raw_metar': metar_raw,
        'decoded_data': decoded_data
    })

# Application Entry Point

if __name__ == '__main__':
    """
    Run the Flask application in development mode.

    Note: In production, use a proper WSGI server like Gunicorn or uWSGI
    instead of the built-in development server.
    """
    app.run(debug=True, host='127.0.0.1', port=5000)