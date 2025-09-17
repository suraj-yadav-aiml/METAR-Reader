#!/usr/bin/env python3
"""
Unit tests for METAR Reader application.

This module contains comprehensive tests for the MetarDecoder class and Flask routes,
using mock METAR data to ensure accurate weather interpretation.

Author: Claude Code
License: MIT
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from app import app, MetarDecoder, fetch_metar


class TestMetarDecoder(unittest.TestCase):
    """Test cases for the MetarDecoder class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.decoder = MetarDecoder()

    def test_degrees_to_direction(self):
        """Test wind direction conversion from degrees to compass direction."""
        # Test cardinal directions
        self.assertEqual(self.decoder.degrees_to_direction(0), "North")
        self.assertEqual(self.decoder.degrees_to_direction(90), "East")
        self.assertEqual(self.decoder.degrees_to_direction(180), "South")
        self.assertEqual(self.decoder.degrees_to_direction(270), "West")

        # Test intermediate directions
        self.assertEqual(self.decoder.degrees_to_direction(45), "Northeast")
        self.assertEqual(self.decoder.degrees_to_direction(225), "Southwest")

        # Test edge cases
        self.assertEqual(self.decoder.degrees_to_direction(360), "North")  # Should wrap around
        self.assertEqual(self.decoder.degrees_to_direction(None), "variable")

    def test_decode_visibility(self):
        """Test visibility value formatting."""
        self.assertEqual(self.decoder.decode_visibility(10), "10+ miles")
        self.assertEqual(self.decoder.decode_visibility(15), "10+ miles")
        self.assertEqual(self.decoder.decode_visibility(5), "5 miles")
        self.assertEqual(self.decoder.decode_visibility(1), "1 miles")
        self.assertEqual(self.decoder.decode_visibility(0.5), "0.5 mile")
        self.assertEqual(self.decoder.decode_visibility(0.25), "0.25 mile")

    def test_decode_sky_condition(self):
        """Test sky condition code interpretation."""
        self.assertEqual(self.decoder.decode_sky_condition("CLR"), "Clear skies")
        self.assertEqual(self.decoder.decode_sky_condition("SKC"), "Sky clear")
        self.assertEqual(self.decoder.decode_sky_condition("FEW"), "Few clouds")
        self.assertEqual(self.decoder.decode_sky_condition("SCT"), "Scattered clouds")
        self.assertEqual(self.decoder.decode_sky_condition("BKN"), "Broken clouds")
        self.assertEqual(self.decoder.decode_sky_condition("OVC"), "Overcast")

        # Test unknown codes
        self.assertEqual(self.decoder.decode_sky_condition("XXX"), "XXX")

    def test_decode_weather_phenomenon(self):
        """Test weather phenomenon interpretation."""
        # Test precipitation
        self.assertEqual(self.decoder.decode_weather_phenomenon("RA"), "rain")
        self.assertEqual(self.decoder.decode_weather_phenomenon("-RA"), "Light rain")
        self.assertEqual(self.decoder.decode_weather_phenomenon("+RA"), "Heavy rain")

        # Test snow
        self.assertEqual(self.decoder.decode_weather_phenomenon("SN"), "snow")
        self.assertEqual(self.decoder.decode_weather_phenomenon("-SN"), "Light snow")

        # Test thunderstorms
        self.assertEqual(self.decoder.decode_weather_phenomenon("TSRA"), "Thunderstorms with rain")

        # Test obscuration
        self.assertEqual(self.decoder.decode_weather_phenomenon("FG"), "fog")
        self.assertEqual(self.decoder.decode_weather_phenomenon("BR"), "mist")
        self.assertEqual(self.decoder.decode_weather_phenomenon("HZ"), "haze")

    def test_celsius_to_fahrenheit(self):
        """Test temperature conversion."""
        self.assertEqual(self.decoder.celsius_to_fahrenheit(0), 32)
        self.assertEqual(self.decoder.celsius_to_fahrenheit(100), 212)
        self.assertEqual(self.decoder.celsius_to_fahrenheit(-40), -40)
        self.assertEqual(self.decoder.celsius_to_fahrenheit(20), 68)
        self.assertEqual(self.decoder.celsius_to_fahrenheit(-10), 14)

    def test_decode_metar_empty_input(self):
        """Test handling of empty METAR input."""
        result = self.decoder.decode_metar("")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No METAR data available")

        result = self.decoder.decode_metar(None)
        self.assertIn("error", result)

    def test_decode_metar_clear_conditions(self):
        """Test decoding of clear weather conditions."""
        # KJFK clear conditions
        metar = "METAR KJFK 161251Z 28008KT 10SM CLR 22/13 A3012 RMK AO2"
        result = self.decoder.decode_metar(metar)

        # Check wind data
        self.assertIsNotNone(result["wind"])
        self.assertEqual(result["wind"]["speed"], 8)
        self.assertEqual(result["wind"]["direction"], "West")  # 280 degrees = West
        self.assertIsNone(result["wind"]["gust"])

        # Check visibility
        self.assertIsNotNone(result["visibility"])
        self.assertEqual(result["visibility"]["value"], 10)

        # Check temperature
        self.assertIsNotNone(result["temperature"])
        self.assertEqual(result["temperature"]["celsius"], 22)
        self.assertEqual(result["temperature"]["fahrenheit"], 72)

        # Check dewpoint
        self.assertIsNotNone(result["dewpoint"])
        self.assertEqual(result["dewpoint"]["celsius"], 13)
        self.assertEqual(result["dewpoint"]["fahrenheit"], 55)

        # Check sky conditions
        self.assertEqual(len(result["sky_conditions"]), 1)
        self.assertEqual(result["sky_conditions"][0]["condition"], "CLR")

        # Check pressure
        self.assertIsNotNone(result["pressure"])
        self.assertEqual(result["pressure"]["inches_hg"], 30.12)

        # Check time
        self.assertIsNotNone(result["time"])
        self.assertEqual(result["time"], "16th at 12:51 UTC")

    def test_decode_metar_stormy_conditions(self):
        """Test decoding of stormy weather conditions."""
        # Thunderstorm with heavy rain
        metar = "METAR KLAX 161253Z 25015G25KT 3SM +TSRA BKN008 OVC015 18/16 A2995"
        result = self.decoder.decode_metar(metar)

        # Check wind with gusts
        self.assertEqual(result["wind"]["speed"], 15)
        self.assertEqual(result["wind"]["gust"], 25)

        # Check reduced visibility
        self.assertEqual(result["visibility"]["value"], 3)

        # Check weather phenomena - should have thunderstorm with rain
        self.assertGreater(len(result["weather_phenomena"]), 0)
        # Look for thunderstorm and rain in any of the phenomena
        phenomena_descriptions = [p["description"] for p in result["weather_phenomena"]]
        phenomena_text = " ".join(phenomena_descriptions)
        self.assertIn("Heavy", phenomena_text)
        self.assertIn("Thunderstorms", phenomena_text)

        # Check multiple cloud layers
        self.assertEqual(len(result["sky_conditions"]), 2)
        self.assertEqual(result["sky_conditions"][0]["condition"], "BKN")
        self.assertEqual(result["sky_conditions"][0]["height"], 800)
        self.assertEqual(result["sky_conditions"][1]["condition"], "OVC")
        self.assertEqual(result["sky_conditions"][1]["height"], 1500)

    def test_decode_metar_calm_winds(self):
        """Test decoding of calm wind conditions."""
        metar = "METAR KTIG 161255Z 00000KT 10SM CLR 25/10 A3020"
        result = self.decoder.decode_metar(metar)

        self.assertEqual(result["wind"]["description"], "Calm")
        self.assertEqual(result["wind"]["speed"], 0)
        self.assertIsNone(result["wind"]["direction"])

    def test_decode_metar_variable_winds(self):
        """Test decoding of variable wind conditions."""
        metar = "METAR KORD 161252Z VRB05KT 10SM FEW250 20/15 A3015"
        result = self.decoder.decode_metar(metar)

        self.assertEqual(result["wind"]["speed"], 5)
        self.assertIn("variable", result["wind"]["description"].lower())

    def test_decode_metar_negative_temperatures(self):
        """Test decoding of below-freezing temperatures."""
        metar = "METAR CYUL 161200Z 32010KT 10SM CLR M05/M12 A3025"
        result = self.decoder.decode_metar(metar)

        # Check negative temperature
        self.assertEqual(result["temperature"]["celsius"], -5)
        self.assertEqual(result["temperature"]["fahrenheit"], 23)

        # Check negative dewpoint
        self.assertEqual(result["dewpoint"]["celsius"], -12)
        self.assertEqual(result["dewpoint"]["fahrenheit"], 10)

    def test_decode_metar_fractional_visibility(self):
        """Test decoding of fractional visibility."""
        metar = "METAR KBOS 161254Z 09008KT 1/2SM FG OVC002 15/15 A2990"
        result = self.decoder.decode_metar(metar)

        self.assertEqual(result["visibility"]["value"], 0.5)
        self.assertEqual(result["visibility"]["description"], "0.5 mile")


