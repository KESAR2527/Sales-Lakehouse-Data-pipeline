# Upload to GitHub

1. Extract the downloaded ZIP. Open the `cloud-data-engineering-capstone` folder.
2. Run `python pipeline.py` (or `py pipeline.py` on Windows).
3. Open `output/dashboard.html` and check that it shows 20 raw rows, 15 valid orders, 5 rejected rows and ₹87,000.00 revenue.
4. Sign in at https://github.com and create a new repository named `cloud-data-engineering-capstone`. Choose visibility according to your course requirements. Never upload private data or passwords.
5. On the empty repository page, choose the link to upload an existing file. If a README already exists, choose **Add file → Upload files**.
6. Drag the CONTENTS of the extracted project folder into the upload area. Include `pipeline.py`, README, dataset and the `output` folder. Do not upload only the ZIP. Exclude `__pycache__` if running Python created it.
7. Commit the uploaded files. Confirm `README.md` and `pipeline.py` appear at the repository root and folders are preserved.
8. Copy your repository's address and use it as the project link, if your course accepts this type of project. Leave an optional live-demo field blank: the dashboard is an offline file, not a hosted demo.

Suggested repository description:

> Local Bronze–Silver–Gold sales data pipeline using Python and SQLite, with data quality checks and an offline analytics dashboard.

If the course requires S3, Glue, Athena or BigQuery execution, this local repository alone does not satisfy that requirement. Review the actual instructions before submission.
