/**
 * Shared Drive Provisioner — Simple Version
 * Reads a Google Sheet and creates Shared Drives with group permissions.
 * Results are sent in an email report only.
 */

const ROLE_MAP = {
  "manager": "organizer",
  "content manager": "fileOrganizer",
  "contributor": "writer",
  "commenter": "commenter",
  "viewer": "reader"
};

function doGet() {
  return HtmlService.createHtmlOutputFromFile("Index")
    .setTitle("Shared Drive Provisioner");
}

function runProvision(sheetRef, sheetName, emailOverride) {
  const ssId = extractSheetId_(sheetRef);
  if (!ssId) throw new Error("Could not parse Spreadsheet ID.");

  const sheet = openSheet_(ssId, sheetName);
  const res = processSheet_(sheet);

  const to = (emailOverride && emailOverride.trim()) || getNotifyEmail_();
  if (to) sendReportEmail_(res, to);

  return "Provisioning complete. Report sent to " + to;
}

// ========== Core Engine ==========
function processSheet_(sheet) {
  const values = sheet.getDataRange().getValues();
  const headers = values[0].map(h => String(h || "").trim().toLowerCase());

  const idx = { driveName: headers.indexOf("drive name") };
  Object.keys(ROLE_MAP).forEach(k => idx[k] = headers.indexOf(k));

  const created = [], failures = [], skipped = [];

  for (let r = 1; r < values.length; r++) {
    const row = values[r];
    const driveName = String(row[idx.driveName] || "").trim();
    if (!driveName) {
      skipped.push({ row: r+1, reason: "Missing Drive name" });
      continue;
    }

    let driveId;
    try {
      driveId = createSharedDrive_(driveName);
    } catch (e) {
      failures.push({ driveName, driveId:"", error:"Create failed: "+e.message });
      continue;
    }

    Object.entries(ROLE_MAP).forEach(([headerKey, driveRole]) => {
      const col = idx[headerKey];
      if (col < 0) return;
      const cell = String(row[col] || "").trim();
      if (!cell) return;
      const groups = parseEmails_(cell);
      groups.forEach(g => {
        try {
          addGroupPermission_(driveId, g, driveRole);
        } catch (e) {
          failures.push({ driveName, driveId, role:driveRole, group:g, error:e.message });
        }
      });
    });

    created.push({ driveName, driveId });
  }

  return { created, failures, skipped, timestamp: new Date() };
}

// ========== Drive Helpers ==========
function createSharedDrive_(name) {
  const requestId = Utilities.getUuid();
  const drive = Drive.Drives.create({ name }, requestId);
  if (!drive || !drive.id) throw new Error("No drive ID returned");
  return drive.id;
}

function addGroupPermission_(driveId, groupEmail, role) {
  Drive.Permissions.create(
    { type:"group", role, emailAddress:groupEmail },
    driveId,
    { supportsAllDrives:true, sendNotificationEmail:false }
  );
}

// ========== Helpers ==========
function openSheet_(id, sheetName) {
  const ss = SpreadsheetApp.openById(id);
  if (sheetName) {
    const s = ss.getSheetByName(sheetName);
    if (!s) throw new Error(`No sheet named "${sheetName}"`);
    return s;
  }
  return ss.getSheets()[0];
}

function parseEmails_(txt) {
  return txt.split(/[,;\n\r]+/).map(s => s.trim()).filter(Boolean);
}

function extractSheetId_(urlOrId) {
  if (/^[a-zA-Z0-9-_]{20,}$/.test(urlOrId)) return urlOrId;
  const m = urlOrId.match(/\/d\/([a-zA-Z0-9-_]+)/);
  if (m) return m[1];
  const m2 = urlOrId.match(/[?&]id=([a-zA-Z0-9-_]+)/);
  if (m2) return m2[1];
  return "";
}

function getNotifyEmail_() {
  try {
    return Session.getActiveUser().getEmail();
  } catch(e) {
    return "";
  }
}

// ========== Report Email ==========
function sendReportEmail_(res, to) {
  const when = Utilities.formatDate(res.timestamp, Session.getScriptTimeZone(), "MMM d, yyyy h:mma");
  let html = `<h2>Shared Drive Provisioning Report</h2><p>${when}</p>`;
  html += `<h3>Created (${res.created.length})</h3><ul>`;
  res.created.forEach(c => {
    const link = `https://drive.google.com/drive/folders/${c.driveId}`;
    html += `<li><a href="${link}">${c.driveName}</a> (${c.driveId})</li>`;
  });
  html += "</ul>";

  if (res.failures.length) {
    html += `<h3>Failures (${res.failures.length})</h3><ul>`;
    res.failures.forEach(f => {
      html += `<li>${f.driveName} (${f.driveId||"-"}): ${f.error||""}</li>`;
    });
    html += "</ul>";
  }

  if (res.skipped.length) {
    html += `<h3>Skipped (${res.skipped.length})</h3><ul>`;
    res.skipped.forEach(s => {
      html += `<li>Row ${s.row}: ${s.reason}</li>`;
    });
    html += "</ul>";
  }

  MailApp.sendEmail({ to, subject:"Shared Drive Provisioning Report", htmlBody:html });
}
