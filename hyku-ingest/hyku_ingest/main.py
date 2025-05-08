import argparse
import os
import csv

# ======== start of ingest code ========

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

def verify_work_row(work, verbose=False):
  """Does any edits or checks to given work row, currently fixes has_work_type field, removes whitespace from source_identifier, and copies over primary identifier.

  Args:
      work (dict): The work row that will be verified and fixed
      verbose (bool, optional): Option to print out extra debug information. Defaults to False.

  Returns:
      dict: The work row after any edits or fixes
  """
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
  if work['rdf_type'] == "":
    if work['model'].lower() == 'pdf':
      work['rdf_type'] = RDF_TYPE_MAP['PDF']
    elif "_i." in work['file_identifier']:
      work['rdf_type'] = RDF_TYPE_MAP['Intermediate'] 
    elif "_p." in work['file_identifier']:
      work['rdf_type'] = RDF_TYPE_MAP['Preservation']
    elif "_transcript." in work['file_identifier']:
      work['rdf_type'] = RDF_TYPE_MAP['Transcript']
    elif "_ocr." in work['file_identifier']:
      work['rdf_type'] = RDF_TYPE_MAP['OCR']
    elif "_hocr." in work['file_identifier']:
      work['rdf_type'] = RDF_TYPE_MAP['HOCR']
    elif ".jpg" in work['file_identifier'] or ".mp3" in work['file_identifier'] or ".jp2" in work["file_identifier"]:
      work['rdf_type'] = RDF_TYPE_MAP['Access']
    else:
      work['rdf_type'] = "" # default rdf type is currently nothing
  return work

def verify_attachment_row(attachment, verbose=False):
  """Does any edits or checks to given attachment row, currently sets correct rdf_type, copies over primary_identifier, and removes whitespace from source_identifier.

  Args:
    attachment (dict): Attachment row as a dictionary that you want to edit/check
    verbose (bool, optional): Option to print out extra debug information. Defaults to False.

  Returns:
    dict: A dictionary of the attachment row with any fixes done
  """
  if ' ' in attachment['source_identifier']:
    if verbose:
      print("removing spaces from source_identifier")
    attachment['source_identifier'] = attachment['source_identifier'].strip()
    attachment['source_identifier'] = attachment['source_identifier'].replace(' ', '_')
  attachment['primary_identifier'] = attachment['source_identifier']
  
  # adding the rdf type if it is not already present
  if attachment['rdf_type'] == "":
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
    elif ".jpg" in attachment['file_identifier'] or ".mp3" in attachment['file_identifier'] or ".jp2" in attachment["file_identifier"]:
      attachment['rdf_type'] = RDF_TYPE_MAP['Access']
    else:
      attachment['rdf_type'] = ""
  
  return attachment

def create_attachment_row(work, verbose=False, av=None):
  """Creates an attachment row from a given work row

  Args:
    work (dict): The work row to create the attachment row from as a dictionary.
    verbose (bool, optional): Option to print out extra debug information. Defaults to False
    av (int, optional): Represents how to handle audio visual works. None for not av, 1 for first attachment of av, 2 for transcript attachment for av. Defaults to None
  
  Returns:
    dict: A dictionary representation of the attachment row
  """
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
  elif ".jpg" in work['file_identifier'] or ".mp3" in work['file_identifier'] or ".jp2" in work["file_identifier"]:
    rdf = RDF_TYPE_MAP['Access']
  else:
    rdf = "" # default rdf type is currently nothing
  
  # Special case for the second attachment from a single av work, which should always be a transcript
  if av == 2:
    rdf = RDF_TYPE_MAP['Transcript']
    source_id = work['source_identifier'] + '_transcript_attachment'
  else:
    source_id = work['source_identifier'] + '_attachment'

  # checks if the title is in the list of restricted titles and sets visibility accordingly, default is open
  # TODO see todo for RESTRICTED_TITLES dict definition 
  vis = VISIBILITY_TYPE_MAP[0]
  if title in RESTRICTED_TITLES:
    vis = VISIBILITY_TYPE_MAP[1]

  # Builds the final attachment row dictionary
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

def create_fileset_row(attachment, work, verbose, av=None):
  """Creates and returns a fileset row with all of the data filled in, most of the data is copied from the attachment

  Args:
      attachment (dict): The attachment row to build this fileset from
      work (dict): The associated work row for getting the source_identifier and file_identifier
      verbose (bool): Option to print out extra debug information
      av (int, optional): Option for specifying audio visual row, 2 will add _transcript before the file extension. Defaults to None.

  Returns:
      dict: The finished fileset row with all correct metadata filled in
  """
  # Builds the final fileset row dictionary
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

