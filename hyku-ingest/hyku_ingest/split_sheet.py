# splits one large csv into several csvs of length 10000
# also now splits up the attachments into their own sheets, and filesets into their own
# splits the big _visibility file, that should be the one with all the information
import csv
import sys
import os

# Change the chunk size down to 5000 if we want to keep doing these half size sheets, if not then keep it 10000
# This value used to be 2000 but that would've meant hundreds more sheets to import, so it was upped to 10000
# potentially decreased to 5000 just to see if overloading was an issue
def split_sheet(input_file, output_file_prefix, non_filesets_attachment_file, chunk_size=10000):
  with open(input_file, 'r') as csvfile:
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_sheet.py <input_csv>")
        sys.exit(1)

    input_file = sys.argv[1]
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.abspath(os.path.dirname(input_file))
    output_file_prefix = os.path.join(output_dir, f'{base_filename}_')
    # hopefully this file is always empty, if not there are problems
    non_filesets_attachment_file = os.path.join(output_dir, f'{base_filename}_empty.csv')

    split_sheet(input_file, output_file_prefix, non_filesets_attachment_file)