// =============================================
// Gmail VIP Summarizer Add-on (Apps Script)
// v2 — Summaries, response tracking, reminders, daily report
// =============================================

/**** SETUP NOTES ****
1) Project Settings → Script properties:
   - GEMINI_API_KEY        (Google AI Studio API key)
   - CHAT_WEBHOOK_URL      (Google Chat incoming webhook URL; optional but recommended)

2) Manifest (appsscript.json) must include these scopes:
   "oauthScopes": [
     "https://www.googleapis.com/auth/gmail.addons.execute",
     "https://www.googleapis.com/auth/gmail.readonly",
     "https://www.googleapis.com/auth/gmail.modify",
     "https://www.googleapis.com/auth/script.external_request",
     "https://www.googleapis.com/auth/script.storage",
     "https://www.googleapis.com/auth/script.send_mail",   // needed for daily email report
     "https://www.googleapis.com/auth/script.scriptapp"    // optional; allows clearing triggers
   ]

3) Deploy → Test deployments → Google Workspace add-on → Install.

4) In Gmail add-on → Settings:
   - VIP emails
   - Reminder frequency (Off / 15m / 30m / 1h / 2h / 4h)
   - Daily report time (HH:mm, 24h)
   Then click “Install/Refresh Triggers.”

5) Edit URGENCY_KEYWORDS to fit your org.
****/

const URGENCY_KEYWORDS = [
  'urgent', 'asap', 'time sensitive', 'immediately', 'priority', 'due today',
  'needs your approval', 'deadline', 'blocker', 'critical', 'high priority'
];

const CONFIG = {
  MODEL: 'gemini-1.5-flash',
  MAX_TOKENS: 2048,
  TEMPERATURE: 0.2,
  LOOKBACK_DAYS: 7,              // window for searching VIP threads
  MAX_THREADS: 30,               // cap to protect quotas
  SUMMARY_BULLETS: 5,
  TIMEZONE: Session.getScriptTimeZone(),
  LABEL_SUMMARIZED: 'VIP-Summarized',
  LABEL_TRACKED: 'VIP-Tracked',
};

// -----------------------
// Gmail Add-on Entrypoints
// -----------------------

function onGmailAddonOpen(e) {
  return buildHomeCard_();
}

function onGmailMessageOpen(e) {
  return buildHomeCard_(e);
}

function buildHomeCard_(e) {
  const card = CardService.newCardBuilder();
  card.setHeader(CardService.newCardHeader().setTitle('VIP Email Summarizer'));

  const vipList = getVipList_();
  const vipText = vipList.length ? vipList.join(', ') : 'No VIPs set';
  const prefs = getPrefs_();

  const section = CardService.newCardSection();
  section.addWidget(CardService.newTextParagraph().setText(
    'Summarize unread VIP emails with Gemini, detect urgency, track your replies, set reminders, and get a daily report.'
  ));
  section.addWidget(CardService.newKeyValue().setTopLabel('VIP Senders').setContent(vipText));
  section.addWidget(CardService.newKeyValue().setTopLabel('Reminder Frequency').setContent(prefs.reminder || 'off'));
  section.addWidget(CardService.newKeyValue().setTopLabel('Daily Report Time').setContent(prefs.reportTime || '17:00'));

  section.addWidget(
    CardService.newTextButton()
      .setText('Summarize Unread Now')
      .setOnClickAction(CardService.newAction().setFunctionName('addonSummarizeNow_'))
      .setTextButtonStyle(CardService.TextButtonStyle.FILLED)
  );

  section.addWidget(
    CardService.newTextButton()
      .setText('Settings')
      .setOnClickAction(CardService.newAction().setFunctionName('openSettings_'))
  );

  section.addWidget(
    CardService.newTextButton()
      .setText('Install/Refresh Triggers')
      .setOnClickAction(CardService.newAction().setFunctionName('installTriggersFromPrefs_'))
  );

  card.addSection(section);
  return card.build();
}

// -----------------------
// Settings UI (fixed)
// -----------------------