def append_transcript(file_id):
  """Puts '_transcript' before the file extension for av filesets for the remote_files section

  Args:
      file_id (string): The file_identifier from the original work row

  Returns:
      string: The new file_identifier with '_transcript' added before the file extension
  """
  parts = file_id.rsplit('.', 1)
  if len(parts) == 2:
    return f"{parts[0]}_transcript.{parts[1]}"
  else:
    print(f"Issue with adding transcript to remote file \"{file_id}\"")
    return file_id

def remove_file_identifier_column(row):
  """Helper function to remove the file_identifier column from a row dictionary.

  Args:
      row (dict): The row you want to remove the column from.

  Returns:
      dict: The row dictionary with the file_identifier column removed.
  """
  if 'file_identifier' in row:
    del row['file_identifier']
  return row

def add_title_to_book_page(attachment, reader, verbose=False):
  """Sets the title field for book page attachments. Uses the parent's title and sequence to build correct page title. Also sets the correct rdf_type.

  Args:
      attachment (dict): The book page attachment row to make edits to.
      reader (DictReader): A file reader for the infile to use for finding this attachment's parent.
      verbose (bool, optional): Option to print out extra debug information. Defaults to False.

  Returns:
      dict: The attachment row with the title and rdf_type fields set correctly.
  """

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
  elif ".jpg" in attachment['file_identifier'] or ".mp3" in attachment['file_identifier'] or ".jp2" in attachment["file_identifier"]:
    attachment['rdf_type'] = RDF_TYPE_MAP['Access']
  else:
    attachment['rdf_type'] = ""

  return attachment

def ingest_main(input_file, output_file, attachments_given, verbose, audio_visual):
  """The main function that is called from the create_sheet driver function, these parameters match the command line arguments for create_sheet.
  This function is what will do all of the processing of the data and writing to the outfiles. 

  Args:
      input_file (srt): The filename of the input file.
      output_file (str): The filename of the desired output file.
      attachments_given (bool): Option for if attachment rows should be expected in the input file
      verbose (bool): Option to print out extra debug information.
      audio_visual (bool): Option for if this file contains all audio visual works. 
  """
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
    
    # Main for loop that reads every row in the infile and processes it
    for row in reader:
      if row['model'] == "Attachment":
        if attachments_given:
          if audio_visual: # attachments given for audio visual not currently supported, shouldn't be hard to add if needed
            print("Attachments given for audio visual works. Unexpected, exiting.")
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
            print("Attachments given not specified, book/compound detected. Use the -a flag if attachments are in the input file.")
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
# ======== end of ingest code ===============

# ======== start of split sheet code =========
def split_sheet(input_file, output_file_prefix, non_filesets_attachment_file, chunk_size):
  """Splits a given input sheet into filesets and attachments, then splits those into files with a max number of rows.

  Args:
      input_file (str): The filename of the input file. This is the file that will be split up, this file itself will not be changed.
      output_file_prefix (str): A string to start every newly created file with, is usually just the input file without the file extension.
      non_filesets_attachment_file (str): Filename of the file where any miscellaneous rows will go. This file should be empty.
      chunk_size (int): Maximum number of rows that each file can have, excluding the header row.
  """
  with open(input_file, 'r') as csvfile:
    if os.stat(input_file).st_size == 0:
      print("Input file is empty. Exiting.")
      exit(1)
    reader = csv.reader(csvfile)
    header = next(reader)

    non_filesets_attachment_rows = []
    fileset_rows = []
    attachment_rows = []

    #### Assumes model is in the second column
    # makes the fileset and attachment row arrays for easy use
    # stores the other rows as well but there should never be other rows
    for row in reader:
      if row[1].lower() == 'fileset':
        fileset_rows.append(row)
      elif row[1].lower() == 'attachment':
        attachment_rows.append(row)
      else:
        non_filesets_attachment_rows.append(row)

    # writes the file that should be empty, just for sanity purposes
    with open(non_filesets_attachment_file, 'w', newline='') as non_filesets_attachment_csv:
      writer = csv.writer(non_filesets_attachment_csv)
      writer.writerow(header)
      writer.writerows(non_filesets_attachment_rows)

    # writes the fileset row files, one chunk at a time
    for i in range(0, len(fileset_rows), chunk_size):
      chunk = fileset_rows[i:i + chunk_size]
      output_file = f"{output_file_prefix}fileset_{i // chunk_size}.csv"
      with open(output_file, 'w', newline='') as chunk_csv:
        writer = csv.writer(chunk_csv)
        writer.writerow(header)
        writer.writerows(chunk)

    # writes the attachment row files, one chunk at a time
    for i in range(0, len(attachment_rows), chunk_size):
      chunk = attachment_rows[i:i + chunk_size]
      output_file = f"{output_file_prefix}attachment_{i // chunk_size}.csv"
      with open(output_file, 'w', newline='') as chunk_csv:
        writer = csv.writer(chunk_csv)
        writer.writerow(header)
        writer.writerows(chunk)
