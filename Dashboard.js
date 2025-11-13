// Dashboard data functions for the Stanford Law Review Workflow Management System

function server_getDashboardData() {
  try {
    const userEmail = Session.getEffectiveUser().getEmail();
    const member = getMemberByEmail(userEmail);

    if (member) {
      const tasks = server_getTasksForUser(member.memberId);
      const attendance = getAttendanceLogs(member.memberId);
      const forms = getAvailableForms(member.memberId); // This function doesn't exist yet

      const isAdmin = member.role && String(member.role).toLowerCase().indexOf('admin') !== -1;
      Logger.log('Admin check: email=' + userEmail + ', role=' + member.role + ', isAdmin=' + isAdmin);
      return {
        member: member,
        tasks: tasks,
        attendance: attendance,
        forms: forms,
        isAdmin: isAdmin
      };
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}
