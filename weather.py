from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP


# Initialize FastMCP server
mcp = FastMCP('weather')


# Constants
NWS_API_BASE = 'https://api.weather.gov'
USER_AGENT = 'weather-app/1.0'


# Helper functions
async def make_nws_request(url: str) -> dict[str, Any] | None:
  """
  Make a request to the NWS API with proper error handling.
  Returns JSON response or None on failure.
  """
  headers = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/geo+json',
  }

  async with httpx.AsyncClient() as client:
    try:
      response = await client.get(url, headers=headers, timeout=30.0)
      response.raise_for_status()
      return response.json()
    except Exception:
      return None
    

def format_alert(feature: dict) -> str:
  """
  Format a weather alert feature into a readable string.
  """
  properties = feature.get('properties', {})
  event = properties.get('event', 'Unknown Event')
  area = properties.get('areaDesc', 'Unknown Area')
  severity = properties.get('severity', 'Unknown Severity')
  description = properties.get('description', 'No description available.')
  instructions = properties.get('instruction', 'No specific instructions provided.')

  alert_message = (
      f'**{event}**\n'
      f'*Area:* {area}\n\n'
      f'*Severity:* {severity}\n'
      f'{description}\n\n'
      f'**Instructions:** {instructions}'
  )

  return alert_message


# Tool execution functions
@mcp.tool()
async def get_alerts(state: str) -> str:
  """
  Get current weather alerts for a given US state.

  Args:
    state: Two-letter US state code (e.g. CA, NY)
  """
  url = f'{NWS_API_BASE}/alerts/active/area/{state}'
  data = await make_nws_request(url)

  if not data or 'features' not in data:
    return 'Unable to fetch alerts or no alerts found.'

  if not data['features']:
      return 'No active alerts for this state.'

  alerts = [format_alert(feature) for feature in data['features']]
  return '\n---\n'.join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
  """
  Get weather forecast for a location.

  Args:
      latitude: Latitude of the location
      longitude: Longitude of the location
  """
  # First get the forecast grid endpoint
  points_url = f'{NWS_API_BASE}/points/{latitude},{longitude}'
  points_data = await make_nws_request(points_url)

  if not points_data:
    return 'Unable to fetch forecast data for this location.'

  # Get the forecast URL from the points response
  forecast_url = points_data['properties']['forecast']
  forecast_data = await make_nws_request(forecast_url)

  if not forecast_data:
    return 'Unable to fetch detailed forecast.'
  
  # Format the periods into a readable forecast
  periods = forecast_data['properties']['periods']
  forecasts = []
  for period in periods[:5]:  # Limit to next 5 periods
    name = period['name']
    temp = f"{period['temperature']}°{period['temperatureUnit']}"
    wind = f"{period['windSpeed']} {period['windDirection']}"
    foreast_text = period['detailedForecast']
    forecast = (
      f'**{name}**\n'
      f'- Temperature: {temp}\n'
      f'- Wind: {wind}\n'
      f'- Forecast: {foreast_text}\n'
    )
    forecasts.append(forecast)
    return "\n---\n".join(forecasts)
  

# Initialize and run the server
if __name__ == '__main__':
  mcp.run(transport='stdio')
