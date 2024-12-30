import argparse
from typing import List
import sys
import os
import json
import time
import random
from zdp_api import ZiviConnectClient, Locale, ApiError

TOKEN_KEY = "ZDP_API_TOKEN"
MIN_SCRAPE_INTERVAL = 10
""" Minimum interval between scraping requests in seconds """
SCRAPE_INTEVAL_FLUCTUATION = 3
""" Maximum fluctuation in scraping interval in seconds """

def create_cli():
	parser = argparse.ArgumentParser(description='ZiviConnect CLI Tool', 
									 epilog=f'Make sure to set the {TOKEN_KEY} environment variable.')
	parser.add_argument('--cookies', help='Path to cookies file')
	parser.add_argument('--locale', choices=['de-CH', 'fr-CH', 'it-CH'],
						default='de-CH', help='Locale for API responses')
	
	# Add subparsers for different commands
	subparsers = parser.add_subparsers(dest='command', help='Available commands')

	# Details command
	details_parser = subparsers.add_parser('details', help='Get details for a Pflichtenheft entry')
	details_parser.add_argument('id', type=int, help='ID of the Pflichtenheft entry')
	
	# Search command
	search_parser = subparsers.add_parser('search', help='Search for Pflichtenheft entries')
	search_parser.add_argument('--text', help='Text to search for')
	search_parser.add_argument('--location-id', type=int, help='ID of the deployment location')
	search_parser.add_argument('--radius', type=int, choices=[0,5,10,15,20,25], 
							 help='Search radius in km (0-25 in steps of 5)')
	search_parser.add_argument('--duration', type=int, help='Duration in weeks (1-52)')
	search_parser.add_argument('--activity-areas', type=int, nargs='+', 
							 help='List of activity area IDs')
	search_parser.add_argument('--languages', type=int, nargs='+', 
							 help='List of language IDs (max 3)')
	search_parser.add_argument('--special-codes', nargs='+',
							 help='List of special marking codes (max 3)')
	search_parser.add_argument('--scrape', action='store_true', help='Scrape detailed information for results')

	return parser

def parse_cookies_file(file_path: str) -> dict:
	"""Parse a Netscape format cookies file"""
	cookies = {}
	with open(file_path, 'r') as f:
		for line in f:
			if not line.startswith('#'):
				fields = line.strip().split('\t')
				if len(fields) >= 7:
					cookies[fields[5]] = fields[6]
	return cookies

def main():
	parser = create_cli()
	args = parser.parse_args()

	if not args.command:
		parser.print_help()
		sys.exit(1)

	# Initialize client
	token = os.getenv(TOKEN_KEY)
	if not token:
		print(f"Error: {TOKEN_KEY} environment variable not set.", file=sys.stderr)
		sys.exit(1)
	client = ZiviConnectClient(token, parse_cookies_file(args.cookies) if args.cookies else None, args.locale)
	
	try:

		if args.command == 'search':
			result = client.search(
				search_text=args.text,
				einsatzort_id=args.location_id,
				umkreis=args.radius,
				einsatzdauer=args.duration,
				taetigkeitsbereich_ids=args.activity_areas,
				sprache_ids=args.languages,
				kennzeichnung_speziell_codes=args.special_codes
			)

			if args.scrape:
				print(f"{"{"}'result': {result},'details': [")
				for entry in result:
					print(f"{client.pflichtenheft(entry['pflichtenheftId'])},")
					time.sleep(MIN_SCRAPE_INTERVAL + random.random()*SCRAPE_INTEVAL_FLUCTUATION)
				print("]}")
				return
			print(result)

		elif args.command == 'details':
			print(client.pflichtenheft(args.id))
			
	except ApiError as e:
		print(f"Error: {str(e)}", file=sys.stderr)
		sys.exit(1)
	except KeyboardInterrupt:
		print("\nOperation cancelled by user")
		sys.exit(1)

if __name__ == '__main__':
	main()

# This script includes creative contributions from a generative AI. https://declare-ai.org/1.0.0/creative.html
