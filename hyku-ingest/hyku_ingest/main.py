import argparse
from ingest import ingest
from split_sheet import split_sheet

def start():
  # Create the main argument parser and the regular flags for it
  # The main functionality will be creating ingeset sheets 
  parser = argparse.ArgumentParser(description='Generate CSV for attachments and filesets.')
  parser.add_argument('-i', '--input_file', type=str, help='Input CSV file with metadata')
  parser.add_argument('-o', '--output_file', type=str, help='Output CSV file with generated works, attachments, and filesets rows')
  parser.add_argument('-a', '--attachments_given', action='store_true', help='Flag to generate just filesets')
  parser.add_argument('-v', '--verbose', action='store_true', help='Flag to print out debug information')
  subparsers = parser.add_subparsers(help='subcommand help here')
  parser_a = subparsers.add_parser('split_sheet', help='a help')



  #This flag could be removed if we just check the first work and if its av set this flag, will have to look into this more, for now this works
  parser.add_argument('--audio_visual', action='store_true', help='Flag to specify that these will be audio visual works')
  args = parser.parse_args()
  if not args.input_file or not args.output_file:
    print("Error: Both input_file and output_file arguments are required. Use --help to see help menu.")
    exit(1)
  if args.input_file == args.output_file:
    print("Error: Input file cannot be the same as output file. Use --help to see help menu")
    exit(1)
  ingest(args.input_file, args.output_file, args.attachments_given, args.verbose, args.audio_visual)

# input file and output file flags are required and must be different files
if __name__ == "__main__":
  start()