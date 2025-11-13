// Automated Attendance Tracking Engine for the Stanford Law Review Workflow Management System

function createTrackedEvent(title, startTime, endTime, memberEmails) {
  try {
    // Create a new form for the event
    const form = FormApp.create(title + ' Attendance');
    form.setConfirmationMessage('Thanks for confirming your attendance.');
    const formUrl = form.getPublishedUrl();

    // Create a new calendar event
    const calendar = CalendarApp.getDefaultCalendar();
    const event = calendar.createEvent(title, new Date(startTime), new Date(endTime), {
      description: 'Please confirm your attendance by filling out this form: ' + formUrl,
      guests: memberEmails.join(',')
    });

    // Log the event and form details
    const eventId = event.getId();
    const formId = form.getId();
    createAttendanceLog({ eventId: eventId, memberId: null, eventName: title, date: new Date(startTime), status: 'Pending' });

    return eventId;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}
