const MASTER_SHEET_ID = '1_LLee3csGsrcqlJc38Ao_46FGsLnaZEOoMXWVmNqfXY';

function logError(error) {
  try {
    const ss = SpreadsheetApp.openById(MASTER_SHEET_ID);
    const errorLogSheet = ss.getSheetByName('Error_Log');

    const lock = LockService.getScriptLock();
    lock.waitLock(30000);

    try {
      const newRow = [[new Date(), error.user, error.message, error.stack_trace]];
      errorLogSheet.getRange(errorLogSheet.getLastRow() + 1, 1, 1, 4).setValues(newRow);
      return true;
    } finally {
      lock.releaseLock();
    }
  } catch (e) {
    // If logging fails, we can't do much
    console.error("Failed to log error: " + e.message);
    return false;
  }
}

function setupSheet() {
  const spreadsheetId = '1_LLee3csGsrcqlJc38Ao_46FGsLnaZEOoMXWVmNqfXY';
  const ss = SpreadsheetApp.openById(spreadsheetId);

  const tabs = {
    'Members': ['member_id', 'full_name', 'email', 'role'],
    'Tasks': ['task_id', 'title', 'description', 'due_date', 'linked_form_id'],
    'Assignments': ['assignment_id', 'member_id', 'task_id', 'status', 'date_completed'],
    'Form_Definitions': ['form_def_id', 'form_name', 'google_form_id', 'item_id', 'question_title', 'item_type', 'options'],
    'Form_Submissions': [],
    'Attendance_Log': ['event_id', 'member_id', 'event_name', 'date', 'status'],
    'System_Config': ['key', 'value'],
    'Error_Log': ['timestamp', 'user', 'message', 'stack_trace']
  };

  for (const tabName in tabs) {
    let sheet = ss.getSheetByName(tabName);
    if (!sheet) {
      sheet = ss.insertSheet(tabName);
    }

    const headers = tabs[tabName];
    if (headers.length > 0) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    }
  }
}

function doGet(e) {
  const userEmail = Session.getEffectiveUser().getEmail();
  Logger.log('User Email: ' + userEmail);
  
  if (!isAuthorized(userEmail)) {
    Logger.log('User is NOT authorized.');
    return HtmlService.createHtmlOutput('<h1>Access Denied</h1><p>You are not authorized to access this application.</p>');
  }

  Logger.log('User IS authorized.');
  const html = HtmlService.createTemplateFromFile('index');
  const member = getMemberByEmail(userEmail);
  html.userEmail = userEmail;
  html.userName = member && member.fullName ? member.fullName : userEmail;
  return html.evaluate();
}

function isAuthorized(email) {
  Logger.log('Checking authorization for email: ' + email);
  const member = getMemberByEmail(email);
  Logger.log('Member found: ' + (member !== null));
  return member !== null;
}

function setupRoles() {
  const spreadsheetId = '1_LLee3csGsrcqlJc38Ao_46FGsLnaZEOoMXWVmNqfXY';
  const ss = SpreadsheetApp.openById(spreadsheetId);
  
  // 1. Add roles to System_Config if they don't exist
  const configSheet = ss.getSheetByName('System_Config');
  const configData = configSheet.getDataRange().getValues();
  let rolesExist = false;
  for (let i = 0; i < configData.length; i++) {
    if (configData[i][0] === 'user_roles') {
      rolesExist = true;
      break;
    }
  }
  if (!rolesExist) {
    configSheet.appendRow(['user_roles', 'Member Editor,Senior Editor,Admin']);
  }

  // 2. Create data validation rule
  const membersSheet = ss.getSheetByName('Members');
  const rolesRange = configSheet.createTextFinder('user_roles').findNext().getRow();
  const roles = configSheet.getRange(rolesRange, 2).getValue().split(',');
  const rule = SpreadsheetApp.newDataValidation().requireValueInList(roles).build();
  membersSheet.getRange('D2:D').setDataValidation(rule);
}

