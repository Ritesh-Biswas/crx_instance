import requests
from datetime import date, datetime 
import calendar
from allauth.socialaccount.models import SocialToken
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def get_google_drive_files(request):
    def fetch_files_in_folder(folder_id="root"):
        files = []
        try:
            token = SocialToken.objects.get(
                account__user=request.user, account__provider="google"
            )
            headers = {"Authorization": f"Bearer {token.token}"}
            params = {
                "q": f"'{folder_id}' in parents",
                "fields": "files(id, name, mimeType, createdTime, modifiedTime, webViewLink, webContentLink)"
            }
            response = requests.get(
                "https://www.googleapis.com/drive/v3/files", headers=headers, params=params
            )
            files_data = response.json()
            for file in files_data.get("files", []):
                file_info = {
                    "name": file.get("name", "No Name"),
                    "id": file.get("id", ""),
                    "mimeType": file.get("mimeType", ""),
                    "createdTime": file.get("createdTime", ""),
                    "modifiedTime": file.get("modifiedTime", ""),
                    "viewLink": file.get("webViewLink", ""),
                    "downloadLink": file.get("webContentLink", ""),
                    "children": []
                }
                if file.get("mimeType") == "application/vnd.google-apps.folder":
                    file_info["children"] = fetch_files_in_folder(file.get("id"))
                files.append(file_info)
        except SocialToken.DoesNotExist:
            print("No valid Google token found for user:", request.user)
        return files

    drive_files = fetch_files_in_folder()
    return drive_files


def get_calendar_events(request):
    today = date.today()
    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))

    # Get first day of the month and total days in month
    first_weekday, num_days = calendar.monthrange(year, month)

    # Adjust first_weekday to match Sunday as the first day of the week
    first_weekday = (first_weekday + 1) % 7

    # Calculate previous and next month for navigation
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    # Build calendar weeks with empty slots for non-month days
    month_weeks = []
    week = []

    # Add padding for previous month's days
    prev_month_days = calendar.monthrange(prev_year, prev_month)[1]
    for i in range(first_weekday):
        day = prev_month_days - (first_weekday - 1) + i
        full_date = f"{prev_year}-{prev_month:02d}-{day:02d}"
        week.append({"day": day, "full_date": full_date, "current_month": False})

    # Fill actual month days
    for day in range(1, num_days + 1):
        full_date = f"{year}-{month:02d}-{day:02d}"
        week.append({"day": day, "full_date": full_date, "current_month": True})

        if len(week) == 7:
            month_weeks.append(week)
            week = []

    # Add padding for next month's days
    next_day = 1
    while len(week) < 7:
        full_date = f"{next_year}-{next_month:02d}-{next_day:02d}"
        week.append({"day": next_day, "full_date": full_date, "current_month": False})
        next_day += 1

    if week:
        month_weeks.append(week)

    # Fetch Google Calendar events
    events = []
    try:
        token = SocialToken.objects.get(
            account__user=request.user, account__provider="google"
        )
        headers = {"Authorization": f"Bearer {token.token}"}
        response = requests.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers=headers,
        )
        events_data = response.json()
 
        for event in events_data.get("items", []):
            start = event.get("start", {})
            event_date = start.get("dateTime", start.get("date", ""))[
                :10
            ]  # Extract YYYY-MM-DD
            events.append(
                {
                    "summary": event.get("summary", "No Title"),
                    "start_date": event_date,
                    "description": event.get("description", ""),
                    "create_at": event.get("created", ""),
                    "update_at": event.get("updated", ""),
                }
            )

    except SocialToken.DoesNotExist:
        print("No valid Google token found for user:", request.user)

    # Pass context to template
    context = {
        "month_name": calendar.month_name[month],
        "year": year,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "month_weeks": month_weeks,
        "events": events,
    }

    return context

def get_onedrive_files(request):
    """Fetch files from OneDrive using Microsoft Graph API."""
    def fetch_files_in_folder(folder_id=None):
        files = []
        try:
            token = SocialToken.objects.get(account__user=request.user, account__provider="microsoft")
            headers = {"Authorization": f"Bearer {token.token}"}
            url = f"https://graph.microsoft.com/v1.0/me/drive/root/children" if not folder_id else f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            items = response.json().get("value", [])
            for item in items:
                file_info = {
                    "name": item.get("name", "No Name"),
                    "id": item.get("id", ""),
                    "mimeType": "application/vnd.microsoft.folder" if item.get("folder") else item.get("file", {}).get("mimeType", ""),
                    "createdTime": item.get("createdDateTime", ""),
                    "modifiedTime": item.get("lastModifiedDateTime", ""),
                    "viewLink": item.get("webUrl", ""),
                    "downloadLink": item.get("@microsoft.graph.downloadUrl", ""),
                    "children": fetch_files_in_folder(item.get("id")) if item.get("folder") else []
                }
                files.append(file_info)
        except SocialToken.DoesNotExist:
            print("No valid Microsoft token found for user:", request.user)
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch OneDrive files: {str(e)}")
        return files

    drive_files = fetch_files_in_folder()
    return drive_files

