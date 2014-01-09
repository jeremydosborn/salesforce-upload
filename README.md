salesforce-upload
=================

Merge files for upload into Salesforce with Python.

This is not a generic program, and is actually more or less obsolete now due to a great new tool called dataloader.io. When we built this in 2011 Salesforce still had a weak API for integrating third party data.

Still, if you are doing something custom that involves merging multiple .csv files into a single, hierarchical Salesforce data model, you may find some inspiration here.

Here is how it works:

1. Index.html posts two .csv files in a specific format to webmerge.py
2. Webmerge.py then does some data validation and error checking and shows differences from the last upload.
3. Calls merge.py to merge the files, and return them to webmerge.py.
4. Prints the results to file for uplading into Salesforce, and displays results in the browser