class TestFlaskRoutes(unittest.TestCase):
    """Test cases for Flask application routes."""

    def setUp(self):
        """Set up test client before each test method."""
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        """Test the main index route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'METAR Reader', response.data)

    def test_get_metar_missing_airport_code(self):
        """Test API with missing airport code."""
        response = self.app.post('/get_metar', data={})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Please enter an airport code')

    def test_get_metar_invalid_airport_code_length(self):
        """Test API with invalid airport code length."""
        # Too short
        response = self.app.post('/get_metar', data={'airport_code': 'JFK'})
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('4 characters', data['error'])

        # Too long
        response = self.app.post('/get_metar', data={'airport_code': 'KJFKA'})
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.fetch_metar')
    def test_get_metar_successful_response(self, mock_fetch):
        """Test successful METAR API response with mocked data."""
        # Mock the fetch_metar function
        mock_metar = "METAR KJFK 161251Z 28008KT 10SM CLR 22/13 A3012 RMK AO2"
        mock_fetch.return_value = (mock_metar, None)

        response = self.app.post('/get_metar', data={'airport_code': 'KJFK'})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['airport_code'], 'KJFK')
        self.assertEqual(data['raw_metar'], mock_metar)
        self.assertIn('decoded_data', data)
        self.assertIn('wind', data['decoded_data'])

    @patch('app.fetch_metar')
    def test_get_metar_fetch_error(self, mock_fetch):
        """Test API response when fetch_metar returns an error."""
        # Mock fetch_metar to return an error
        mock_fetch.return_value = (None, "No METAR data found for this airport code")

        response = self.app.post('/get_metar', data={'airport_code': 'XXXX'})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], "No METAR data found for this airport code")


class TestFetchMetar(unittest.TestCase):
    """Test cases for the fetch_metar function."""

    @patch('app.requests.get')
    def test_fetch_metar_successful(self, mock_get):
        """Test successful METAR data fetch."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.text = "METAR KJFK 161251Z 28008KT 10SM CLR 22/13 A3012"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        metar_data, error = fetch_metar("KJFK")

        self.assertIsNotNone(metar_data)
        self.assertIsNone(error)
        self.assertIn("KJFK", metar_data)

        # Verify the correct URL was called
        expected_url = "https://aviationweather.gov/api/data/metar?ids=KJFK"
        mock_get.assert_called_once_with(expected_url, timeout=10)

    @patch('app.requests.get')
    def test_fetch_metar_empty_response(self, mock_get):
        """Test fetch_metar with empty response."""
        # Mock empty HTTP response
        mock_response = MagicMock()
        mock_response.text = "   "  # Only whitespace
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        metar_data, error = fetch_metar("XXXX")

        self.assertIsNone(metar_data)
        self.assertIsNotNone(error)
        self.assertEqual(error, "No METAR data found for this airport code")

    @patch('app.requests.get')
    def test_fetch_metar_http_error(self, mock_get):
        """Test fetch_metar with HTTP error."""
        # Mock requests.RequestException which is what the function catches
        import requests
        mock_get.side_effect = requests.RequestException("Connection timeout")

        metar_data, error = fetch_metar("KJFK")

        self.assertIsNone(metar_data)
        self.assertIsNotNone(error)
        self.assertIn("Error fetching METAR data", error)

    @patch('app.requests.get')
    def test_fetch_metar_case_insensitive(self, mock_get):
        """Test that airport codes are converted to uppercase."""
        mock_response = MagicMock()
        mock_response.text = "METAR KJFK 161251Z 28008KT 10SM CLR 22/13 A3012"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test with lowercase airport code
        fetch_metar("kjfk")

        # Verify uppercase was used in URL
        expected_url = "https://aviationweather.gov/api/data/metar?ids=KJFK"
        mock_get.assert_called_once_with(expected_url, timeout=10)


