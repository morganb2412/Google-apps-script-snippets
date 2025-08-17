ATLAS

Automated Template for Linked Accessed SharedDrives

ATLAS is a Google Apps Script web application that  I created that streamlines the creation of Google Shared Drives using predefined templates. It allows organizations to quickly provision standardized folder structures, assign roles, and ensure consistency across teams and departments.

🚀 Features

Template-based Drive Creation

Choose from PMO, Finance, or Acquisitions templates.

Each template automatically provisions a structured set of folders tailored to the use case.

Customizable Drive Naming

Automatically applies a prefix (PMO--, Finance--, Acq--) with a user-defined suffix.

Access Control

Require 1–2 Owners (Managers).

Add an unlimited number of Editors, Viewers, and Commenters.

Supports both user accounts and Google Groups.

Automated Folder Generation

PMO: Common project lifecycle folders (Charter, Requirements, Testing, Deliverables, etc.).

Finance: Departmental folders (Budgeting, Payroll, Audit, etc.).

Acquisitions: General placeholder folders (Folder1, Folder2, Folder3, etc.).

Email Notifications

Automatically emails the creator with the new Drive details and folder links.

Modern UI

Dark mode design with a purple-to-blue gradient.

Simple navigation to select templates.

Planned light/dark theme toggle for accessibility.

🛠️ Tech Stack

Google Apps Script: Core logic, Drive API, Permissions, Email.

HTML/CSS/JS: User interface and navigation.

Google Drive API (v3): Shared Drive + folder creation.

📋 How It Works

From the home page, choose a template (PMO, Finance, Acquisitions).

Fill in the form with:

Drive name suffix.

Owner(s), editors, viewers, and commenters.

ATLAS automatically:

Creates the Shared Drive with the proper prefix.

Assigns permissions.

Creates the template folder structure.

Emails you a summary with links.

📦 Installation

Open Google Apps Script.

Create a new project and add these files:

Code.gs
index.html (PMO)



Enable the Google Drive API v3 in:

Services (inside Apps Script → Services → Drive API).

Google Cloud Console (enable Drive API).

Deploy as a Web App with access set to your org.

Roadmap

✅ PMO & Finance folder templates

✅ Role-based permissions

✅ Modern UI (dark mode)

🔲 Light/dark theme toggle

🔲 Admin dashboard for usage tracking

🤝 Contributing

Contributions are welcome!

Fork the repo

Create a feature branch

Submit a pull request with details

📧 Contact

Built by Morgan Brown
Morganbrown2412@gmail.com
For questions, reach out on LinkedIn (https://www.linkedin.com/in/morgan-brown-3a0353199/) or open an issue in the repo.
