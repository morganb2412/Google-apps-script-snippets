 VIP Email Summarizer (Gmail Add-on, Apps Script + Gemini)

Triage VIP email fast. This Gmail add-on lets you set a list of **VIP senders**, then:
- ✨ Uses **Gemini** to summarize unread VIP threads (last few messages)
- 🚨 Detects urgency cues (e.g., “ASAP”, “deadline”) 
- 💬 Sends a **Google Chat** notification with summary + “Open in Gmail” link
- ⚙️ In-addon **Settings** to manage VIPs

> Optional (v2 branch): reply tracking, configurable reminders for unreplied VIP emails, and an end-of-day report to Chat + email.

## Demo
_(screenshot or GIF here)_

## Quick start
1. Go to **script.new** → paste `Code.gs` (from this repo) and update `appsscript.json` (manifest).
2. **Project Settings → Script properties**  
   - `GEMINI_API_KEY` = your Google AI Studio key  
   - `CHAT_WEBHOOK_URL` = Google Chat Space webhook (optional but recommended)
3. **Deploy → Test deployments → Google Workspace add-on → Install** for your account.
4. Open Gmail → right sidebar → **VIP Email Summarizer** → **Settings** → add your VIP emails.
5. Click **Summarize Unread Now** to test.  
   _(Optional)_ Run `installTriggers()` to scan hourly.  
   _(v2)_ Use **Install/Refresh Triggers** to enable reminders + daily report.

## Manifest scopes
```json
[
  "https://www.googleapis.com/auth/gmail.addons.execute",
  "https://www.googleapis.com/auth/gmail.readonly",
  "https://www.googleapis.com/auth/gmail.modify",
  "https://www.googleapis.com/auth/script.external_request",
  "https://www.googleapis.com/auth/script.storage",
  "https://www.googleapis.com/auth/userinfo.email",
  "https://www.googleapis.com/auth/script.scriptapp",   // manage triggers (v2)
  "https://www.googleapis.com/auth/script.send_mail"     // daily email report (v2)
]
