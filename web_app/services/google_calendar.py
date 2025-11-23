"""Google Calendar integration service."""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from shared_utils.logger import get_logger
from shared_utils.exceptions import SLRException

logger = get_logger(__name__)


class GoogleCalendarService:
    """Service for interacting with Google Calendar API."""

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, service_account_file: Optional[str] = None):
        """
        Initialize Google Calendar service.

        Args:
            service_account_file: Path to service account JSON file
        """
        self.service_account_file = service_account_file or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE"
        )
        self._service = None

    def _get_service(self):
        """Get or create Google Calendar service."""
        if self._service is None:
            try:
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_file, scopes=self.SCOPES
                )
                self._service = build("calendar", "v3", credentials=credentials)
                logger.info("Google Calendar service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Calendar service: {e}")
                raise SLRException(f"Failed to initialize Calendar service: {e}")

        return self._service

    def create_event(
        self,
        calendar_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a calendar event.

        Args:
            calendar_id: ID of the calendar
            summary: Title of the event
            start_time: Start datetime
            end_time: End datetime
            description: Optional event description
            location: Optional event location
            attendees: Optional list of attendee email addresses

        Returns:
            Event metadata including ID

        Raises:
            SLRException: If creation fails
        """
        try:
            service = self._get_service()

            event = {
                "summary": summary,
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "America/Los_Angeles",
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "America/Los_Angeles",
                },
            }

            if description:
                event["description"] = description
            if location:
                event["location"] = location
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            result = (
                service.events()
                .insert(calendarId=calendar_id, body=event, sendUpdates="all")
                .execute()
            )

            logger.info(f"Created event: {result.get('summary')} (ID: {result.get('id')})")
            return result
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            raise SLRException(f"Failed to create event: {e}")

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update a calendar event.

        Args:
            calendar_id: ID of the calendar
            event_id: ID of the event to update
            summary: Optional new title
            start_time: Optional new start time
            end_time: Optional new end time
            description: Optional new description
            location: Optional new location
            attendees: Optional new list of attendees

        Returns:
            Updated event metadata

        Raises:
            SLRException: If update fails
        """
        try:
            service = self._get_service()

            # Get existing event
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            # Update fields
            if summary:
                event["summary"] = summary
            if start_time:
                event["start"] = {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "America/Los_Angeles",
                }
            if end_time:
                event["end"] = {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "America/Los_Angeles",
                }
            if description:
                event["description"] = description
            if location:
                event["location"] = location
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            result = (
                service.events()
                .update(calendarId=calendar_id, eventId=event_id, body=event, sendUpdates="all")
                .execute()
            )

            logger.info(f"Updated event: {result.get('id')}")
            return result
        except HttpError as e:
            logger.error(f"Failed to update event: {e}")
            raise SLRException(f"Failed to update event: {e}")

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        """
        Delete a calendar event.

        Args:
            calendar_id: ID of the calendar
            event_id: ID of the event to delete

        Raises:
            SLRException: If deletion fails
        """
        try:
            service = self._get_service()
            service.events().delete(
                calendarId=calendar_id, eventId=event_id, sendUpdates="all"
            ).execute()
            logger.info(f"Deleted event: {event_id}")
        except HttpError as e:
            logger.error(f"Failed to delete event: {e}")
            raise SLRException(f"Failed to delete event: {e}")

    def list_events(
        self,
        calendar_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List events in a calendar.

        Args:
            calendar_id: ID of the calendar
            time_min: Optional minimum time for events
            time_max: Optional maximum time for events
            max_results: Maximum number of results to return

        Returns:
            List of event dictionaries

        Raises:
            SLRException: If listing fails
        """
        try:
            service = self._get_service()

            kwargs = {
                "calendarId": calendar_id,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
            }

            if time_min:
                kwargs["timeMin"] = time_min.isoformat() + "Z"
            if time_max:
                kwargs["timeMax"] = time_max.isoformat() + "Z"

            events_result = service.events().list(**kwargs).execute()
            events = events_result.get("items", [])

            logger.info(f"Listed {len(events)} events")
            return events
        except HttpError as e:
            logger.error(f"Failed to list events: {e}")
            raise SLRException(f"Failed to list events: {e}")

    def get_event(self, calendar_id: str, event_id: str) -> Dict[str, Any]:
        """
        Get a single event.

        Args:
            calendar_id: ID of the calendar
            event_id: ID of the event

        Returns:
            Event metadata

        Raises:
            SLRException: If retrieval fails
        """
        try:
            service = self._get_service()
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            logger.info(f"Retrieved event: {event.get('summary')}")
            return event
        except HttpError as e:
            logger.error(f"Failed to get event: {e}")
            raise SLRException(f"Failed to get event: {e}")
