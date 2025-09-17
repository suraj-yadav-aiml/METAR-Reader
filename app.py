import requests
import re
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

class MetarDecoder:
    def __init__(self):
        self.wind_directions = {
            'N': 'North', 'NNE': 'North-northeast', 'NE': 'Northeast',
            'ENE': 'East-northeast', 'E': 'East', 'ESE': 'East-southeast',
            'SE': 'Southeast', 'SSE': 'South-southeast', 'S': 'South',
            'SSW': 'South-southwest', 'SW': 'Southwest', 'WSW': 'West-southwest',
            'W': 'West', 'WNW': 'West-northwest', 'NW': 'Northwest', 'NNW': 'North-northwest'
        }

    def degrees_to_direction(self, degrees):
        if degrees is None:
            return "variable"
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return self.wind_directions.get(directions[index], directions[index])

    def decode_visibility(self, visibility):
        if visibility >= 10:
            return "10+ miles"
        elif visibility >= 1:
            return f"{visibility} miles"
        else:
            return f"{visibility} mile"

    def decode_sky_condition(self, condition):
        sky_conditions = {
            'CLR': 'Clear skies',
            'SKC': 'Sky clear',
            'FEW': 'Few clouds',
            'SCT': 'Scattered clouds',
            'BKN': 'Broken clouds',
            'OVC': 'Overcast'
        }
        return sky_conditions.get(condition[:3], condition)

    def decode_weather_phenomenon(self, phenomenon):
        intensity = {'-': 'Light ', '+': 'Heavy ', '': ''}
        descriptor = {
            'MI': 'Shallow ', 'PR': 'Partial ', 'BC': 'Patches of ', 'DR': 'Drifting ',
            'BL': 'Blowing ', 'SH': 'Showers of ', 'TS': 'Thunderstorms with ', 'FZ': 'Freezing '
        }
        precipitation = {
            'DZ': 'drizzle', 'RA': 'rain', 'SN': 'snow', 'SG': 'snow grains',
            'IC': 'ice crystals', 'PL': 'ice pellets', 'GR': 'hail', 'GS': 'small hail'
        }
        obscuration = {
            'BR': 'mist', 'FG': 'fog', 'FU': 'smoke', 'VA': 'volcanic ash',
            'DU': 'dust', 'SA': 'sand', 'HZ': 'haze', 'PY': 'spray'
        }

        result = ""
        i = 0

        if i < len(phenomenon) and phenomenon[i] in ['-', '+']:
            result += intensity[phenomenon[i]]
            i += 1

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
        return round((celsius * 9/5) + 32)

    def decode_metar(self, metar_text):
        if not metar_text:
            return {"error": "No METAR data available"}

        parts = metar_text.split()

        # Initialize result structure
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

        for i, part in enumerate(parts):
            # Time extraction
            time_match = re.match(r'(\d{6})Z', part)
            if time_match:
                time_str = time_match.group(1)
                day = time_str[:2]
                hour = time_str[2:4]
                minute = time_str[4:6]
                result["time"] = f"{day}th at {hour}:{minute} UTC"
                continue

            # Wind information
            wind_match = re.match(r'(\d{3}|VRB)(\d{2,3})(G\d{2,3})?KT', part)
            if wind_match:
                direction = wind_match.group(1)
                speed = int(wind_match.group(2))
                gust = wind_match.group(3)

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

            # Visibility
            if re.match(r'\d+SM', part):
                vis_num = re.findall(r'\d+', part)[0]
                visibility = int(vis_num)
                result["visibility"] = {
                    "value": visibility,
                    "description": self.decode_visibility(visibility)
                }
            elif re.match(r'\d+/\d+SM', part):
                fraction = part.replace('SM', '')
                num, denom = map(int, fraction.split('/'))
                visibility = num / denom
                result["visibility"] = {
                    "value": visibility,
                    "description": self.decode_visibility(visibility)
                }

            # Temperature and Dewpoint
            if re.match(r'M?\d{2}/M?\d{2}', part):
                temp_dew = part.split('/')
                temp_str = temp_dew[0]
                dew_str = temp_dew[1]

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

            # Sky conditions
            sky_match = re.match(r'(CLR|SKC|FEW|SCT|BKN|OVC)(\d{3})?', part)
            if sky_match:
                condition = sky_match.group(1)
                height = sky_match.group(2)

                sky_data = {
                    "condition": condition,
                    "description": self.decode_sky_condition(condition),
                    "height": int(height) * 100 if height else None
                }
                result["sky_conditions"].append(sky_data)

            # Weather phenomena
            weather_match = re.match(r'[-+]?[A-Z]{2,}', part)
            if weather_match and part not in ['AUTO', 'COR', 'RMK']:
                if not re.match(r'\d{3}\d{2,3}', part) and not re.match(r'[A-Z]\d{4}', part):
                    result["weather_phenomena"].append({
                        "code": part,
                        "description": self.decode_weather_phenomenon(part)
                    })

            # Pressure (altimeter setting)
            pressure_match = re.match(r'A(\d{4})', part)
            if pressure_match:
                pressure_raw = pressure_match.group(1)
                pressure_inhg = float(pressure_raw) / 100
                result["pressure"] = {
                    "inches_hg": pressure_inhg,
                    "description": f"{pressure_inhg:.2f} inches Hg"
                }

        return result

def fetch_metar(airport_code):
    try:
        url = f"https://aviationweather.gov/api/data/metar?ids={airport_code.upper()}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        metar_data = response.text.strip()
        if not metar_data:
            return None, "No METAR data found for this airport code"

        return metar_data, None
    except requests.RequestException as e:
        return None, f"Error fetching METAR data: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_metar', methods=['POST'])
def get_metar():
    airport_code = request.form.get('airport_code', '').strip().upper()

    if not airport_code:
        return jsonify({'error': 'Please enter an airport code'})

    if len(airport_code) != 4:
        return jsonify({'error': 'Airport code must be 4 characters (e.g., KTIG)'})

    metar_raw, error = fetch_metar(airport_code)

    if error:
        return jsonify({'error': error})

    decoder = MetarDecoder()
    decoded_data = decoder.decode_metar(metar_raw)

    return jsonify({
        'airport_code': airport_code,
        'raw_metar': metar_raw,
        'decoded_data': decoded_data
    })

if __name__ == '__main__':
    app.run(debug=True)