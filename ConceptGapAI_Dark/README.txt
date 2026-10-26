CONCEPTGAP AI — DEPLOYMENT-READY STARTER

WHAT IS INCLUDED
- Dark responsive homepage and library
- Search and filters for branch, pattern, year, semester, and resource type
- Admin login, resource links, file upload and delete
- PDF, DOC, DOCX, PPT, PPTX, TXT uploads up to 15 MB
- Render deployment configuration (render.yaml)

PUBLISH ONLINE (NO CODE CHANGES REQUIRED)
1. Sign in to GitHub and create a NEW repository named ConceptGapAI. Public or private is okay.
2. Extract this ZIP on your computer.
3. Open the repository on GitHub, choose Add file > Upload files, and upload the CONTENTS of the extracted ConceptGapAI_Dark folder (app.py, render.yaml, requirements.txt, templates folder, static folder, README.txt). Commit the upload.
4. Sign in to Render and choose New > Blueprint.
5. Connect GitHub and select the ConceptGapAI repository. Render will read render.yaml.
6. When prompted for ADMIN_USERNAME, choose your admin username. For ADMIN_PASSWORD, use a long unique password; do not share it. CONCEPTGAP_SECRET_KEY is generated automatically.
7. Deploy. When the deploy finishes successfully, open the onrender.com URL shown in the Render dashboard. That is your public website link.

IMPORTANT HOSTING / STORAGE NOTE
This Blueprint uses Render's free web service to make initial publishing easier. Free service files are temporary: the SQLite database and uploaded files can be lost on restarts or redeploys. For durable admin uploads, attach a persistent disk on a plan that supports it, mount it at /data, and set DATA_DIR=/data in the service environment. Back up important files. A persistent disk may require a paid plan.

ADMIN PAGE
Open https://YOUR-SITE-URL/admin/login and sign in with the credentials you set in Render.
Do not use the old development password on a public site. If the database was initialized before changing credentials, use a fresh deployment database or update the admin account securely.

LOCAL TEST
python -m pip install -r requirements.txt
python app.py
Then open http://127.0.0.1:5000

NOTES
- This starter does not automatically include official SBTET question papers; upload files or add verified source URLs through the admin page.
- It does not include a live AI recommendation engine or quiz system yet.
- Do not upload private student information or copyrighted material unless you have permission.