# ======== End of split sheet code =========

# ======== Driver functions ================
def create_sheet(args):
  """Driver function for the create_sheet command line option, will parse command line arguments and run ingest_main.

  Args:
      args (args): A namespace of the command line arguments.
  """
  if not args.input_file or not args.output_file:
    print("Error: Both input_file and output_file arguments are required. Use `ingest create_sheet -h` to see help menu.")
    exit(1)
  if args.input_file == args.output_file:
    print("Error: Input file cannot be the same as output file. Use `ingest create_sheet -h` to see help menu")
    exit(1)
  ingest_main(args.input_file, args.output_file, args.attachments_given, args.verbose, args.audio_visual)

def split_sheet_main(args):
  """Driver function for the split_sheet command line option, will parse command line arguments and run split_sheet.

  Args:
      args (args): A namespace of the command line arguments.
  """
  if not args.input_file:
    print("Error: input_file argument is required. Use `ingest split_sheet -h` to see help menu.")
    exit(1)
  if not args.num_rows:
    print("No number of rows set, using default of 10000")
    chunk_size = 10000
  else:
    chunk_size = args.num_rows
  
  input_file = args.input_file
  base_filename = os.path.splitext(os.path.basename(input_file))[0]
  output_dir = os.path.abspath(os.path.dirname(input_file))
  output_file_prefix = os.path.join(output_dir, f'{base_filename}_')
  # hopefully this file is always empty, if not there are unexpected rows in the input file
  non_filesets_attachment_file = os.path.join(output_dir, f'{base_filename}_empty.csv')

  split_sheet(input_file, output_file_prefix, non_filesets_attachment_file, chunk_size)

def no_command(args):
  """Driver function for when no subcommand is given, currently just prints out some help information and exits.

  Args:
      args (args): Nothing is done with these command line args.
  """
  print("No command given. Use `ingest -h` to see commands.")
  exit(1)

def start():
  """
  This is the function that gets run when this package is installed and you run the command `ingest`. This behavior is defined in the pyproject.toml
  """
  
  # Create the main argument parser and add the subparsers for each different command
  parser = argparse.ArgumentParser(description='Tools for creating and manipulating ingest spreadsheets')
  parser.set_defaults(func=no_command)
  subparsers = parser.add_subparsers(help='The subcommands are as follows: ')

  # Creating the subparser for the main functionality - create_sheet
  parser_create_sheet = subparsers.add_parser('create_sheet', help='Create ingest sheets from metadata files')
  parser_create_sheet.add_argument('-i', '--input_file', type=str, help='Input CSV file with metadata')
  parser_create_sheet.add_argument('-o', '--output_file', type=str, help='Output CSV file with generated works, attachments, and filesets rows')
  parser_create_sheet.add_argument('-a', '--attachments_given', action='store_true', help='Flag to generate just filesets')
  parser_create_sheet.add_argument('-v', '--verbose', action='store_true', help='Flag to print out debug information')
  parser_create_sheet.add_argument('--audio_visual', action='store_true', help='Flag to specify that these will be audio visual works') # probably don't need this, keeping it for now
  parser_create_sheet.set_defaults(func=create_sheet)

  # Creating the subparser for the split_sheet functionality
  parser_split_sheet = subparsers.add_parser('split_sheet', help='Split and sort a large ingest sheet into smaller files')
  parser_split_sheet.add_argument('-i', '--input_file', type=str, help='Input CSV file')
  parser_split_sheet.add_argument('-n', '--num_rows', type=str, help='The number of rows per file')
  parser_split_sheet.set_defaults(func=split_sheet_main)

  # collect the arguments and run the entered subparser's function
  args = parser.parse_args()
  args.func(args)


if __name__ == "__main__":
  start()