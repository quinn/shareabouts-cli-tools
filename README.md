shareabouts-cli-tools
=====================

After you checkout shareabouts-cli-tools, you can run the upload script like:

./upload_geojson.py <config_file>

In your config, set the owner, dataset, key, and source_file, and possibly the fields. 

If you want to use all the fields, then just omit the fields value completely.

When uploading point data from csv, make sure you have fields for `id`, `lat`, `lon`.

