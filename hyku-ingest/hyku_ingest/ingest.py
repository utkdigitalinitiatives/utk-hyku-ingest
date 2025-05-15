from hyku_ingest.create_sheet import CreateSheet
from hyku_ingest.split_sheet import split_sheet

import argparse
import os
import csv

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
  cs = CreateSheet()
  cs.ingest_main(args.input_file, args.output_file, args.attachments_given, args.verbose, args.audio_visual)

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
  # hopefully this file is always empty, if not there are unexpected rows in the input file, most likely work and collection rows
  non_filesets_attachment_file = os.path.join(output_dir, f'{base_filename}_empty.csv')

  split_sheet(input_file, output_file_prefix, non_filesets_attachment_file, chunk_size)

def no_command(args):
  """
  Driver function for when no subcommand is given, currently just prints out some help information and exits.
  """
  print("No command given. Use `ingest -h` to see commands.")
  exit(1)

def start(): # the entry point for the command line interface
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