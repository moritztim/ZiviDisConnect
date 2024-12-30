from dataclasses import dataclass
from typing import List, Optional
import requests
from enum import Enum

class ApiError(Exception):
	"""Custom exception for API-related errors."""
	pass

class Locale(str, Enum):
	"""Supported locales for the API."""
	DE = "de-CH"
	FR = "fr-CH"
	IT = "it-CH"

class ZiviConnectClient:
	"""
	Client for interacting with the ZiviConnect API.
	
	Attributes:
		base_url (str): Base URL for the API
		locale (Locale): Locale for API responses
		token (str): Authentication token
	"""

	def __init__(self, token: str, cookies: dict = None, locale: Locale = Locale.DE):
		"""
		Initialize the API client.
		
		Args:
			locale: Preferred locale for API responses
		"""
		self.base_url = "https://ziviconnect.admin.ch/web-zdp/api"
		self.locale = locale
		self.token = token
		self._session = requests.Session()
		if cookies:
			self._session.cookies.update(cookies)

	def _get_headers(self) -> dict:
		"""
		Get headers required for API requests.
		
		Returns:
			dict: Headers dictionary
		
		Raises:
			ApiError: If no authentication token is set
		"""
		if not self.token:
			raise ApiError("Authentication token not set.")

		return {
			"Accept": "application/json",
			"Content-Type": "application/json",
			"x-zivi-locale": self.locale,
			"Authorization": f"Bearer {self.token}",
			"Origin": self.base_url,
			"Referer": f"{self.base_url}/zdp/einsatz"
		}

	def search(
		self,
		search_text: Optional[str] = None,
		einsatzort_id: Optional[int] = None,
		umkreis: Optional[int] = None,
		einsatzdauer: Optional[int] = None,
		taetigkeitsbereich_ids: Optional[List[int]] = None,
		sprache_ids: Optional[List[int]] = None,
		kennzeichnung_speziell_codes: Optional[List[str]] = None
	) -> dict:
		"""
		Search for Pflichtenheft entries.
		
		Args:
			search_text: Text to search for
			einsatzort_id: ID of the deployment location
			umkreis: Radius in km (0-25 in steps of 5)
			einsatzdauer: Duration in weeks (max 52)
			taetigkeitsbereich_ids: List of activity area IDs
			sprache_ids: List of language IDs (max 3)
			kennzeichnung_speziell_codes: List of special marking codes (max 3)
		
		Returns:
			Raw JSON response from the API
			
		Raises:
			ApiError: If the request fails or parameters are invalid
		"""
		# Validate parameters
		if umkreis and (umkreis < 0 or umkreis > 25 or umkreis % 5 != 0):
			raise ApiError("umkreis must be between 0 and 25 in steps of 5")
		
		if einsatzdauer and (einsatzdauer < 1 or einsatzdauer > 52):
			raise ApiError("einsatzdauer must be between 1 and 52")
			
		if sprache_ids and len(sprache_ids) > 3:
			raise ApiError("Maximum 3 sprache_ids allowed")
			
		if kennzeichnung_speziell_codes and len(kennzeichnung_speziell_codes) > 3:
			raise ApiError("Maximum 3 kennzeichnung_speziell_codes allowed")

		# Build request payload
		payload = {
			"searchText": search_text,
			"einsatzortId": einsatzort_id,
			"umkreis": umkreis,
			"einsatzdauer": einsatzdauer,
			"taetigkeitsbereichId": taetigkeitsbereich_ids,
			"spracheId": sprache_ids,
			"pflichtenheftKennzeichnungSpeziellCodeList": kennzeichnung_speziell_codes
		}
		
		# Remove None values
		payload = {k: v for k, v in payload.items() if v is not None}

		response = self._session.post(
			f"{self.base_url}/pflichtenheft/search",
			headers=self._get_headers(),
			json=payload
		)

		if response.status_code != 200:
			raise ApiError(f"API request failed with status {response.status_code}: {response.text}")

		# Parse response into Pflichtenheft objects
		return response.json()

# This script includes creative contributions from a generative AI. https://declare-ai.org/1.0.0/creative.html