function openSettings_() {
  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle('Settings'));

  const vipList = getVipList_();
  const prefs = getPrefs_(); // { reminder, reportTime }

  // Create section FIRST, then add widgets to it.
  const section = CardService.newCardSection();

  // VIP emails input
  const vipInput = CardService.newTextInput()
    .setFieldName('vip_emails')
    .setTitle('VIP email addresses (comma/newline separated)')
    .setValue(vipList.join(', '));
  section.addWidget(vipInput);

  // Reminder dropdown (uses addItem, NOT newSelectionItem)
  const reminderChoices = ['off','15m','30m','1h','2h','4h'];
  const ddReminder = CardService.newSelectionInput()
    .setType(CardService.SelectionInputType.DROPDOWN)
    .setFieldName('reminder')
    .setTitle('Reminder frequency for unreplied VIP emails');
  reminderChoices.forEach(v => ddReminder.addItem(v, v, prefs.reminder === v));
  section.addWidget(ddReminder);

  // Daily report time
  const reportTime = CardService.newTextInput()
    .setFieldName('reportTime')
    .setTitle('Daily report time (24h HH:mm)')
    .setValue(prefs.reportTime || '17:00');
  section.addWidget(reportTime);

  // Save / Back
  section.addWidget(
    CardService.newTextButton()
      .setText('Save')
      .setOnClickAction(CardService.newAction().setFunctionName('saveSettings_'))
      .setTextButtonStyle(CardService.TextButtonStyle.FILLED)
  );
  section.addWidget(
    CardService.newTextButton()
      .setText('Back')
      .setOnClickAction(CardService.newAction().setFunctionName('onGmailAddonOpen'))
  );

  card.addSection(section);
  return card.build();
}

function saveSettings_(e) {
  const inputs = (e && e.commonEventObject && e.commonEventObject.formInputs) || {};
  const rawVip = getInput_(inputs, 'vip_emails');
  const list = normalizeEmailList_(rawVip);
  setVipList_(list);

  const reminder = getInput_(inputs, 'reminder') || 'off';
  const reportTime = (getInput_(inputs, 'reportTime') || '17:00').trim();
  setPrefs_({ reminder, reportTime });

  const nav = CardService.newNavigation();
  nav.updateCard(buildHomeCard_());
  return CardService.newActionResponseBuilder().setNavigation(nav).build();
}

function installTriggersFromPrefs_() {
  installTriggers(); // clears + installs based on saved prefs (safe if scope missing)
  const nav = CardService.newNavigation().pushCard(buildToastCard_('Triggers installed/updated based on settings.'));
  return CardService.newActionResponseBuilder().setNavigation(nav).build();
}

function getInput_(inputs, key) {
  const f = inputs[key];
  if (!f) return '';
  const si = f.stringInputs;
  if (!si || !si.value || !si.value.length) return '';
  return si.value[0];
}

// -----------------------
// Buttons → Actions
// -----------------------

function addonSummarizeNow_() {
  summarizeUnreadVip_();
  const nav = CardService.newNavigation().pushCard(buildToastCard_('Summary run started. Check Chat or Logs.'));
  return CardService.newActionResponseBuilder().setNavigation(nav).build();
}

// -----------------------
// Core Logic
// -----------------------

function checkInboxAndNotify() { summarizeUnreadVip_(); }
function reminderTick()        { sendRemindersForUnreplied_(); }
function dailyReportTick()     { sendDailyReport_(); }

