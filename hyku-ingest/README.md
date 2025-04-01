# UTK ingest for Hyku

### Installing

Preferably use pipx to install this package
```
pipx install hyku-ingest
```
Then the program should be accessible from the `ingest` command.

### Usage

To list all commands run:
```
ingest --help
```

The basic command format is as follows:
```
ingest -o <output_filename> -i <input_filename> [optional flags]
```
Flags:
- `-i <input_sheet>, --input`: Required, Path to the input metadata sheet.
- `-o <output_sheet>, --output`: Required, Path to the output ingest sheet.
- `-a, --attachments_given`: Optional flag for when the attachment rows are provided, usually for books or compound objects
- `-v, --verbose`: Optional flag to print additional debug information to the command line
- `--audio_visual`: Optional flag to specify that this sheet will be audio visual works