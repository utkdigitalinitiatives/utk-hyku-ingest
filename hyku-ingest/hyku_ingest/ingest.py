import csv

RDF_TYPE_MAP = {
  'Preservation': 'http://pcdm.org/use#PreservationFile', # will have _p at end of file_identifier
  'Intermediate': 'http://pcdm.org/use#IntermediateFile', # will have _i at end of file_identifier
  'Access': 'http://pcdm.org/use#ServiceFile',            # will be .mp3 .jpg, possibly .mp4 but not sure yet
  'HOCR': 'http://pcdm.org/file-format-types#HTML',       # only applies to books?, has _hocr 
  'PDF': 'http://pcdm.org/file-format-types#Document',    # if model is pdf 
  'Transcript': 'http://pcdm.org/use#Transcript',         # will have _transcript at end of file_identifier
  'OCR': 'http://pcdm.org/use#ExtractedText',             # only applies to books, has _ocr
}

RESTRICTED_TITLES = { # TODO titles are slightly different now so this will need to change
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

HAS_WORK_TYPE_MAP = {
    "Audio": "https://ontology.lib.utk.edu/works#AudioWork",
    "Book": "https://ontology.lib.utk.edu/works#BookWork ",
    "CompoundObject": "https://ontology.lib.utk.edu/works#CompoundObjectWork ",
    "Generic": "https://ontology.lib.utk.edu/works#GenericWork ",
    "Image": "https://ontology.lib.utk.edu/works#ImageWork ",
    "Pdf": "https://ontology.lib.utk.edu/works#PDFWork ",
    "Video": "https://ontology.lib.utk.edu/works#VideoWork "
}

# Given a work row, does any edits/checks needed to the row and returns it
def verify_work_row(work, verbose):
  if 'has_work_type' not in work:
    if work['model'].lower() in HAS_WORK_TYPE_MAP:
      work['has_work_type'] = HAS_WORK_TYPE_MAP[work['model'].lower()]
    else:
      work['has_work_type'] = HAS_WORK_TYPE_MAP["Generic"]
  if ' ' in work['source_identifier']:
    if verbose:
      print("removing spaces from source_identifier")
    work['source_identifier'] = work['source_identifier'].strip()
    work['source_identifier'] = work['source_identifier'].replace(' ', '_')
  work['primary_identifier'] = work['source_identifier']
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
#   work - This is a dict containing the work row that this attachment will be associated with
#   verbose - T/F value to print out extra debug info
#   av - optional, default is None, for specifying if this attachment should be the first (1) or second (2) for a given audio visual work
def create_attachment_row(work, verbose=False, av=None):
  if work['model'].lower() == 'image':                # Special case for images
    title = f"Image for {work['source_identifier']}"
  elif av == 2:                                       # Special case for audio visual files
    title = f"Transcript for {work['title']}"
  else:                                               # Generic title format
    title = f"{work['model']} for {work['title']}"
  
  # Ensures that file identifier only has one dot
  if work['file_identifier'].count('.') >= 2:
    print(f"File identifier, {work["file_identifier"]} , for work {work['source_identifier']} has 2 or more periods, may cause errors")
    # may want to exit here, leaving it to just print error for now

  # Finds the correct RDF type from the file identifier
  if work['model'].lower() == 'pdf':
    rdf = RDF_TYPE_MAP['PDF']
  elif "_i." in work['file_identifier']:
    rdf = RDF_TYPE_MAP['Intermediate'] 
  elif "_p." in work['file_identifier']:
    rdf = RDF_TYPE_MAP['Preservation']
  elif "_transcript." in work['file_identifier']:
    rdf = RDF_TYPE_MAP['Transcript']
  elif "_ocr." in work['file_identifier']:
    rdf = RDF_TYPE_MAP['OCR']
  elif "_hocr." in work['file_identifier']:
    rdf = RDF_TYPE_MAP['HOCR']
  elif ".jpg" in work['file_identifier'] or ".mp3" in work['file_identifier']:
    rdf = RDF_TYPE_MAP['Access']
  else:
    rdf = ""
  
  # This is the special case for the second attachment from a single av work, which should always just be a transcript
  if av == 2:
    rdf = RDF_TYPE_MAP['Transcript']
  
  # Handle special case for source id of av work
  if av == 2:
    source_id = work['source_identifier'] + '_transcript_attachment'
  else:
    source_id = work['source_identifier'] + '_attachment'

  # checks if the title is in the list of restricted titles and sets visibility accordingly, default is open
  # TODO see todo for RESTRICTED_TITLES dict definition 
  vis = VISIBILITY_TYPE_MAP[0]
  if title in RESTRICTED_TITLES:
    vis = VISIBILITY_TYPE_MAP[1]

  # this defines everything in the attachment row
  attachment = {
    'source_identifier': source_id,
    'primary_identifier': source_id,
    'title': title,
    'model': 'Attachment',
    'parents': work['source_identifier'],
    'visibility': vis,
    'rdf_type': rdf,
    'has_work_type': work['has_work_type']
  }
  return attachment


# Given an attachment row, returns a fileset row with all data filled in
# Everything is essentially copied from attachment row with minor changes
# remote files will add _transcript before the file extension when av = 2, since the work will just define the first of the two av files
# work is needed for correct source_identifier and getting the file_identifier
def create_fileset_row(attachment, work, verbose, av=None):
  # this defines everything in the fileset row
  fileset = {
    'source_identifier': work['source_identifier'] + '_fileset',
    'primary_identifier': work['source_identifier'] + '_fileset',
    'title': attachment['title'],
    'model': 'FileSet',
    'parents': attachment['source_identifier'],
    'visibility': attachment.get('visibility', 'open'),
    'sequence': attachment.get('sequence', ''),
    'rdf_type': attachment['rdf_type'],
    'has_work_type': attachment['has_work_type'],
    'remote_files': f"http://hykuimports.lib.utk.edu/files/hyku-import/{work['file_identifier'] if not (av==2) else append_transcript(work['file_identifier'])}"
  }
  return fileset

# Takes a file identifier and attempts to put _transcript right before the file extension
# this is just used for the special case that the works are av
def append_transcript(file_id):
  parts = file_id.rsplit('.', 1)
  if len(parts) == 2:
    return f"{parts[0]}_transcript.{parts[1]}"
  else:
    print(f"Issue with adding transcript to remote file \"{file_id}\"")
    return file_id

#:TODO: this does not need to be its own function, but this works for now
def remove_file_identifier_column(row):
  if 'file_identifier' in row:
    del row['file_identifier']
  return row

# This creates the titles and sets the rdf type for the book pages attachment rows, will return the modified attachment row dict
# takes a new reader to find this attachment's parent from infile, there is probably a better way to do this
def add_title_to_book_page(attachment, reader, verbose):
  # If there is a title already there, then do nothing
  if attachment['title'] != "":
    return attachment
  parent_title = None
  for row in reader:
    if row['source_identifier'] == attachment['parents']:
      parent_title = row['title']
      break

  if parent_title:
    page_number = attachment['sequence']
    attachment['title'] = f'Page {page_number}, {parent_title}'
  else:
    # Not sure when this could happen, but if it does something is most likely very wrong
    print(f"Parent work for {attachment['source_identifier']} not found")

  if attachment['source_identifier'].count('.') >= 2:
    print(f"Source identifier for {attachment['source_identifier']} has 2 or more periods, may cause errors")
    # may want to exit here, leaving it to just print error for now

  # Adding the rdf type to the row
  if "_hocr." in attachment['source_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['HOCR']
  elif "_ocr." in attachment['source_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['OCR']
  elif "_i." in attachment['file_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['Intermediate'] 
  elif "_p." in attachment['file_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['Preservation']
  elif "_transcript." in attachment['file_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['Transcript']
  elif ".jpg" in attachment['file_identifier'] or ".mp3" in attachment['file_identifier']:
    attachment['rdf_type'] = RDF_TYPE_MAP['Access']
  else:
    attachment['rdf_type'] = ""

  return attachment

def ingest(input_file, output_file, attachments_given, verbose, audio_visual):
  with open(input_file, mode='r', encoding='utf-8-sig') as infile, open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    reader = csv.DictReader(infile)
    if verbose:
      print("Opening " + input_file + " as input file and " + output_file + " as output file")
      if attachments_given:
        print("Attachments given, only creating FileSet rows")
    # Check if the input file is empty
    if not reader.fieldnames:
      print("Input file is empty. Exiting.")
      exit(1)
    fieldnames = reader.fieldnames
    required_fieldnames = ['source_identifier','model','visibility','remote_files','parents','file_identifier','title','sequence','abstract']
    for field in required_fieldnames: # these should be the fieldnames required on the input file
      if field not in reader.fieldnames:
        print(f"Required column {field} not found, exiting")
        exit(1)
    # These columns headers will be added if they do not already exist, although they should always exist, mostly here for debugging
    additional_fieldnames = ['source_identifier', 'primary_identifier', 'title', 'model', 'parents', 'abstract', 'sequence', 'visibility', 'rdf_type', 'remote_files', 'has_work_type']
    # reads all columns names and adds the ones that do not exist
    for field in additional_fieldnames:
      if field not in fieldnames:
        if verbose:
          print(field + " column not provided, adding it")
        fieldnames.append(field)
    # Create a copy of fieldnames for the writer and remove 'file_identifier' from it, TODO: this is not efficient and could be cleaned up
    fieldnames_for_writer = fieldnames.copy()
    if 'file_identifier' in fieldnames_for_writer:
      fieldnames_for_writer.remove('file_identifier')

    writer = csv.DictWriter(outfile, fieldnames=fieldnames_for_writer)
    writer.writeheader()
    
    # not a huge fan of how nested the if statements are here, could get out of hand and unreadable, may rework logic flow later
    for row in reader:
      if row['model'] == "Attachment":
        if attachments_given:
          if audio_visual: # attachments given for audio visual not currently supported, shouldn't be hard to add if needed
            print("Unsure if this will ever happen, erroring for now if it does")
            exit(1) 
          attachment = verify_attachment_row(row, verbose)
          # Adds title and rdf type for book page attachment rows, TODO: make this not so poorly written later
          # makes a new file reader every time we need to do this, this is bad
          with open(input_file, mode='r', encoding='utf-8-sig') as new_infile:
            new_reader = csv.DictReader(new_infile)
            attachment = add_title_to_book_page(attachment, new_reader, verbose)
          fileset = create_fileset_row(attachment, row, verbose)
          
          # Removes 'file_identifier' from rows before writing to the CSV outfile
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
        work = verify_work_row(row, verbose)
        if row['model'] == 'Book' or row['model'] == 'CompoundObject':
          if not attachments_given:
            print("Attachments given not specified, book/compound detected, most likely an error")
            exit(1)
        if audio_visual: # this is the special case of audio visual works, untested but should work in principal
          if attachments_given: # attachments given for audio visual not currently supported, shouldn't be hard to add if needed
            print("Unsure if this will ever happen, erroring for now if it does")
            exit(1)
          # Creates the 2 attachments and 2 filesets needed for each av work
          attachment_1 = create_attachment_row(work, verbose, 1)
          attachment_2 = create_attachment_row(work, verbose, 2)
          fileset_1 = create_fileset_row(attachment_1, work, verbose)
          fileset_2 = create_fileset_row(attachment_2, work, verbose)
          # Removes the file id column from everything related to this work
          work = remove_file_identifier_column(work)
          attachment_1 = remove_file_identifier_column(attachment_1)
          attachment_2 = remove_file_identifier_column(attachment_2)
          fileset_1 = remove_file_identifier_column(fileset_1)
          fileset_2 = remove_file_identifier_column(fileset_2)
          # Writes 5 lines to outfile, the work, both attachments, and both filesets
          writer.writerow(work)
          writer.writerow(attachment_1)
          writer.writerow(attachment_2)
          writer.writerow(fileset_1)
          writer.writerow(fileset_2)
          # goes to the next row in the infile
          continue
        if not attachments_given: # will create and write attachment and fileset rows, and write modified work row
          attachment = create_attachment_row(work, verbose)
          fileset = create_fileset_row(attachment, work, verbose)
          # Remove 'file_identifier' from rows before writing to the CSV outfile
          work = remove_file_identifier_column(work)
          attachment = remove_file_identifier_column(attachment)
          fileset = remove_file_identifier_column(fileset)
          # Writing to the outfile
          writer.writerow(work)
          writer.writerow(attachment)
          writer.writerow(fileset)
        else: # Since attachments are given here, just remove file id and write work row
          work = remove_file_identifier_column(work)
          writer.writerow(work)
          continue
