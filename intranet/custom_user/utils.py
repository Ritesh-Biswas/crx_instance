import os
import requests
from datetime import datetime

# def punch_employee(employee_number, event_type='IN'):
#     username = os.getenv("WORKDAY_API_USERNAME")
#     password = os.getenv("WORKDAY_API_PASSWORD")
#     endpoint = os.getenv("WORKDAY_API_ENDPOINT")

#     print("-- username:", username)
#     print("-- password:", password)
#     print("-- endpoint:", endpoint)

#     now_utc = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

#     soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
# 	<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
# 					xmlns:bsvc="urn:com.workday/bsvc">
# 	<soapenv:Header>
# 		<bsvc:Workday_Common_Header>
# 		<bsvc:Include_Reference_Descriptors_In_Response>true</bsvc:Include_Reference_Descriptors_In_Response>
# 		</bsvc:Workday_Common_Header>
# 		<wsse:Security soapenv:mustUnderstand="1"
# 					xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
# 					xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
# 		<wsse:UsernameToken wsu:Id="bogus">
# 			<wsse:Username>{username}</wsse:Username>
# 			<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
# 		</wsse:UsernameToken>
# 		</wsse:Security>
# 	</soapenv:Header>
# 	<soapenv:Body>
# 		<bsvc:Put_Time_Clock_Events_Request bsvc:version="v40.2">
# 		<bsvc:Time_Clock_Event_Data>
# 			<bsvc:Employee_ID>{employee_number}</bsvc:Employee_ID>
# 			<bsvc:Position_ID>P-{employee_number}</bsvc:Position_ID>
# 			<bsvc:Time_Clock_Event_Date_Time>{now_utc}</bsvc:Time_Clock_Event_Date_Time>
# 			<bsvc:Time_Entry_Code>Hours Worked</bsvc:Time_Entry_Code>
# 			<bsvc:Clock_Event_Type_Reference>
# 			<bsvc:ID bsvc:type="Clock_Event_Type">{event_type}</bsvc:ID>
# 			</bsvc:Clock_Event_Type_Reference>
# 		</bsvc:Time_Clock_Event_Data>
# 		</bsvc:Put_Time_Clock_Events_Request>
# 	</soapenv:Body>
# 	</soapenv:Envelope>"""

#     headers = {
#         "Content-Type": "text/xml;charset=UTF-8",
#         "SOAPAction": "PutTimeClockEvents"
#     }

#     try:
#         response = requests.post(endpoint, data=soap_body.encode('utf-8'), headers=headers)

#         print("---- status:", response.status_code)
#         print("---- response ---", response.text)

#         if 200 <= response.status_code < 300:
#             return True, "Punch processed successfully"
#         else:
#             return False, f"Failed with status {response.status_code}: {response.text}"

#     except Exception as e:
#         return False, f"Request Exception: {str(e)}"

def punch_employee(employee_number, event_type='IN'):
    return False, "Punching is disabled in the current environment."