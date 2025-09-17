# METAR Reader

A modern web application that fetches and decodes METAR (Meteorological Aerodrome Report) weather data from airports worldwide. Transform cryptic aviation weather codes into beautiful, human-readable weather reports.

![METAR Reader Screenshot](https://img.shields.io/badge/Status-Live-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-2.3+-red) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Real-time Weather Data**: Fetches current METAR reports from FAA's Aviation Weather Center
- **Structured Display**: Organizes weather information into easy-to-read cards
- **Comprehensive Decoding**: Displays temperature, wind, visibility, pressure, and sky conditions
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Modern UI**: Clean, intuitive interface with hover effects and smooth animations
- **Fast Performance**: Lightweight application with efficient data processing
- **Developer Friendly**: Well-documented code with comprehensive comments

## Live Demo

Enter any 4-letter airport code (ICAO format) to see current weather conditions:

- **KJFK** - John F. Kennedy International Airport (New York)
- **EGLL** - Heathrow Airport (London)
- **KLAX** - Los Angeles International Airport
- **KTIG** - Martinsburg Regional Airport (West Virginia)

## Tech Stack

### Backend
- **Python 3.8+** - Core programming language
- **Flask 2.3+** - Lightweight web framework
- **Requests** - HTTP library for API calls
- **Regular Expressions** - METAR pattern matching

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with Grid and Flexbox
- **Vanilla JavaScript** - Interactive functionality
- **Responsive Design** - Mobile-first approach

### Data Source
- **Aviation Weather Center API** - Official FAA weather data
- **METAR Format** - Standardized aviation weather reports

### Development Tools
- **uv** - Fast Python package manager
- **Git** - Version control
- **Visual Studio Code** - Development environment

## Prerequisites

Before running this application, ensure you have:

- Python 3.8 or higher installed
- Internet connection (for fetching weather data)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation

### Option 1: Using uv (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/suraj-yadav-aiml/METAR-Reader.git
   cd metar-reader
   ```

2. **Install uv** (if not already installed)
   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Create virtual environment and install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   uv add flask requests
   ```

4. **Run the application**
   ```bash
   uv run python app.py
   ```

### Option 2: Using pip

1. **Clone the repository**
   ```bash
   git clone https://github.com/suraj-yadav-aiml/METAR-Reader.git
   cd metar-reader
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

##  Usage

1. **Start the application**
   - The server will start on `http://127.0.0.1:5000`
   - Open this URL in your web browser

2. **Enter an airport code**
   - Use 4-letter ICAO codes (e.g., KJFK, EGLL, KLAX)
   - Click "Get Weather Report" or press Enter

3. **View the weather data**
   - See organized weather information in individual cards
   - Each card shows different weather elements with icons
   - Click "View Raw METAR Data" to see the original report

##  Understanding METAR

METAR (Meteorological Aerodrome Report) is a standardized format for reporting weather information, primarily used in aviation. A typical METAR report includes:

- **Station Identifier**: 4-letter ICAO airport code
- **Time**: Day, hour, and minute of observation (UTC)
- **Wind**: Direction, speed, and gusts
- **Visibility**: Distance in statute miles
- **Weather**: Precipitation, obscuration, and other phenomena
- **Sky Condition**: Cloud coverage and heights
- **Temperature/Dewpoint**: In degrees Celsius
- **Pressure**: Barometric pressure in inches of mercury

### Example METAR Breakdown

```
METAR KJFK 161251Z 28008KT 10SM FEW250 22/13 A3012 RMK AO2 SLP201
```

- **KJFK**: John F. Kennedy International Airport
- **161251Z**: 16th day, 12:51 UTC
- **28008KT**: Wind from 280 at 8 knots
- **10SM**: Visibility 10 statute miles
- **FEW250**: Few clouds at 25,000 feet
- **22/13**: Temperature 22C, dewpoint 13C
- **A3012**: Pressure 30.12 inches Hg

## API Reference

### GET /

Returns the main application interface.

### POST /get_metar

Fetches and decodes METAR data for a given airport.

**Parameters:**
- `airport_code` (string): 4-letter ICAO airport code

**Response:**
```json
{
  "airport_code": "KJFK",
  "raw_metar": "METAR KJFK 161251Z 28008KT 10SM FEW250 22/13 A3012",
  "decoded_data": {
    "wind": {
      "description": "From the west-northwest",
      "speed": 8,
      "direction": "West-northwest",
      "gust": null
    },
    "temperature": {
      "celsius": 22,
      "fahrenheit": 72
    }
    // ... additional weather data
  }
}
```

##  Project Structure

```
metar-reader/
 app.py                 # Main Flask application
 requirements.txt       # Python dependencies
 pyproject.toml         # Project configuration (uv)
 uv.lock                # Dependency lock file
 static/
    style.css           # Application styles
 templates/
    index.html          # Main HTML template
 README.md              # Project documentation
```

##  Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** and add tests if applicable
4. **Commit your changes** (`git commit -m 'Add amazing feature'`)
5. **Push to the branch** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include comments for complex logic
- Test your changes with multiple airport codes
- Ensure responsive design works on all screen sizes

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## =O Acknowledgments

- **FAA Aviation Weather Center** - For providing free METAR data API
- **International Civil Aviation Organization (ICAO)** - For METAR format standards
- **Flask Community** - For the excellent web framework
- **Python Community** - For the amazing ecosystem

##  Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/suraj-yadav-aiml/METAR-Reader.git/issues) page
2. Create a new issue with detailed description
3. Include your Python version and operating system
4. Provide steps to reproduce the problem

## =. Future Enhancements

- [ ] Add historical weather data support
- [ ] Implement weather alerts and warnings
- [ ] Add aviation-specific calculations (density altitude, etc.)
- [ ] Support for TAF (Terminal Aerodrome Forecast) reports
- [ ] Weather map integration
- [ ] API rate limiting and caching
- [ ] User favorites for frequently checked airports
- [ ] Export weather data to different formats

---