function summarizeUnreadVip_() {
  const vipList = getVipList_();
  if (!vipList.length) { console.log('No VIPs configured; skipping.'); return; }

  const query = buildSearchQuery_(vipList);
  const threads = GmailApp.search(query, 0, CONFIG.MAX_THREADS);
  if (!threads.length) { console.log('No unread VIP threads.'); return; }

  const meAliases = new Set([Session.getActiveUser().getEmail()].concat(GmailApp.getAliases()));

  threads.forEach(thread => {
    try {
      // Track thread snapshot
      const firstMsg = thread.getMessages()[0];
      const from = firstMsg.getFrom();
      const subject = thread.getFirstMessageSubject();
      const threadId = thread.getId();

      upsertTrack_(threadId, {
        subject, from,
        firstSeen: Date.now(),
        responded: hasUserResponded_(thread, meAliases),
        lastReminderTs: null
      });

      // Summarize + notify
      const summary = summarizeThread_(thread);
      const { isUrgent, urgencyHits } = detectUrgency_(summary);
      const permalink = buildPermalink_(firstMsg);
      const chatText = `**From:** ${from}\n**Subject:** ${subject}\n\n**Summary:**\n${summary}\n\n[Open in Gmail](${permalink})`;
      postToChat_(chatText, isUrgent, urgencyHits);

      thread.addLabel(getOrCreateLabel_(CONFIG.LABEL_SUMMARIZED));
      thread.addLabel(getOrCreateLabel_(CONFIG.LABEL_TRACKED));
    } catch (err) {
      console.error('Error summarizing thread', err);
    }
  });
}

function hasUserResponded_(thread, meAliases) {
  // True if any message in thread is from me (including aliases)
  const msgs = thread.getMessages();
  for (let i = msgs.length - 1; i >= 0; i--) {
    const fromHeader = (msgs[i].getFrom() || '').toLowerCase();
    for (const alias of meAliases) {
      if (alias && fromHeader.indexOf(alias.toLowerCase()) !== -1) return true;
    }
  }
  return false;
}

function summarizeThread_(thread) {
  const msgs = thread.getMessages().slice(-3); // last up to 3 mails
  let content = '';
  msgs.forEach((m, idx) => {
    const header = `\n--- Message ${idx+1} from ${m.getFrom()} at ${m.getDate()} ---\n`;
    const body = stripHtml_(m.getBody());
    content += header + body.substring(0, 5000);
  });

  const prompt = `You are an executive assistant. Summarize the email thread in ${CONFIG.SUMMARY_BULLETS} concise bullet points. Then extract action items with owner and due date if stated. Keep under 120 words.`;
  return callGemini_(prompt + "\n\nTHREAD:\n" + content);
}

function detectUrgency_(summary) {
  const lower = summary.toLowerCase();
  const hits = URGENCY_KEYWORDS.filter(k => lower.includes(k));
  return { isUrgent: hits.length > 0, urgencyHits: hits };
}

function buildPermalink_(message) {
  return 'https://mail.google.com/mail/u/0/#search/rfc822msgid%3A' + encodeURIComponent(message.getId());
}

// -----------------------
// Tracking Store (User Properties JSON)
// -----------------------

function getTrack_() {
  const raw = PropertiesService.getUserProperties().getProperty('TRACK_MAP');
  return raw ? JSON.parse(raw) : {}; // { threadId: {subject, from, firstSeen, responded, lastReminderTs} }
}

function upsertTrack_(threadId, patch) {
  const map = getTrack_();
  const prev = map[threadId] || {};
  if (prev.responded) patch.responded = true; // once true, keep true
  map[threadId] = Object.assign({}, prev, patch);
  PropertiesService.getUserProperties().setProperty('TRACK_MAP', JSON.stringify(map));
}

function setRespondedIfAny_() {
  const map = getTrack_();
  const meAliases = new Set([Session.getActiveUser().getEmail()].concat(GmailApp.getAliases()));
  Object.keys(map).forEach(id => {
    try {
      const thread = GmailApp.getThreadById(id);
      if (thread && hasUserResponded_(thread, meAliases)) {
        map[id].responded = true;
      }
    } catch (e) {/* ignore */}
  });
  PropertiesService.getUserProperties().setProperty('TRACK_MAP', JSON.stringify(map));
}

// -----------------------
// Reminders for Unreplied
// -----------------------

