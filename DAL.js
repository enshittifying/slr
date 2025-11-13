function getMasterSheet() {
  return SpreadsheetApp.openById(MASTER_SHEET_ID);
}

function createMember(memberData) {
  try {
    const ss = getMasterSheet();
    const membersSheet = ss.getSheetByName('Members');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const newMemberId = membersSheet.getLastRow() > 0 ? membersSheet.getLastRow() : 1;
      const newRow = [[newMemberId, memberData.fullName, memberData.email, memberData.role]];
      membersSheet.getRange(membersSheet.getLastRow() + 1, 1, 1, 4).setValues(newRow);
      return newMemberId;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getMemberByEmail(email) {
  try {
    const ss = getMasterSheet();
    const membersSheet = ss.getSheetByName('Members');

    const lastRow = membersSheet.getLastRow();
    if (lastRow < 2) {
      return null; // No data rows
    }

    const target = String(email).trim().toLowerCase();
    const emails = membersSheet.getRange(2, 3, lastRow - 1, 1).getValues();

    for (let i = 0; i < emails.length; i++) {
      const candidate = String(emails[i][0] || '').trim().toLowerCase();
      if (candidate === target) {
        const row = i + 2; // offset for header
        const memberData = membersSheet.getRange(row, 1, 1, 4).getValues()[0];
        return {
          memberId: memberData[0],
          fullName: memberData[1],
          email: memberData[2],
          role: memberData[3]
        };
      }
    }

    return null;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getAllMembers() {
  try {
    const ss = getMasterSheet();
    const membersSheet = ss.getSheetByName('Members');
    const values = membersSheet.getDataRange().getValues();
    if (!values || values.length <= 1) {
      return [];
    }
    values.shift(); // remove header
    const members = [];
    for (const row of values) {
      if ((row[0] !== '' && row[0] !== null) || (row[2] && String(row[2]).trim() !== '')) {
        members.push({
          memberId: row[0],
          fullName: row[1],
          email: row[2],
          role: row[3]
        });
      }
    }
    return members;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return [];
  }
}

function getAllTasks() {
  try {
    const ss = getMasterSheet();
    const tasksSheet = ss.getSheetByName('Tasks');
    const values = tasksSheet.getDataRange().getValues();
    if (!values || values.length <= 1) return [];
    values.shift();
    const tasks = [];
    for (const row of values) {
      tasks.push({
        taskId: row[0],
        title: row[1],
        description: row[2],
        dueDate: row[3],
        linkedFormId: row[4]
      });
    }
    return tasks;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return [];
  }
}

function getAllAssignments() {
  try {
    const ss = getMasterSheet();
    const assignmentsSheet = ss.getSheetByName('Assignments');
    const values = assignmentsSheet.getDataRange().getValues();
    if (!values || values.length <= 1) return [];
    values.shift();
    const assignments = [];
    for (const row of values) {
      assignments.push({
        assignmentId: row[0],
        memberId: row[1],
        taskId: row[2],
        status: row[3],
        dateCompleted: row[4]
      });
    }
    return assignments;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return [];
  }
}

function getAllAttendanceLogs() {
  try {
    const ss = getMasterSheet();
    const sheet = ss.getSheetByName('Attendance_Log');
    const values = sheet.getDataRange().getValues();
    if (!values || values.length <= 1) return [];
    values.shift();
    const logs = [];
    for (const row of values) {
      logs.push({
        eventId: row[0],
        memberId: row[1],
        eventName: row[2],
        date: row[3],
        status: row[4]
      });
    }
    return logs;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return [];
  }
}

function getAllSystemConfig() {
  try {
    const ss = getMasterSheet();
    const sheet = ss.getSheetByName('System_Config');
    const values = sheet.getDataRange().getValues();
    if (!values || values.length <= 1) return [];
    values.shift();
    const cfg = [];
    for (const row of values) {
      cfg.push({ key: row[0], value: row[1] });
    }
    return cfg;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return [];
  }
}

function updateMember(memberId, memberData) {
  try {
    const ss = getMasterSheet();
    const membersSheet = ss.getSheetByName('Members');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = membersSheet.createTextFinder(memberId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        membersSheet.getRange(row, 2, 1, 3).setValues([[memberData.fullName, memberData.email, memberData.role]]);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function deleteMember(memberId) {
  try {
    const ss = getMasterSheet();
    const membersSheet = ss.getSheetByName('Members');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = membersSheet.createTextFinder(memberId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        membersSheet.deleteRow(row);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function createTask(taskData) {
  try {
    const ss = getMasterSheet();
    const tasksSheet = ss.getSheetByName('Tasks');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const newTaskId = tasksSheet.getLastRow() > 0 ? tasksSheet.getLastRow() : 1;
      const newRow = [[newTaskId, taskData.title, taskData.description, taskData.dueDate, taskData.linkedFormId]];
      tasksSheet.getRange(tasksSheet.getLastRow() + 1, 1, 1, 5).setValues(newRow);
      return newTaskId;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getTaskById(taskId) {
  try {
    const ss = getMasterSheet();
    const tasksSheet = ss.getSheetByName('Tasks');

    const textFinder = tasksSheet.createTextFinder(taskId);
    const foundRange = textFinder.findNext();

    if (foundRange) {
      const row = foundRange.getRow();
      const taskData = tasksSheet.getRange(row, 1, 1, 5).getValues()[0];
      return {
        taskId: taskData[0],
        title: taskData[1],
        description: taskData[2],
        dueDate: taskData[3],
        linkedFormId: taskData[4]
      };
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function updateTask(taskId, taskData) {
  try {
    const ss = getMasterSheet();
    const tasksSheet = ss.getSheetByName('Tasks');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = tasksSheet.createTextFinder(taskId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        tasksSheet.getRange(row, 2, 1, 4).setValues([[taskData.title, taskData.description, taskData.dueDate, taskData.linkedFormId]]);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function deleteTask(taskId) {
  try {
    const ss = getMasterSheet();
    const tasksSheet = ss.getSheetByName('Tasks');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = tasksSheet.createTextFinder(taskId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        tasksSheet.deleteRow(row);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function createAssignment(assignmentData) {
  try {
    const ss = getMasterSheet();
    const assignmentsSheet = ss.getSheetByName('Assignments');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const newAssignmentId = assignmentsSheet.getLastRow() > 0 ? assignmentsSheet.getLastRow() : 1;
      const newRow = [[newAssignmentId, assignmentData.memberId, assignmentData.taskId, assignmentData.status, assignmentData.dateCompleted]];
      assignmentsSheet.getRange(assignmentsSheet.getLastRow() + 1, 1, 1, 5).setValues(newRow);
      return newAssignmentId;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getAssignmentById(assignmentId) {
  try {
    const ss = getMasterSheet();
    const assignmentsSheet = ss.getSheetByName('Assignments');

    const textFinder = assignmentsSheet.createTextFinder(assignmentId);
    const foundRange = textFinder.findNext();

    if (foundRange) {
      const row = foundRange.getRow();
      const assignmentData = assignmentsSheet.getRange(row, 1, 1, 5).getValues()[0];
      return {
        assignmentId: assignmentData[0],
        memberId: assignmentData[1],
        taskId: assignmentData[2],
        status: assignmentData[3],
        dateCompleted: assignmentData[4]
      };
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function updateAssignment(assignmentId, assignmentData) {
  try {
    const ss = getMasterSheet();
    const assignmentsSheet = ss.getSheetByName('Assignments');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = assignmentsSheet.createTextFinder(assignmentId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        assignmentsSheet.getRange(row, 2, 1, 4).setValues([[assignmentData.memberId, assignmentData.taskId, assignmentData.status, assignmentData.dateCompleted]]);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function deleteAssignment(assignmentId) {
  try {
    const ss = getMasterSheet();
    const assignmentsSheet = ss.getSheetByName('Assignments');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = assignmentsSheet.createTextFinder(assignmentId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        assignmentsSheet.deleteRow(row);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function getAssignmentsByMemberId(memberId) {
  try {
    const ss = getMasterSheet();
    const assignmentsSheet = ss.getSheetByName('Assignments');

    const textFinder = assignmentsSheet.createTextFinder(memberId);
    const foundRanges = textFinder.findAll();

    if (foundRanges.length > 0) {
      const result = [];
      for (const range of foundRanges) {
        const row = range.getRow();
        const assignmentData = assignmentsSheet.getRange(row, 1, 1, 5).getValues()[0];
        result.push({
          assignmentId: assignmentData[0],
          memberId: assignmentData[1],
          taskId: assignmentData[2],
          status: assignmentData[3],
          dateCompleted: assignmentData[4]
        });
      }
      return result;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getAssignmentsByTaskId(taskId) {
  try {
    const ss = getMasterSheet();
    const assignmentsSheet = ss.getSheetByName('Assignments');

    const textFinder = assignmentsSheet.createTextFinder(taskId);
    const foundRanges = textFinder.findAll();

    if (foundRanges.length > 0) {
      const result = [];
      for (const range of foundRanges) {
        const row = range.getRow();
        const assignmentData = assignmentsSheet.getRange(row, 1, 1, 5).getValues()[0];
        result.push({
          assignmentId: assignmentData[0],
          memberId: assignmentData[1],
          taskId: assignmentData[2],
          status: assignmentData[3],
          dateCompleted: assignmentData[4]
        });
      }
      return result;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function createFormDefinition(formDefinitionData) {
  try {
    const ss = getMasterSheet();
    const formDefinitionsSheet = ss.getSheetByName('Form_Definitions');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const newFormDefId = formDefinitionsSheet.getLastRow() > 0 ? formDefinitionsSheet.getLastRow() : 1;
      const newRow = [[newFormDefId, formDefinitionData.formName, formDefinitionData.googleFormId, formDefinitionData.itemId, formDefinitionData.questionTitle, formDefinitionData.itemType, formDefinitionData.options]];
      formDefinitionsSheet.getRange(formDefinitionsSheet.getLastRow() + 1, 1, 1, 7).setValues(newRow);
      return newFormDefId;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getFormDefinitionByName(formName) {
  try {
    const ss = getMasterSheet();
    const formDefinitionsSheet = ss.getSheetByName('Form_Definitions');

    const textFinder = formDefinitionsSheet.createTextFinder(formName);
    const foundRanges = textFinder.findAll();

    if (foundRanges.length > 0) {
      const result = [];
      for (const range of foundRanges) {
        const row = range.getRow();
        const formDefinitionData = formDefinitionsSheet.getRange(row, 1, 1, 7).getValues()[0];
        result.push({
          formDefId: formDefinitionData[0],
          formName: formDefinitionData[1],
          googleFormId: formDefinitionData[2],
          itemId: formDefinitionData[3],
          questionTitle: formDefinitionData[4],
          itemType: formDefinitionData[5],
          options: formDefinitionData[6]
        });
      }
      return result;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function updateFormDefinition(formDefId, formDefinitionData) {
  try {
    const ss = getMasterSheet();
    const formDefinitionsSheet = ss.getSheetByName('Form_Definitions');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = formDefinitionsSheet.createTextFinder(formDefId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        formDefinitionsSheet.getRange(row, 2, 1, 6).setValues([[formDefinitionData.formName, formDefinitionData.googleFormId, formDefinitionData.itemId, formDefinitionData.questionTitle, formDefinitionData.itemType, formDefinitionData.options]]);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function deleteFormDefinition(formDefId) {
  try {
    const ss = getMasterSheet();
    const formDefinitionsSheet = ss.getSheetByName('Form_Definitions');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = formDefinitionsSheet.createTextFinder(formDefId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        formDefinitionsSheet.deleteRow(row);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function createFormSubmission(submissionData) {
  try {
    const ss = getMasterSheet();
    const formSubmissionsSheet = ss.getSheetByName('Form_Submissions');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const newRow = [[new Date(), submissionData.formId, submissionData.respondentEmail, submissionData.responses]];
      formSubmissionsSheet.getRange(formSubmissionsSheet.getLastRow() + 1, 1, 1, 4).setValues(newRow);
      return true;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function getFormSubmissions(formId) {
  try {
    const ss = getMasterSheet();
    const formSubmissionsSheet = ss.getSheetByName('Form_Submissions');

    const textFinder = formSubmissionsSheet.createTextFinder(formId);
    const foundRanges = textFinder.findAll();

    if (foundRanges.length > 0) {
      const result = [];
      for (const range of foundRanges) {
        const row = range.getRow();
        const submissionData = formSubmissionsSheet.getRange(row, 1, 1, 4).getValues()[0];
        result.push({
          timestamp: submissionData[0],
          formId: submissionData[1],
          respondentEmail: submissionData[2],
          responses: submissionData[3]
        });
      }
      return result;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function createAttendanceLog(attendanceData) {
  try {
    const ss = getMasterSheet();
    const attendanceLogSheet = ss.getSheetByName('Attendance_Log');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const newRow = [[attendanceData.eventId, attendanceData.memberId, attendanceData.eventName, attendanceData.date, attendanceData.status]];
      attendanceLogSheet.getRange(attendanceLogSheet.getLastRow() + 1, 1, 1, 5).setValues(newRow);
      return true;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function getAttendanceLogs(memberId) {
  try {
    const ss = getMasterSheet();
    const attendanceLogSheet = ss.getSheetByName('Attendance_Log');

    const textFinder = attendanceLogSheet.createTextFinder(memberId);
    const foundRanges = textFinder.findAll();

    if (foundRanges.length > 0) {
      const result = [];
      for (const range of foundRanges) {
        const row = range.getRow();
        const logData = attendanceLogSheet.getRange(row, 1, 1, 5).getValues()[0];
        result.push({
          eventId: logData[0],
          memberId: logData[1],
          eventName: logData[2],
          date: logData[3],
          status: logData[4]
        });
      }
      return result;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function updateAttendanceLog(log) {
  try {
    const ss = getMasterSheet();
    const attendanceLogSheet = ss.getSheetByName('Attendance_Log');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = attendanceLogSheet.createTextFinder(log.eventId);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        attendanceLogSheet.getRange(row, 5).setValue(log.status);
        return true;
      } else {
        return false;
      }
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function getSystemConfig(key) {
  try {
    const ss = getMasterSheet();
    const systemConfigSheet = ss.getSheetByName('System_Config');

    const textFinder = systemConfigSheet.createTextFinder(key);
    const foundRange = textFinder.findNext();

    if (foundRange) {
      const row = foundRange.getRow();
      const value = systemConfigSheet.getRange(row, 2).getValue();
      return value;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function setSystemConfig(key, value) {
  try {
    const ss = getMasterSheet();
    const systemConfigSheet = ss.getSheetByName('System_Config');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const textFinder = systemConfigSheet.createTextFinder(key);
      const foundRange = textFinder.findNext();

      if (foundRange) {
        const row = foundRange.getRow();
        systemConfigSheet.getRange(row, 2).setValue(value);
      } else {
        systemConfigSheet.appendRow([key, value]);
      }

      return true;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function getTasksByFormId(formId) {
  try {
    const ss = getMasterSheet();
    const tasksSheet = ss.getSheetByName('Tasks');

    const textFinder = tasksSheet.createTextFinder(formId);
    const foundRanges = textFinder.findAll();

    if (foundRanges.length > 0) {
      const result = [];
      for (const range of foundRanges) {
        const row = range.getRow();
        const taskData = tasksSheet.getRange(row, 1, 1, 5).getValues()[0];
        result.push({
          taskId: taskData[0],
          title: taskData[1],
          description: taskData[2],
          dueDate: taskData[3],
          linkedFormId: taskData[4]
        });
      }
      return result;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getAllFormDefinitions() {
  try {
    const ss = getMasterSheet();
    const formDefinitionsSheet = ss.getSheetByName('Form_Definitions');
    const formDefinitions = formDefinitionsSheet.getDataRange().getValues();
    formDefinitions.shift(); // Remove header row

    const result = [];
    for (const row of formDefinitions) {
      result.push({
        formDefId: row[0],
        formName: row[1],
        googleFormId: row[2],
        itemId: row[3],
        questionTitle: row[4],
        itemType: row[5],
        options: row[6]
      });
    }
    return result;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getSubmittedForms(memberId) {
  try {
    const ss = getMasterSheet();
    const formSubmissionsSheet = ss.getSheetByName('Form_Submissions');
    const submissions = formSubmissionsSheet.getDataRange().getValues();
    submissions.shift(); // Remove header row

    const member = getMemberById(memberId);
    if (!member) {
      return null;
    }

    const result = [];
    for (const row of submissions) {
      if (row[2] === member.email) {
        result.push(row[1]);
      }
    }
    return result;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function getMemberById(memberId) {
  try {
    const ss = getMasterSheet();
    const membersSheet = ss.getSheetByName('Members');

    const textFinder = membersSheet.createTextFinder(memberId);
    const foundRange = textFinder.findNext();

    if (foundRange) {
      const row = foundRange.getRow();
      const memberData = membersSheet.getRange(row, 1, 1, 4).getValues()[0];
      return {
        memberId: memberData[0],
        fullName: memberData[1],
        email: memberData[2],
        role: memberData[3]
      };
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}
