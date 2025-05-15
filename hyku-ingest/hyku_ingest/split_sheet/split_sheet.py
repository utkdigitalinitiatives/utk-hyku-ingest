import os
import csv

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