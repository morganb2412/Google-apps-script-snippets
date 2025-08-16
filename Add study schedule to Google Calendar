function scheduleChapters() {
  const cal = CalendarApp.getDefaultCalendar();          
  const startDate = new Date(2025, 7, 17);              
  const firstChapter = 7;
  const lastChapter  = 20;

  for (let ch = firstChapter; ch <= lastChapter; ch++) {
    const date = new Date(startDate);                    
    date.setDate(startDate.getDate() + (ch - firstChapter));

    const title = `Read Python Crash Course — Chapter ${ch}`;
    const desc  = `Goal: complete Chapter ${ch} today.`;

    // Avoid duplicates
    const existing = cal.getEventsForDay(date)
      .some(e => e.isAllDayEvent() && e.getTitle() === title);
    if (existing) continue;

    const ev = cal.createAllDayEvent(title, date, { description: desc });
    
    try { ev.addPopupReminder(120); } catch (_) {}
  }
}