function sendRemindersForUnreplied_() {
  const prefs = getPrefs_();
  const minutes = parseReminder_(prefs.reminder);
  if (!minutes) return; // reminders off

  // refresh responded statuses
  setRespondedIfAny_();

  const map = getTrack_();
  const now = Date.now();
  const cutoff = now - CONFIG.LOOKBACK_DAYS * 24 * 60 * 60 * 1000;
  const pending = [];

  Object.entries(map).forEach(([threadId, rec]) => {
    if (rec.firstSeen < cutoff) return; // too old
    if (rec.responded) return;          // already replied

    const sinceLast = rec.lastReminderTs ? (now - rec.lastReminderTs) : Infinity;
    if (sinceLast >= minutes * 60 * 1000) {
      pending.push({ threadId, rec });
    }
  });

  if (!pending.length) return;

  pending.forEach(item => {
    try {
      const thread = GmailApp.getThreadById(item.threadId);
      if (!thread) return;
      const firstMsg = thread.getMessages()[0];
      const permalink = buildPermalink_(firstMsg);
      const text = `⏰ *Reminder*: Unreplied VIP email
**From:** ${item.rec.from}
**Subject:** ${item.rec.subject}
[Open in Gmail](${permalink})`;
      postToChat_(text, false, []);
      item.rec.lastReminderTs = Date.now(); // mark reminder time
    } catch (e) {/* ignore per-thread errors */}
  });

  // save back
  const map2 = getTrack_();
  pending.forEach(({ threadId, rec }) => { map2[threadId] = rec; });
  PropertiesService.getUserProperties().setProperty('TRACK_MAP', JSON.stringify(map2));
}

function parseReminder_(val) {
  if (!val || val === 'off') return 0;
  const unit = val.slice(-1);
  const num = parseInt(val.slice(0, -1), 10);
  if (unit === 'm') return num;
  if (unit === 'h') return num * 60;
  return 0;
}

// -----------------------
// Daily Report
// -----------------------

function sendDailyReport_() {
  setRespondedIfAny_(); // refresh first
  const map = getTrack_();

  const today = new Date();
  const tz = CONFIG.TIMEZONE;
  const start = new Date(today); start.setHours(0,0,0,0);
  const end   = new Date(today); end.setHours(23,59,59,999);

  const opened = [];
  const replied = [];
  const pending = [];

  Object.entries(map).forEach(([threadId, rec]) => {
    if (rec.firstSeen >= start.getTime() && rec.firstSeen <= end.getTime()) {
      opened.push({ threadId, rec });
      (rec.responded ? replied : pending).push({ threadId, rec });
    }
  });

  const lines = [];
  lines.push(`**Daily VIP Email Report** (${Utilities.formatDate(today, tz, 'MMM d, yyyy')})`);
  lines.push(`Opened today: ${opened.length} | Responded: ${replied.length} | Pending: ${pending.length}`);
  if (opened.length) {
    lines.push(`\n**Details**`);
    opened.forEach(x => {
      const thread = safeGetThread_(x.threadId);
      const link = thread ? `[Open](${buildPermalink_(thread.getMessages()[0])})` : '';
      lines.push(`• ${x.rec.subject} — ${x.rec.from} ${x.rec.responded ? '✓ replied' : '⏳ pending'} ${link}`);
    });
  }
  const md = lines.join('\n');

  // Chat report
  postToChat_(md, false, []);

  // Email report
  const me = Session.getActiveUser().getEmail();
  MailApp.sendEmail({
    to: me,
    subject: `Daily VIP Email Report — ${Utilities.formatDate(today, tz, 'MMM d')}`,
    htmlBody: md.replace(/\n/g, '<br>')
  });
}

function safeGetThread_(id) {
  try { return GmailApp.getThreadById(id); } catch (e) { return null; }
}

// -----------------------
// Gemini API (Google AI Studio)
// -----------------------

