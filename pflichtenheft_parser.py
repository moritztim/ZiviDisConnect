import csv
import json
import sys
import glob
import os
import traceback
import argparse

DELIMITER = ','

HEADER = DELIMITER.join([
	'PLZ',
	'Land',
	'Einsatzbetrieb',
	'Tätigkeiten',
	'Mindestdauer',
	'Arbeitszeitenmodell',
	'Wochenendarbeit Möglich',
	'Nachtarbeit Möglich',
	'Unterkunft',
	'Verpflegung', 
	'Kurse',
	'Kontaktperson Name',
	'Kontaktperson VCard',
	'Schwerpunktprogramm'
])

def extract_sub_csv(list_of_items, key='kurzbeschreibung'):
	"""Create sub-csv strings from lists"""
	if not list_of_items:
		return ""
	return ", ".join(item[key] for item in list_of_items)

def extract_kurs_codes(kurs_list):
	"""Extract course codes"""
	if not kurs_list:
		return ""
	return ", ".join(kurs['code'] for kurs in kurs_list)

def convert_boolean_value(value):
	"""Convert various boolean representations to TRUE/FALSE"""
	if isinstance(value, dict):
		return 'TRUE' if value.get('code') in ['JA', 'IE'] else 'FALSE'
	return 'TRUE' if value else 'FALSE'

def construct_name(first_name, last_name):
	"""Construct full name from first and last name"""
	if first_name and last_name:
		return f"{first_name} {last_name}"
	return first_name or last_name

def create_vcard(first_name, last_name, function, phone_1, phone_2, email, organisation):
	"""Convert kontaktPerson data to VCard format"""
	fields = {
		"BEGIN": "VCARD",
		"VERSION": "4.0",
		"FN": construct_name(first_name, last_name),
		"N": f"{last_name};{first_name};;;" if first_name or last_name else "",
		"ORG": organisation,
		"KIND": "org" if not first_name and not last_name and not function and organisation else "individual",
		"TITLE": function,
		"TEL;TYPE=WORK,X-1": phone_1,
		"TEL;TYPE=WORK,X-2": phone_2,
		"EMAIL": email,
		"END": "VCARD"
	}
	fields = {k: v for k, v in fields.items() if v}
	return "\n".join([f"{k}:{v}" for k, v in fields.items()])

def save_vcard(vcard_content, vcf_dir, filename=None, organisation_id=None):
	"""
	Save vCard to file.
	If filename is not provided but organisation_id is, organisation_id becomes the filename.
	If organisation_id is provided with filename, creates a subfolder with organisation_id.
	"""
	if not vcf_dir:
		return
	
	if filename is None:
		if organisation_id is None:
			raise ValueError("Either filename or organisation_id must be provided")
		# Use organisation_id as filename and save directly in vcf_dir
		filepath = os.path.join(vcf_dir, f"{organisation_id}.vcf")
	else:
		if organisation_id is not None:
			# Create company directory and save file there
			company_dir = os.path.join(vcf_dir, str(organisation_id))
			os.makedirs(company_dir, exist_ok=True)
			filepath = os.path.join(company_dir, f"{filename}.vcf")
		else:
			# Save directly in vcf_dir
			filepath = os.path.join(vcf_dir, f"{filename}.vcf")
	
	with open(filepath, 'w', encoding='utf-8') as f:
		f.write(vcard_content)
	
	return filepath

def json_to_csv(json_data, language, vcf_dir=None):
	"""Process JSON data and return a row for CSV"""
	
	language = language.capitalize()

	def get(key, *sub_keys):
		"""Get value from JSON data"""
		try:
			value = json_data.get(key)
		except Exception as e:
			print(f"Error getting {key}: {str(e)}")
			return ""
		for sub_key in sub_keys:
			if not value:
				return ""
			value = value.get(sub_key)
		return "" if value == None or value == "n/a" else value

	# Create and save contact person vCard
	company_id = get('eibNummer')
	contact_name = construct_name(get('kontaktPersonVorname'), get('kontaktPersonName'))
	vcard_path = ""
	if contact_name and vcf_dir:
		contact_vcard = create_vcard(
			get('kontaktPersonVorname'),
			get('kontaktPersonName'),
			get('kontaktPersonFunktion'),
			get('kontaktPersonTelefon1'),
			get('kontaktPersonTelefon2'),
			get('kontaktPersonEmail'),
			get('eibName')
		)
		vcard_path = save_vcard(contact_vcard, vcf_dir, contact_name, company_id)

	# Create and save company vCard
	if vcf_dir:
		company_vcard = create_vcard(
			"",
			get('eibName'),
			"",
			get('eibTelefon'),
			"",
			get('eibEmail'),
			get('eibName')
		)
		save_vcard(company_vcard, vcf_dir, company_id)

	return DELIMITER.join(
		[f"\"{str(item)}\"" for item in [
			get('eibAdresse', 'plz'),
			get('eibAdresse', 'land', f'text{language}') or "Schweiz",
			get('eibName'),
			extract_sub_csv(get('taetigkeitList')),
			get('mindestdauerEinsatzInWochen'),
			get('arbeitszeitmodell', f'text{language}'),
			'TRUE' if get('wochenendarbeit', 'code') == 'M' else 'FALSE',
			'TRUE' if get('nachtarbeit', 'code') == 'J' else 'FALSE',
			convert_boolean_value(get('unterkunftAngeboten')),
			convert_boolean_value(get('verpflegungAngeboten')),
			extract_kurs_codes(get('kursZiviList')),
			contact_name,
			vcard_path,
			convert_boolean_value(get('schwerpunktprogramm'))
		]]
	)

def main():
	parser = argparse.ArgumentParser(description='Convert JSON to CSV with optional vCard generation')
	parser.add_argument('--language', default='DE', help='Language code', choices=['DE', 'FR', 'IT'])
	parser.add_argument('--vcf', help='Directory path for vCard files. If not provided, vCards will not be generated.')
	parser.add_argument('files', nargs='+', help='JSON files to process')
	
	args = parser.parse_args()

	print(HEADER)
	
	for json_file in args.files:
		try:
			with open(json_file, 'r', encoding='utf-8') as f:
				json_data = json.load(f)
				processed_row = json_to_csv(json_data, args.language, args.vcf)
				print(processed_row)
		except Exception as e:
			print(f"Error processing {json_file}: {str(e)}")
			traceback.print_exc()
			sys.exit(1)

if __name__ == '__main__':
	main()