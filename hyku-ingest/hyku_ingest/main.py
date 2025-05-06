import argparse
from ingest import ingest
from split_sheet import split_sheet
import os

def create_sheet(args):
  if not args.input_file or not args.output_file:
    print("Error: Both input_file and output_file arguments are required. Use --help to see help menu.")
    exit(1)
  if args.input_file == args.output_file:
    print("Error: Input file cannot be the same as output file. Use --help to see help menu")
    exit(1)
  ingest(args.input_file, args.output_file, args.attachments_given, args.verbose, args.audio_visual)

def split_sheet_main(args):
  if not args.input_file:
    print("Error: input_file argument is required. Use --help to see help menu.")
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
  # hopefully this file is always empty, if not there are problems
  non_filesets_attachment_file = os.path.join(output_dir, f'{base_filename}_empty.csv')

  split_sheet(input_file, output_file_prefix, non_filesets_attachment_file, chunk_size)

def start():
  # Create the main argument parser and the regular flags for it
  # The main functionality will be creating ingeset sheets 
  parser = argparse.ArgumentParser(description='Generate CSV for attachments and filesets.')
  subparsers = parser.add_subparsers(help='subcommand help here')
  parser_create_sheet = subparsers.add_parser('create_sheet', help='Create ingest sheets from metadata files')
  parser_create_sheet.add_argument('-i', '--input_file', type=str, help='Input CSV file with metadata')
  parser_create_sheet.add_argument('-o', '--output_file', type=str, help='Output CSV file with generated works, attachments, and filesets rows')
  parser_create_sheet.add_argument('-a', '--attachments_given', action='store_true', help='Flag to generate just filesets')
  parser_create_sheet.add_argument('-v', '--verbose', action='store_true', help='Flag to print out debug information')

  #This flag could be removed if we just check the first work and if its av set this flag, will have to look into this more, for now this works
  parser_create_sheet.add_argument('--audio_visual', action='store_true', help='Flag to specify that these will be audio visual works')
  parser_create_sheet.set_defaults(func=create_sheet)

  parser_split_sheet = subparsers.add_parser('split_sheet', help='Split and sort a large ingest sheet into smaller files')
  parser_split_sheet.add_argument('-i', '--input_file', type=str, help='Input CSV file')
  parser_split_sheet.add_argument('-n', '--num_rows', type=str, help='The number of rows per file')
  parser_split_sheet.set_defaults(func=split_sheet_main)

  args = parser.parse_args()
  args.func(args)

# input file and output file flags are required and must be different files
if __name__ == "__main__":
  start()