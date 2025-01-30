# utk-hyku-ingest
Tool for creating full Bulkrax ingest sheets from given metadata sheets. Currently tested with Python 3.13.1, should work on later versions as well.

## Example Usage
```bash
python utk_hyku_ingest.py -i input_metadata_sheet.csv -o output_ingest_sheet.csv -a -v
```
This will use input_metadata_sheet.csv as the input sheet, and will create output_ingest_sheet.csv as an output sheet, and will expect the attachment rows to be given (-a), and will print out extra debugging information (-v).

### Arguments
- `-i <input_sheet>, --input`: Required, Path to the input metadata sheet.
- `-o <output_sheet>, --output`: Required, Path to the output ingest sheet.
- `-a, --attachments_given`: Optional flag for when the attachment rows are provided, usually for books or compound objects
- `-v, --verbose`: Optional flag to print additional debug information to the command line
- `--audio_visual`: Optional flag to specify that this sheet will be audio visual works