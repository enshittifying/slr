// Task Management Engine for the Stanford Law Review Workflow Management System

function server_createTask(title, description, dueDate) {
  try {
    const taskData = {
      title: title,
      description: description,
      dueDate: dueDate,
      linkedFormId: null
    };

    const taskId = createTask(taskData);
    return taskId;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function server_assignTask(taskId, memberId) {
  try {
    const assignmentData = {
      memberId: memberId,
      taskId: taskId,
      status: 'Pending',
      dateCompleted: null
    };

    const assignmentId = createAssignment(assignmentData);
    return assignmentId;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return null;
  }
}

function server_updateTaskStatus(assignmentId, newStatus) {
  try {
    const assignment = getAssignmentById(assignmentId);
    if (assignment) {
      assignment.status = newStatus;
      if (newStatus === 'Completed') {
        assignment.dateCompleted = new Date();
      }
      updateAssignment(assignmentId, assignment);
      return true;
    } else {
      return false;
    }
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function server_getTasksForUser(memberId) {
  try {
    const assignments = getAssignmentsByMemberId(memberId);
    const tasks = [];

    if (assignments) {
      for (const assignment of assignments) {
        const task = getTaskById(assignment.taskId);
        if (task) {
          task.assignmentId = assignment.assignmentId;
          task.status = assignment.status;
          tasks.push(task);
        }
      }
    }

    return tasks;
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return [];
  }
}

function server_assignTaskByEmail(taskId, assigneeEmail) {
  try {
    const member = getMemberByEmail(assigneeEmail);
    if (!member) return { ok: false, error: 'Assignee not found' };
    const assignmentId = createAssignment({
      memberId: member.memberId,
      taskId: taskId,
      status: 'Pending',
      dateCompleted: null
    });
    if (!assignmentId) return { ok: false, error: 'Failed to assign' };
    return { ok: true, assignmentId: assignmentId };
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return { ok: false, error: e.message };
  }
}

function server_deleteTask(taskId) {
  try {
    return deleteTask(taskId);
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return false;
  }
}

function server_getAdminSnapshot() {
  try {
    return {
      members: getAllMembers(),
      tasks: getAllTasks(),
      assignments: getAllAssignments(),
      forms: getAllFormDefinitions(),
      attendanceLogs: getAllAttendanceLogs(),
      systemConfig: getAllSystemConfig()
    };
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return { members: [], tasks: [], assignments: [], forms: [], attendanceLogs: [], systemConfig: [] };
  }
}
function server_createAndAssignTask(title, description, dueDate, assigneeEmail) {
  try {
    const member = getMemberByEmail(assigneeEmail);
    if (!member) {
      return { ok: false, error: 'Assignee not found' };
    }

    const taskId = createTask({
      title: title,
      description: description,
      dueDate: dueDate,
      linkedFormId: null
    });
    if (!taskId) {
      return { ok: false, error: 'Failed to create task' };
    }

    const assignmentId = createAssignment({
      memberId: member.memberId,
      taskId: taskId,
      status: 'Pending',
      dateCompleted: null
    });
    if (!assignmentId) {
      return { ok: false, error: 'Failed to assign task' };
    }

    return { ok: true, taskId: taskId, assignmentId: assignmentId };
  } catch (e) {
    logError({ user: Session.getEffectiveUser().getEmail(), message: e.message, stack_trace: e.stack });
    return { ok: false, error: e.message };
  }
}
