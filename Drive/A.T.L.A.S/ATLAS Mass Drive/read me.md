# Atlas Mass Drive Creation (Google Apps Script Web App)

This project, Atlas Mass Drive Creation, is a Google Apps Script web application that automates the creation of Google Shared Drives and applies group permissions based on a configuration stored in a Google Sheet.  

Instead of manually creating drives and assigning groups, you simply prepare a Sheet, paste its link into the app, and the script does the rest.  
At the end of each run, you will receive an **email report** summarizing:
- Which drives were created (with links),
- Which permissions were successfully applied,
- Any failures or skipped rows.

---

## Features
- Creates Google Shared Drives in bulk.
- Assigns groups as Manager, Content Manager, Contributor, Commenter, Viewer.
- Handles multiple groups per role (comma-separated).
- Continues processing even if some groups fail.
- Emails a **summary report** (success, failures, skipped rows).

---

## Requirements
1. A Google Workspace account with permission to create Shared Drives.
2. Access to **Google Apps Script**.
3. Admin rights (or sufficient API privileges) to manage group permissions.

---

## Setup

1. **Open Google Apps Script**
   - Go to [https://script.google.com/](https://script.google.com/)  
   - Click **New Project**.
   - Paste in the provided `Code.gs` and `Index.html` files.

2. **Enable APIs**
   - In the Script Editor, click the **puzzle icon → Services**.
   - Enable **Drive API**.
   - In the linked Google Cloud Console, also enable the **Google Drive API**.

3. **Update Manifest Scopes**
   - Open **Project Settings → Show `appsscript.json` manifest file**.
   - Ensure the following scopes are present:
     ```json
     {
       "timeZone": "America/Chicago",
       "runtimeVersion": "V8",
       "oauthScopes": [
         "https://www.googleapis.com/auth/drive",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/script.send_mail",
         "https://www.googleapis.com/auth/userinfo.email"
       ]
     }
     ```

4. **Deploy the Web App**
   - Click **Deploy → Test deployments → Web app**.
   - Execute as: **Me**.
   - Who has access: **Only myself** (or expand to your domain if desired).
   - Copy the **Test Web App URL** and open it in a browser.

---

## Usage

1. Prepare a Google Sheet with the following headers (row 1):
                                      
- **Drive name** → the name of the Shared Drive to create.
- Other columns → group emails (comma-separated if multiple).

Example:

| Drive name         | Manager                  | Contributor            | Viewer        |
|--------------------|--------------------------|------------------------|---------------|
| Finance 2025       | managers@company.com     | staff@company.com      | auditors@ext.com |
| Project Phoenix    | phoenix-leads@company.com, auditors@ext.com | dev-team@company.com  |               |

2. Open the **Atlas Mass Drive Creation Web App** (the URL you deployed).
3. Paste the **Sheet URL or ID**.
4. (Optional) Provide:
- A **Sheet name** if your spreadsheet has multiple tabs.
- A **Report recipient email** (defaults to your account).
5. Click **Run Provisioning**.
6. Wait for the status message.  
You will receive an **email report** with links to the created drives and any errors.

---

## Notes
- If a group email cannot be found, the script logs it as a failure but continues.
- You must have sufficient privileges in Google Workspace to create Shared Drives and assign permissions.
- Emails are only sent if MailApp can resolve a valid recipient (default is the signed-in user).
- For bulk operations, limit to a few hundred rows to avoid quota issues.

---

## License
This project is open for internal or personal use. Customize as needed for your organization.