class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.decoder = MetarDecoder()

    def test_complete_metar_processing_pipeline(self):
        """Test complete METAR processing from raw data to structured output."""
        # Test data representing various weather conditions
        test_cases = [
            {
                'name': 'Clear conditions',
                'metar': 'METAR KJFK 161251Z 28008KT 10SM CLR 22/13 A3012',
                'expected_elements': ['wind', 'visibility', 'temperature', 'sky_conditions', 'pressure']
            },
            {
                'name': 'Stormy conditions',
                'metar': 'METAR KLAX 161253Z 25015G25KT 3SM +TSRA BKN008 OVC015 18/16 A2995',
                'expected_elements': ['wind', 'visibility', 'weather_phenomena', 'sky_conditions']
            },
            {
                'name': 'Foggy conditions',
                'metar': 'METAR KORD 161254Z 09008KT 1/4SM FG OVC002 15/15 A2990',
                'expected_elements': ['wind', 'visibility', 'weather_phenomena', 'sky_conditions']
            }
        ]

        for case in test_cases:
            with self.subTest(case=case['name']):
                result = self.decoder.decode_metar(case['metar'])

                # Verify no error occurred
                self.assertNotIn('error', result)

                # Verify expected elements are present
                for element in case['expected_elements']:
                    self.assertIn(element, result, f"Missing {element} in {case['name']}")

                # Verify structure integrity
                if result.get('wind'):
                    self.assertIn('speed', result['wind'])
                    self.assertIn('description', result['wind'])

                if result.get('temperature'):
                    self.assertIn('celsius', result['temperature'])
                    self.assertIn('fahrenheit', result['temperature'])


if __name__ == '__main__':
    """Run all tests when script is executed directly."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMetarDecoder))
    suite.addTests(loader.loadTestsFromTestCase(TestFlaskRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestFetchMetar))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)