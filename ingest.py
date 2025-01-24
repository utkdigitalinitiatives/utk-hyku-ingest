import csv
import argparse

RDF_TYPE_MAP = {
  'Preservation': 'http://pcdm.org/use#PreservationFile', # will have _p at end of file_identifier
  'Intermediate': 'http://pcdm.org/use#IntermediateFile', # will have _i at end of file_identifier
  'Access': 'http://pcdm.org/use#ServiceFile',            # 
  'HOCR': 'http://pcdm.org/file-format-types#HTML',       # only applies to books?, has _hocr 
  'PDF': 'http://pcdm.org/file-format-types#Document',    # if model is pdf 
  'Transcript': 'http://pcdm.org/use#Transcript',         # will have _transcript at end of file_identifier
  'OCR': 'http://pcdm.org/use#ExtractedText',             # only applies to books, has _ocr
}

# This is only for works, so should already be filled in
# HAS_WORK_TYPE_MAP = { 
#   'Audio': 'https://ontology.lib.utk.edu/works#AudioWork',
#   'Book': 'https://ontology.lib.utk.edu/works#BookWork',
#   'CompoundObject': 'https://ontology.lib.utk.edu/works#CompoundObjectWork',
#   'Generic': 'https://ontology.lib.utk.edu/works#GenericWork',
#   'Image': 'https://ontology.lib.utk.edu/works#ImageWork',
#   'Pdf': 'https://ontology.lib.utk.edu/works#PDFWork',
#   'Video': 'https://ontology.lib.utk.edu/works#VideoWork',
# }

RESTRICTED_TITLES = { # TODO titles are slightly different now so this may need to change
  'MODS',
  'Preserve',
  'Release',
  'Bioform',
  'RELS-INT',
  'HOCR',
  'METS',
  'ALTO'
}

VISIBILITY_TYPE_MAP = [ # reference for types of visibilities
  'open',
  'restricted',
  'authenticated'
]

# Given a work row, does any edits/checks needed to the row and returns it
def verify_work_row(work, verbose):
  if ' ' in work['source_identifier']:
    if verbose:
      print("removing spaces from source_identifier")
    work['source_identifier'] = work['source_identifier'].strip()
    work['source_identifier'] = work['source_identifier'].replace(' ', '_')
  return work

# Given an attachment row, does any edits/checks needed to the row and returns it
def verify_attachment_row(attachment, verbose):
  if ' ' in attachment['source_identifier']:
    if verbose:
      print("removing spaces from source_identifier")
    attachment['source_identifier'] = attachment['source_identifier'].strip()
    attachment['source_identifier'] = attachment['source_identifier'].replace(' ', '_')
  

  return attachment

# Given a work row, returns an attachment row with all pertinent information filled in
def create_attachment_row(work, verbose):
  #TODO get the proper title for book/compound objects
  if work['model'].lower() == 'image': # Special case for images
    title = 'Image for ' + work['source_identifier']
  else:
    title = work['model'] + " for " + work['title']
  
  #TODO special case for av files, transcript attachment will be there but need to create access file
  
  #Finds the correct RDF type
  #TODO this could use a rewrite to be safer and less error prone
  if work['model'].lower() == 'pdf':
    rdf = RDF_TYPE_MAP['PDF']
  elif "_i" in work['file_identifier']:
    rdf = RDF_TYPE_MAP['Intermediate'] 
  elif "_p" in work['file_identifier']:
    rdf = RDF_TYPE_MAP['Preservation']
  elif "_transcript" in work['file_identifier']:
    rdf = RDF_TYPE_MAP['Transcript']
  elif "_ocr" in work['file_identifier']:
    rdf = RDF_TYPE_MAP['OCR']
  elif "_hocr" in work['file_identifier']:
    rdf = RDF_TYPE_MAP['HOCR']
  else:
    rdf = RDF_TYPE_MAP['Access']

  #checks if the title is in the list of restricted titles and sets visibility accordingly, default is open
  vis = VISIBILITY_TYPE_MAP[0]
  if title in RESTRICTED_TITLES:
    vis = VISIBILITY_TYPE_MAP[1]
  
  # this defines everything in the attachment row
  attachment = {
    'source_identifier': work['source_identifier'] + '_attachment',
    'title': title,
    'model': 'Attachment',
    'parents': work['source_identifier'],
    'visibility': vis,
    # 'sequence': '0',                      #this should be filled in manually, here just as reminder the column exists
    'rdf_type': rdf,
  }

  return attachment

# Given an attachment row, returns a fileset row with all data filled in
# the majority of the fileset row is copied verbatim from the attachment, remote files is the main exception
def create_fileset_row(attachment, work, verbose):
  # this defines everything in the fileset row
  fileset = {
    'source_identifier': work['source_identifier'] + '_fileset',
    'title': attachment['title'],
    'model': 'FileSet',
    'parents': attachment['source_identifier'],
    'visibility': attachment.get('visibility', 'open'),
    'sequence': attachment.get('sequence', ''),
    'rdf_type': attachment['rdf_type'],
    'remote_files': 'http://hykuimports.lib.utk.edu/files/hyku-import/' + work['file_identifier']
  }
  return fileset

# TODO this does not need to be its own function, was easier to write to get it working quickly
def remove_file_identifier_column(row):
  if 'file_identifier' in row:
    del row['file_identifier']
  return row