def get_outlook_calendar_events(request):
    # Get current date and query parameters
    today = date.today()
    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))

    # Get first day of the month and total days in month
    first_weekday, num_days = calendar.monthrange(year, month)

    # Adjust first_weekday to match Sunday as the first day of the week
    first_weekday = (first_weekday + 1) % 7

    # Calculate previous and next month for navigation
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    # Calculate date range for the entire month
    start_date = datetime(year, month, 1).isoformat() + 'Z'
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day).isoformat() + 'Z'

    # Build calendar weeks with empty slots for non-month days
    month_weeks = []
    week = []

    # Add padding for previous month's days
    prev_month_days = calendar.monthrange(prev_year, prev_month)[1]
    for i in range(first_weekday):
        day = prev_month_days - (first_weekday - 1) + i
        full_date = f"{prev_year}-{prev_month:02d}-{day:02d}"
        week.append({"day": day, "full_date": full_date, "current_month": False})


    # Fill actual month days
    for day in range(1, num_days + 1):
        full_date = f"{year}-{month:02d}-{day:02d}"
        week.append({"day": day, "full_date": full_date, "current_month": True})

        if len(week) == 7:
            month_weeks.append(week)
            week = []

    # Add padding for next month's days
    next_day = 1
    while len(week) < 7:
        full_date = f"{next_year}-{next_month:02d}-{next_day:02d}"
        week.append({"day": next_day, "full_date": full_date, "current_month": False})
        next_day += 1

    if week:
        month_weeks.append(week)

    # Fetch Outlook Calendar events
    events = []
    try:
        token = SocialToken.objects.get(
            account__user=request.user, 
            account__provider="microsoft"
        )
        headers = {"Authorization": f"Bearer {token.token}"}
        
        params = {
            'startDateTime': start_date,
            'endDateTime': end_date,
            '$select': 'subject,start,end,bodyPreview,createdDateTime,lastModifiedDateTime',
            '$orderby': 'start/dateTime'
        }
        
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me/calendarView",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        events_data = response.json()
        print("Fetched events data:", events_data)

        for event in events_data.get("value", []):
            start = event.get("start", {}).get("dateTime", "")[:10]  # Extract YYYY-MM-DD
            events.append({
                "summary": event.get("subject", "No Title"),
                "start_date": start,
                "description": event.get("bodyPreview", ""),
                "create_at": event.get("createdDateTime", ""),
                "update_at": event.get("lastModifiedDateTime", ""),
            })

    except SocialToken.DoesNotExist:
        print("No valid Microsoft token found for user:", request.user)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch Outlook Calendar events: {str(e)}")

    # Prepare context similar to Google Calendar
    context = {
        "month_name": calendar.month_name[month],
        "year": year,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "month_weeks": month_weeks,
        "events": events,
    }

    return context

import requests
from datetime import datetime

def get_google_calendar_events(calendar_url):
    try:
        print(f"Fetching Google Calendar events from: {calendar_url}")
        return get_google_calendar_events_ics(calendar_url)
    except Exception as e:
        print("Error fetching Google Calendar events:", e)
        return []

def get_google_calendar_events_ics(calendar_url):
    try:
        response = requests.get(calendar_url)
        if response.status_code == 200:
            events = parse_ics(response.text)
            return events
        else:
            return []
    except Exception as e:
        print("Error fetching Google Calendar ICS events:", e)
        return []

# def get_outlook_calendar_events(calendar_url):
#     try:
#         response = requests.get(calendar_url)
#         if response.status_code == 200:
#             events = parse_ics(response.text)
#             return events
#         else:
#             return []
#     except Exception as e:
#         print("Error fetching Outlook Calendar events:", e)
#         return []

def parse_ics(ics_data):
    events = []
    lines = ics_data.splitlines()
    event = {}
    in_event = False
    current_key = None

    def format_ics_datetime(dt_str):
        try:
            dt_str = dt_str.rstrip('Z')
            if 'T' in dt_str:
                return datetime.strptime(dt_str, '%Y%m%dT%H%M%S').strftime('%Y-%m-%d %I:%M %p')
            return datetime.strptime(dt_str, '%Y%m%d').strftime('%Y-%m-%d')
        except Exception:
            return dt_str

    for line in lines:
        line = line.strip()

        if line == "BEGIN:VEVENT":
            in_event = True
            event = {}
            current_key = None

        elif line == "END:VEVENT":
            # Detect type of event
            summary = event.get('summary', '').lower()
            description = event.get('description', '').lower()
            categories = event.get('categories', '').lower()

            if 'birthday' in summary or 'birthday' in description or 'birthday' in categories:
                event['type'] = 'Birthday'
            elif 'anniversary' in summary or 'anniversary' in description or 'anniversary' in categories:
                event['type'] = 'Anniversary'
            else:
                event['type'] = 'General'

            events.append(event)
            in_event = False
            event = {}
            current_key = None

        elif in_event:
            # Handle folded/multiline fields
            if line.startswith(" "):
                if current_key:
                    event[current_key] += line[1:]
            elif ":" in line:
                key, value = line.split(":", 1)
                key = key.split(";")[0].strip()  # Remove any params
                value = value.strip()
                current_key = key.lower()

                if key == "SUMMARY":
                    event["summary"] = value
                elif key == "DESCRIPTION":
                    event["description"] = value
                elif key == "DTSTART":
                    event["start"] = format_ics_datetime(value)
                elif key == "DTEND":
                    event["end"] = format_ics_datetime(value)
                elif key == "LOCATION":
                    event["location"] = value
                elif key == "UID":
                    event["uid"] = value
                elif key == "ORGANIZER":
                    event["organizer"] = value
                elif key == "CATEGORIES":
                    event["categories"] = value
                elif key == "STATUS":
                    event["status"] = value
                elif key == "CREATED":
                    event["created"] = format_ics_datetime(value)
                elif key == "LAST-MODIFIED":
                    event["last_modified"] = format_ics_datetime(value)
                else:
                    event[current_key] = value  # Store unknown fields just in case
    return events

def fetch_calendar_events(calendar_url):
    if "google.com" in calendar_url or calendar_url.endswith(".ics"):
        return get_google_calendar_events_ics(calendar_url)
    elif "outlook.com" in calendar_url or "office365.com" in calendar_url:
        return get_outlook_calendar_events(calendar_url)
    else:
        print("Unsupported calendar URL format.")
        return []
