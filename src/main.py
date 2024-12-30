import argparse
from typing import List
import sys
import os
import json
import time
import random
import csv
from collections.abc import MutableMapping
from zdp_api import ZiviConnectClient, Locale, ApiError
from pflichtenheft_parser import json_to_csv, HEADER

TOKEN_KEY = "ZDP_API_TOKEN"
MIN_SCRAPE_INTERVAL = 6
""" Minimum interval between scraping requests in seconds """
SCRAPE_INTEVAL_FLUCTUATION = 3
""" Maximum fluctuation in scraping interval in seconds """

def create_cli():
	parser = argparse.ArgumentParser(description='ZiviConnect CLI Tool', 
									 epilog=f'Make sure to set the {TOKEN_KEY} environment variable.')
	parser.add_argument('--cookies', help='Path to cookies file')
	parser.add_argument('--locale', choices=['de-CH', 'fr-CH', 'it-CH'],
						default='de-CH', help='Locale for API responses')
	parser.add_argument('--format', choices=['json', 'csv'], default='json',
						help='Output format')
	
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
	search_parser.add_argument('--scrape', nargs='?', const=True, type=str, metavar='DIRECTORY',
							 help='Scrape details for all search results and, if a value is provided, store the resulting files in a directory with the given name.')

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

class OutputType:
	RAW = 'raw'
	SEARCH = 'search_results'
	DETAILS = 'details'

INDENT = "\t"

def format_output(data, format: str, indent:int = 0) -> str:
	if format == 'json':
		rendered_indent = INDENT * indent
		output = json.dumps(data, indent=INDENT)
		if indent:
			output = rendered_indent + output.replace('\n', f'\n{rendered_indent}')
		return output
	return str(data)

# https://stackoverflow.com/a/6027615
# Author: Ophir Carmi
def flatten(dictionary, parent_key='', separator='_'):
    items = []
    for key, value in dictionary.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)

def output(data, args, output_type:OutputType = OutputType.RAW, trailing_newline:bool = True, title:str = None, first:bool = None, last:bool = None):
	if output_type == OutputType.RAW:
		if trailing_newline:
			data = f"{data}\n"
	if args.scrape == True and args.format == 'json' and output_type != OutputType.RAW:
		# {search_results: [ ... ], details: { [...] }}
		output(f"{"{" if output_type == OutputType.SEARCH else ","}\n", args, trailing_newline=False)
		if first or first == None:
			output(f"{INDENT}\"{output_type}\":{f"\n{INDENT * 2}[" if output_type == OutputType.DETAILS else ""}", args)
		output(format_output(data, args.format, 2+int(output_type == OutputType.DETAILS)), args, trailing_newline=False, title=title if title else "data")
		if output_type == OutputType.SEARCH:
			output(f"\n{INDENT}", args, trailing_newline=False)
		if last and output_type == OutputType.DETAILS:
			output(f"\n{INDENT * 2}]\n{"}"}", args)
		return
	
	if not title:
		title = output_type

	if args.format == 'csv' and output_type == OutputType.DETAILS:
		if first or first == None:
			output(HEADER, args, title=title)
		return output(json_to_csv(data, args.locale.split('-')[0], f"{args.scrape}/VCards" if args.scrape else None), args, title=title)

	if isinstance(args.scrape, str):
		os.makedirs(args.scrape, exist_ok=True)
		file_name = f"{args.scrape}/{title}.{args.format}"
		if args.format == 'csv' and output_type == OutputType.SEARCH:
			with open(file_name, 'w') as f:
				if output_type == OutputType.SEARCH:
					data = [flatten(entry, separator=".") for entry in data]
					writer = csv.DictWriter(f, fieldnames=data[0].keys())
					writer.writeheader()
					writer.writerows(data)
					return
				else:
					f.write(str(data))
					return
		
		if output_type == OutputType.RAW:
			with open(file_name, 'a+') as f:
				f.write(str(data))
			return
		
		if args.format == 'json':
			# if first or last are None, that means we are not in a loop.
			return output(f"{"[\n" if first else ""}{format_output(data, args.format, first != None)}{"," if last == False else "\n]" if last else ""}", args, title=title)
		
	if output_type == OutputType.RAW:
		sys.stdout.write(data)
		return
	
	return output(format_output(data, args.format), args, OutputType.RAW, trailing_newline, title, first, last)

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

			output(result, args, OutputType.SEARCH)
			if args.scrape:
				for key in range(len(result)):
					output(client.pflichtenheft(result[key]['pflichtenheftId']), args, OutputType.DETAILS, first=(key == 0), last=(key == len(result)-1))
					if key < len(result)-1:
						time.sleep(MIN_SCRAPE_INTERVAL + random.random()*SCRAPE_INTEVAL_FLUCTUATION)

		elif args.command == 'details':
			output(client.pflichtenheft(args.id))
			
	except ApiError as e:
		print(f"Error: {str(e)}", file=sys.stderr)
		sys.exit(1)
	except KeyboardInterrupt:
		print("\nOperation cancelled by user")
		sys.exit(1)

if __name__ == '__main__':
	main()

# This script includes creative contributions from a generative AI. https://declare-ai.org/1.0.0/creative.html
