
### `download_images.py`

File `client_secret.json` (placed in project root) is needed to access Google Drive, you can get one from
[Google APIs](https://console.developers.google.com/apis/credentials), especially
OAuth 2.0
Client IDs (with all Google Drive perms) for your own project.

## Downloading photos and preparing ESNcard data
Download form responses in .csv format. Then run the following command:

```
python3 ./download_images.py <downloaded_form_file>.csv
```

## Generating ESNcard print files

```
python3 generate.py
```