#TODO also was just simpler to make its own function, however should be rewritten to NOT use a second file pointer
def add_title_to_book_page(attachment, reader, verbose):
  # finds the work row from reader with source identifier of attachment['parents'] and grabs that title
  # then makes this attachments title 'page x for ' book title
  parent_title = None
  for row in reader:
    if row['source_identifier'] == attachment['parents']:
      parent_title = row['title']
      break

  if parent_title:
    page_number = attachment['sequence']
    attachment['title'] = f'Page {page_number}, {parent_title}'
  else:
    if verbose:
      print(f"Parent work for {attachment['source_identifier']} not found")

  #also adds the rdf type before returning, note to self this shouldn't have to be in here twice
  
  if "_hocr" in attachment['source_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['HOCR']
  elif "_ocr" in attachment['source_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['OCR']
  elif "_i" in attachment['file_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['Intermediate'] 
  elif "_p" in attachment['file_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['Preservation']
  elif "_transcript" in attachment['file_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['Transcript']
  else:
    attachment['rdf_type'] = RDF_TYPE_MAP['Access']

  return attachment

def main(input_file, output_file, attachments_given, verbose):
  with open(input_file, mode='r', encoding='utf-8-sig') as infile, open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    if verbose:
      print("Opening " + input_file + " as input file and " + output_file + " as output file")
      if attachments_given:
        print("Attachments given, only creating FileSet rows")

    # These columns headers will be added if they do not already exist, although they should always exist, mostly here for debugging
    additional_fields = ['source_identifier', 'title', 'model', 'parents', 'abstract', 'sequence', 'visibility', 'rdf_type', 'remote_files']
    fieldnames = reader.fieldnames
    # print(fieldnames)
    # reads all columns names and adds the ones that do not exist
    for field in additional_fields:
      if field not in fieldnames:
        if verbose:
          print(field + " column not provided, adding it")
        fieldnames.append(field)
    
    # Create a copy of fieldnames for the writer and remove 'file_identifier' from it, this is not efficient and could be cleaned up
    fieldnames_for_writer = fieldnames.copy()
    if 'file_identifier' in fieldnames_for_writer:
      fieldnames_for_writer.remove('file_identifier')

    writer = csv.DictWriter(outfile, fieldnames=fieldnames_for_writer)
    writer.writeheader()
    
    for row in reader:
      if row['model'] == "Attachment":
        if attachments_given:
          attachment = verify_attachment_row(row, verbose)
          # add the title to the book page for the attachment, TODO make this not so poorly written later
          # makes a new file reader every time we need to do this, this is bad
          with open(input_file, mode='r', encoding='utf-8-sig') as new_infile:
            new_reader = csv.DictReader(new_infile)
            attachment = add_title_to_book_page(attachment, new_reader, verbose)
          fileset = create_fileset_row(attachment, row, verbose)
            # Remove 'file_identifier' from rows before writing to the CSV outfile
          attachment = remove_file_identifier_column(attachment)
          fileset = remove_file_identifier_column(fileset)
          writer.writerow(attachment)
          writer.writerow(fileset)
        else:
          print("Attachments given but not specified, please use the -a flag if attachments are in the input file")
          exit(1)
      elif row['model'] == "FileSet":
        # Currently does nothing to the row if it is a fileset row
        if verbose:
          print("FileSet row read, skipping row")
      elif row['model'] == "Collection":
        # Currently does nothing to the row if it is a collection row
        if verbose:
          print("Collection row read, skipping row")
      else: # We can assume this row must be for a work
        if row['model'] == 'Book' or row['model'] == 'CompoundObject': # TODO apply appropriate sequence when this is true, if needed
          # needsSequence = True; something like this
          pass
        work = verify_work_row(row, verbose)
        if not attachments_given: # only create the attachment and fileset rows here if attachments are not provided
          attachment = create_attachment_row(work, verbose)
          fileset = create_fileset_row(attachment, work, verbose)
            # Remove 'file_identifier' from rows before writing to the CSV outfile
          work = remove_file_identifier_column(work)
          attachment = remove_file_identifier_column(attachment)
          fileset = remove_file_identifier_column(fileset)
          writer.writerow(work)
          writer.writerow(attachment)
          writer.writerow(fileset)
        else:
          work = remove_file_identifier_column(work)
          writer.writerow(work)
          continue


# attachments_given and verbose are by default false, if the flag is present they are set to true
# input file and output file flags are required and must be different files

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Generate CSV for attachments and filesets.')
  parser.add_argument('-i', '--input_file', type=str, help='Input CSV file with metadata')
  parser.add_argument('-o', '--output_file', type=str, help='Output CSV file with generated works, attachments, and filesets rows')
  parser.add_argument('-a', '--attachments_given', action='store_true', help='Flag to generate just filesets')
  parser.add_argument('-v', '--verbose', action='store_true', help='Flag to print out debug information')
  args = parser.parse_args()
  if not args.input_file or not args.output_file:
    print("Error: Both input_file and output_file arguments are required. Use --help to see help menu.")
    exit(1)
  if args.input_file == args.output_file:
    print("Error: Input file cannot be the same as output file. Use --help to see help menu")
    exit(1)
  main(args.input_file, args.output_file, args.attachments_given, args.verbose)