function callGemini_(text) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!apiKey) throw new Error('Missing GEMINI_API_KEY in Script Properties.');

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${CONFIG.MODEL}:generateContent?key=${apiKey}`;
  const payload = {
    contents: [{ parts: [{ text }] }],
    generationConfig: { temperature: CONFIG.TEMPERATURE, maxOutputTokens: CONFIG.MAX_TOKENS }
  };

  const res = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    payload: JSON.stringify(payload)
  });

  if (res.getResponseCode() !== 200) {
    throw new Error('Gemini API error: ' + res.getResponseCode() + ' ' + res.getContentText());
  }
  const data = JSON.parse(res.getContentText());
  const textOut =
    (data.candidates && data.candidates[0] &&
     data.candidates[0].content && data.candidates[0].content.parts &&
     data.candidates[0].content.parts[0].text) || '';
  return textOut.trim();
}

// -----------------------
// Google Chat Notification
// -----------------------

function postToChat_(markdown, isUrgent, hits) {
  const webhook = PropertiesService.getScriptProperties().getProperty('CHAT_WEBHOOK_URL');
  if (!webhook) { console.log('No CHAT_WEBHOOK_URL set; skipping Chat notification.'); return; }
  const prefix = isUrgent ? '🚨 *URGENT VIP EMAIL*' : '✉️ VIP Email Update';
  const hint = isUrgent && hits && hits.length ? `\n_Urgency cues: ${hits.join(', ')}_` : '';
  const payload = { text: `${prefix}\n\n${markdown}${hint}` };
  UrlFetchApp.fetch(webhook, {
    method: 'post',
    contentType: 'application/json; charset=UTF-8',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
}

// -----------------------
// Triggers (safe installer)
// -----------------------

function installTriggers() {
  // Try to clear existing triggers (works only if script.scriptapp scope granted)
  try {
    ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  } catch (e) {
    console.log('Skipping trigger clear (missing https://www.googleapis.com/auth/script.scriptapp).');
  }

  // Hourly VIP scan
  ScriptApp.newTrigger('checkInboxAndNotify').timeBased().everyHours(1).create();

  // Reminders cadence based on prefs
  const prefs = getPrefs_();
  const minutes = parseReminder_(prefs.reminder);
  if (minutes) {
    const b = ScriptApp.newTrigger('reminderTick').timeBased();
    if (minutes % 60 === 0) b.everyHours(Math.max(1, minutes / 60)).create();
    else b.everyMinutes(Math.max(1, minutes)).create();
  }

  // Daily report at specified hour
  const hhmm = (prefs.reportTime || '17:00').split(':');
  const hour = Math.max(0, Math.min(23, parseInt(hhmm[0], 10) || 17));
  ScriptApp.newTrigger('dailyReportTick').timeBased().atHour(hour).everyDays(1).create();
}

// -----------------------
// Helpers (prefs, search, vip list, labels, etc.)
// -----------------------

function getPrefs_() {
  const raw = PropertiesService.getUserProperties().getProperty('PREFS');
  const def = { reminder: 'off', reportTime: '17:00' };
  return raw ? Object.assign(def, JSON.parse(raw)) : def;
}

function setPrefs_(obj) {
  PropertiesService.getUserProperties().setProperty('PREFS', JSON.stringify(obj));
}

function buildSearchQuery_(vipList) {
  const fromClause = vipList.map(e => `from:${e}`).join(' OR ');
  const newer = `newer_than:${CONFIG.LOOKBACK_DAYS}d`;
  return `(${fromClause}) is:unread ${newer}`;
}

function normalizeEmailList_(raw) {
  return raw
    .split(/[\n,;]+/)
    .map(s => s.trim().toLowerCase())
    .filter(Boolean)
    .filter((v, i, a) => a.indexOf(v) === i);
}

function getVipList_() {
  const raw = PropertiesService.getUserProperties().getProperty('VIP_EMAILS') || '';
  return raw ? JSON.parse(raw) : [];
}

function setVipList_(arr) {
  PropertiesService.getUserProperties().setProperty('VIP_EMAILS', JSON.stringify(arr));
}

function stripHtml_(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&gt;/g, '>')
    .replace(/&lt;/g, '<')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();
}

function getOrCreateLabel_(name) {
  return GmailApp.getUserLabelByName(name) || GmailApp.createLabel(name);
}

function buildToastCard_(msg) {
  return CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader().setTitle('VIP Email Summarizer'))
    .addSection(CardService.newCardSection().addWidget(
      CardService.newTextParagraph().setText(msg)
    ))
    .build();
}
