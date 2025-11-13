// Dynamic Form Engine for the Stanford Law Review Workflow Management System

function generateFormFromMetadata(formName) {
  try {
    const formMetadata = getFormDefinitionByName(formName);

    if (formMetadata) {
      const form = FormApp.create(formName);
      let googleFormId = form.getId();

      for (const item of formMetadata) {
        switch (item.itemType) {
          case 'text':
            form.addTextInput().setTitle(item.questionTitle);
            break;
          case 'paragraphText':
            form.addParagraphTextItem().setTitle(item.questionTitle);
            break;
          case 'multipleChoice':
            form.addMultipleChoiceItem().setTitle(item.questionTitle).setChoiceValues(item.options.split(','));
            break;
          case 'checkboxes':
            form.addCheckboxItem().setTitle(item.questionTitle).setChoiceValues(item.options.split(','));
            break;
          case 'dropdown':
            form.addListItem().setTitle(item.questionTitle).setChoiceValues(item.options.split(','));
            break;
        }
      }

      // Update the Google Form ID in the sheet
      for (const item of formMetadata) {
        item.googleFormId = googleFormId;
        updateFormDefinition(item.formDefId, item);
      }

      return googleFormId;
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function updateFormFromMetadata(formName) {
  try {
    const formMetadata = getFormDefinitionByName(formName);

    if (formMetadata) {
      const googleFormId = formMetadata[0].googleFormId;
      const form = FormApp.openById(googleFormId);

      // Delete all items
      const items = form.getItems();
      for (const item of items) {
        form.deleteItem(item);
      }

      // Recreate all items
      for (const item of formMetadata) {
        switch (item.itemType) {
          case 'text':
            form.addTextInput().setTitle(item.questionTitle);
            break;
          case 'paragraphText':
            form.addParagraphTextItem().setTitle(item.questionTitle);
            break;
          case 'multipleChoice':
            form.addMultipleChoiceItem().setTitle(item.questionTitle).setChoiceValues(item.options.split(','));
            break;
          case 'checkboxes':
            form.addCheckboxItem().setTitle(item.questionTitle).setChoiceValues(item.options.split(','));
            break;
          case 'dropdown':
            form.addListItem().setTitle(item.questionTitle).setChoiceValues(item.options.split(','));
            break;
        }
      }

      return true;
    } else {
      return false;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

/**
 * This function is a trigger that runs when a Google Form is submitted.
 * To use this, you must manually create an onFormSubmit trigger for each form and associate it with this function.
 */
function onFormSubmit(e) {
  try {
    const form = e.source;
    const formId = form.getId();
    const respondentEmail = e.response.getRespondentEmail();
    const itemResponses = e.response.getItemResponses();

    const responses = {};
    for (const itemResponse of itemResponses) {
      responses[itemResponse.getItem().getTitle()] = itemResponse.getResponse();
    }

    // Log the submission
    createFormSubmission({ formId: formId, respondentEmail: respondentEmail, responses: JSON.stringify(responses) });

    // Update task status if linked
    const tasks = getTasksByFormId(formId);
    if (tasks) {
      for (const task of tasks) {
        const assignments = getAssignmentsByTaskId(task.taskId);
        if (assignments) {
          for (const assignment of assignments) {
            if (assignment.memberId === getMemberByEmail(respondentEmail).memberId) {
              server_updateTaskStatus(assignment.assignmentId, 'Completed');
            }
          }
        }
      }
    }

    // Handle attendance logging
    if (form.getTitle().endsWith(' Attendance')) {
      const eventName = form.getTitle().replace(' Attendance', '');
      const member = getMemberByEmail(respondentEmail);
      if (member) {
        const attendanceLogs = getAttendanceLogs(member.memberId);
        if (attendanceLogs) {
          for (const log of attendanceLogs) {
            if (log.eventName === eventName) {
              log.status = 'Attended';
              updateAttendanceLog(log);
              break;
            }
          }
        }
      }
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
  }
}

function getAvailableForms(memberId) {
  try {
    const allForms = getAllFormDefinitions();
    const submittedForms = getSubmittedForms(memberId);

    if (allForms) {
      if (submittedForms) {
        const availableForms = allForms.filter(form => !submittedForms.includes(form.googleFormId));
        return availableForms;
      } else {
        return allForms;
      }
    } else {
      return null;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}
