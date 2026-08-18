# Private tenant deployment

Legacy DevBridge is distributed as a private Chrome extension and is not publicly searchable. The backend remains the private Cloud Run service in GCP project `moesautomationweekly`.

## Pilot installation verification

Before uploading a tenant release, verify the exact build locally in Chrome:

1. Run `npm ci`, `npm run typecheck`, `npm run lint`, `npm test -- --run`, and `npm run build` from `extension/`.
2. Open `chrome://extensions`, enable **Developer mode**, and choose **Load unpacked**.
3. Select the generated `extension/dist` directory, not `extension/src` and not the release ZIP.
4. Open an Apps Script project at `https://script.google.com/home/projects/<SCRIPT_ID>/edit`.
5. Confirm the DevBridge toolbar appears and **Project**, **Changes**, and **Code Assistant** open the side panel.
6. Navigate to another Apps Script project without closing the tab and confirm the project ID and name update.
7. Navigate to the Apps Script home page and confirm DevBridge no longer shows the prior project as active.
8. Reload the unpacked extension, reload the Apps Script tab, and repeat steps 5-7.

Record the Chrome version, extension version, tester, date, and results before promoting the ZIP.

## Chromium Edge compatibility

The extension uses Manifest V3, standard content scripts, and the Chromium `sidePanel` API. Microsoft Edge compatibility is expected but is not considered verified until the same pilot checklist passes in `edge://extensions`. Tenant rollout remains Chrome-first; Edge should be assigned to a separate pilot group until validated.

## Release package

From `extension/` run:

```powershell
npm run package:private
```

The versioned ZIP is written to `extension/release/`. Upload the ZIP in the Chrome Web Store Developer Dashboard and select **Private** visibility restricted to the organization's Google Workspace domain. Publishing requires a Chrome Web Store developer publisher controlled by an organizational account or group.

## Tenant assignment

Create a Google Group such as `devbridge-users@your-domain` and add only approved users. In Google Admin Console:

1. Open **Devices > Chrome > Apps & extensions > Users & browsers**.
2. Select the target Google Group or organizational unit.
3. Add the privately published DevBridge extension by its Chrome Web Store ID.
4. Choose **Force install** or **Force install + pin to browser toolbar**.
5. Permit access to `https://script.google.com/*`.
6. Save and allow Chrome policy propagation.

Start with a small pilot group. Confirm the extension appears in `chrome://policy`, the Apps Script toolbar loads, and no unmanaged account receives the extension before expanding access.

## Update process

Increment the manifest version, rerun all checks, create a new private package, upload it to the same private listing, and publish the update. Managed Chrome clients update through the listing while retaining the extension ID and policy assignment.

## Security boundary

The extension package contains no OAuth secrets, GitHub credentials, Cloud Run identity tokens, or LLM keys. Tenant users will authenticate through the planned DevBridge backend session flow. Until that flow is implemented, the embedded toolbar and project detection are suitable for UI testing but privileged backend features remain unavailable.
