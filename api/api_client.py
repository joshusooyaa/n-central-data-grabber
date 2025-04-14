import requests
import datetime

MAX_RETRY = 3 # Number of times to 

class APIClient:
  def __init__(self, config, logger):
    self.logger = logger
    self.base_url = config['API']['api-endpoints']['base-url']
    self.jwt = (config['API']['api-jwt'])
    self.logger.info(f"APIClient initialized with base URL: {self.base_url}")
    self.auth_endpoint = config['API']['api-endpoints']['auth']['authenticate-endpoint']
    self.refresh_endpoint = config['API']['api-endpoints']['auth']['refresh-endpoint']
    self.token_refresh_offset = datetime.timedelta(minutes=config['API']['api-token-refresh-offset'])

    self.refresh = None
    self.token = None
    self._build_token()

  def _build_token(self):
    self.logger.info(f"Buiding token from scratch.")
    resp = self.post(self.auth_endpoint)
    if resp and resp.get('tokens'):
      self.token = {
        'token': resp['tokens']['access']['token'],
        'expiry': datetime.datetime.now() + datetime.timedelta(seconds=resp['tokens']['access']['expirySeconds']) - self.token_refresh_offset
      }
      self.refresh = {
        'token': resp['tokens']['refresh']['token'],
        'expiry': datetime.datetime.now() + datetime.timedelta(seconds=resp['tokens']['refresh']['expirySeconds']) - self.token_refresh_offset
      }
    else:
      self.logger.error("Failed to build token. Make sure API token is valid.")

  def _refresh_token(self):
    if self._is_refresh_expired():
      self.logger.info(f"Refresh token expired, building new token.")
      self._build_token()
    else:
      self.logger.info(f"Refreshing token")
      resp = self.post(self.refresh_endpoint, data=self.refresh['token'])
      if resp:
        self.token = {
          'token': resp['tokens']['access']['token'],
          'expiry': datetime.datetime.now() + datetime.timedelta(seconds=resp['tokens']['access']['expirySeconds'])
        }
        self.logger.info(f"Token successfully refreshed.")
      else:
        self.logger.warning("Failed to refresh token. Attempting to build token from scratch.")
        self._build_token()

  def _build_url(self, endpoint, params=None, data=None):
    return f"{self.base_url}/{endpoint}"
  
  def _check_status(self, response):
    status = response.status_code
    if (status == 200 or status == 201 or status == 204 or status == 206):
      return True
    else:
      return False

  def _build_headers(self, endpoint):
    if endpoint == self.auth_endpoint:
      return {
        'accept': '*/*',
        'Authorization': f'Bearer {self.jwt}'
      }
    elif endpoint == self.refresh_endpoint:
      return {
        'accept': '*/*',
        'Authorization': f'Bearer {self.refresh["token"]}'
      }
    else:
      return {
        'accept': '*/*',
        'Authorization': f'Bearer {self.token["token"]}'
      }

  def _is_token_expired(self):
    return datetime.datetime.now() >= self.token['expiry']

  def _is_refresh_expired(self):
    return datetime.datetime.now() >= self.refresh['expiry']

  def _get_with_retries(self, url, params, headers, endpoint, retry_count=0):
    try:
      response = requests.get(url, params=params, headers=headers)
      
      if self._check_status(response):
        return response.json()
      elif response.status_code == 401 and 'UnauthorizedException' in response.text and retry_count < MAX_RETRY:
        self.logger.error(f"Authorization failed with API Token. Attempting with new token and retrying... (retry: {retry_count+1})")
        self._refresh_token()
        return self._get_with_retries(url, params, headers, endpoint, retry_count + 1)
      else: 
        self.logger.error(f"Failed to GET from endpoint {endpoint}: {response.status_code}, {response.text}")
        return None
    except requests.exceptions.RequestException as e:
      self.logger.error(f"API GET request failed: {e}")
      return None

  def get(self, endpoint, params=None):
    if (self._is_token_expired()):
      self._refresh_token()

    url = self._build_url(endpoint)
    headers = self._build_headers(endpoint)
    return self._get_with_retries(url, params, headers, endpoint)

  def post(self, endpoint, data=""):
    url = self._build_url(endpoint)
    headers = self._build_headers(endpoint)

    try:
      response = requests.post(url, headers=headers, data=data)
      if self._check_status(response):
        response_data = response.json()
        return response_data
      else:
        self.logger.error(f"Failed to POST to endpoint {endpoint}: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
      self.logger.error(f"API POST request failed: {e}")
      return None