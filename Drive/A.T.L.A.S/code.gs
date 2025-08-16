/**
 * ATLAS — Automated Template for Linked Accessed SharedDrives
 * BEFORE YOU RUN:
 * - Services → Add service (+) → Enable Drive API (v3)
 * - Deploy → Web app
 */

const ROLE_MAP = {
  owners: "organizer",   // Shared Drive "Manager"
  editors: "writer",
  viewers: "reader",
  commenters: "commenter",
};

function doGet() {
  return HtmlService.createTemplateFromFile("index")
    .evaluate()
    .setTitle("ATLAS • Automated Template for Linked Accessed SharedDrives");
}

/**
 * payload = {
 *   prefix: "PMO--"|"Finance--"|"Acq--",
 *   templateKey: "PMO"|"FINANCE"|"ACQ",
 *   driveNameInput: string,
 *   owners: string[],               // ≥1 and ≤2
 *   editors?: string[], viewers?: string[], commenters?: string[]
 * }
 */
function createSharedDriveAndFolders(payload) {
  const userEmail = Session.getActiveUser().getEmail();

  const prefix = (payload.prefix || "").trim();
  const templateKey = (payload.templateKey || "").toUpperCase();
  const suffix = (payload.driveNameInput || "").trim();
  if (!prefix) throw new Error("Prefix is required.");
  if (!suffix) throw new Error("Drive name (suffix) is required.");
  if (!templateKey) throw new Error("Template key is required.");

  const driveName = `${prefix}${suffix}`;

  // Owners: 1–2
  const owners = (payload.owners || []).map(s => (s || "").trim()).filter(Boolean);
  if (owners.length < 1 || owners.length > 2) {
    throw new Error("Please provide at least 1 and no more than 2 owner email addresses.");
  }

  // Optional roles
  const editors = dedupeEmails(payload.editors);
  const viewers = dedupeEmails(payload.viewers);
  const commenters = dedupeEmails(payload.commenters);

  // === Create Shared Drive ===
  const requestId = Utilities.getUuid();
  const newDrive = Drive.Drives.create({ name: driveName }, requestId);
  const driveId = newDrive.id;
  const driveUrl = `https://drive.google.com/drive/folders/${driveId}`;

  Utilities.sleep(1500); // settle

  // === Permissions (retry + small gaps) ===
  addPermissionsToSharedDrive(driveId, "owners", owners);
  Utilities.sleep(250);
  addPermissionsToSharedDrive(driveId, "editors", editors);
  Utilities.sleep(250);
  addPermissionsToSharedDrive(driveId, "viewers", viewers);
  Utilities.sleep(250);
  addPermissionsToSharedDrive(driveId, "commenters", commenters);

  // === Folders from template ===
  const folderNames = getFolderTemplate(templateKey);
  const folders = folderNames.map(name => {
    const id = createFolderInSharedDrive(driveId, name);
    return { name, url: `https://drive.google.com/drive/folders/${id}` };
  });

  // Email summary (best effort)
  const subject = `Shared Drive created: ${driveName}`;
  const body = [
    `Shared Drive created: ${driveName}`,
    `URL: ${driveUrl}`,
    ``,
    `Owners: ${owners.join(", ") || "None"}`,
    `Editors: ${editors.join(", ") || "None"}`,
    `Viewers: ${viewers.join(", ") || "None"}`,
    `Commenters: ${commenters.join(", ") || "None"}`,
    ``,
    `Folders:`,
    ...folders.map(f => ` - ${f.name}: ${f.url}`),
  ].join("\n");
  try { if (userEmail) MailApp.sendEmail(userEmail, subject, body); } catch (_) {}

  return { driveId, driveUrl, driveName, folders };
}

/** Folder templates */
function getFolderTemplate(templateKey) {
  switch (templateKey) {
    case "PMO":
      return [
        "01_Project Charter",
        "02_Requirements",
        "03_Project Plan & Schedule",
        "04_Design & Architecture",
        "05_Development",
        "06_Testing & QA",
        "07_Change Control",
        "08_Risks & Issues",
        "09_Stakeholder & Communications",
        "10_Status Reports",
        "11_Deliverables & Documentation",
        "12_Resources",
        "Archive"
      ];
    case "FINANCE":
      return [
        "01_Budgeting",
        "02_Forecasting",
        "03_Accounts Payable",
        "04_Accounts Receivable",
        "05_Payroll",
        "06_Expenses & Reimbursements",
        "07_Procurement",
        "08_Contracts & Vendors",
        "09_Reporting & Analytics",
        "10_Audit & Compliance",
        "11_Tax",
        "12_Month-End Close",
        "13_Year-End",
        "Policies & Procedures",
        "Archive"
      ];
    case "ACQ":
    default:
      return ["Folder 1", "Folder 2", "Folder 3", "Folder 4", "Folder 5"];
  }
}

/** Permissions with retries for transient errors */
function addPermissionsToSharedDrive(driveId, roleKey, emails) {
  const list = (emails || []).map(e => (e || "").trim()).filter(Boolean);
  if (!list.length) return;
  const role = ROLE_MAP[roleKey];

  list.forEach(email => {
    const permResource = { type: looksLikeGroup(email) ? "group" : "user", role, emailAddress: email };
    callWithRetries(() => {
      Drive.Permissions.create(permResource, driveId, {
        supportsAllDrives: true,
        sendNotificationEmail: false,
      });
    }, 5, 500);
  });
}

/** Create folder in Shared Drive root; return ID */
function createFolderInSharedDrive(driveId, folderName) {
  const fileMetadata = { name: folderName, mimeType: "application/vnd.google-apps.folder", parents: [driveId] };
  const file = Drive.Files.create(fileMetadata, null, { supportsAllDrives: true });
  return file.id;
}

/** Retry helper */
function callWithRetries(fn, maxAttempts, baseDelayMs) {
  let attempt = 0, lastErr;
  while (attempt < maxAttempts) {
    try { return fn(); }
    catch (err) {
      const msg = String(err && err.message ? err.message : err);
      if (!/Transient|Rate limit|Backend Error|Internal|503|500|retry/i.test(msg)) throw err;
      lastErr = err;
      Utilities.sleep(Math.pow(2, attempt) * baseDelayMs);
      attempt++;
    }
  }
  throw lastErr || new Error("Operation failed after retries.");
}

function dedupeEmails(arr) {
  const out = [], seen = new Set();
  (arr || []).forEach(e => { const v = (e || "").trim(); if (v && !seen.has(v)) { seen.add(v); out.push(v); } });
  return out;
}
function looksLikeGroup(email) {
  const val = (email || "").toLowerCase();
  return val.includes("group") || val.includes("-all");
}
