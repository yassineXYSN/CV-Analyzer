import requests
import os

hr_email = [
    "sarah.hr@companyexample.com",
    "⏰ Reminder: Interview starting in 5 minutes",
    """
    <html>
        <body style="font-family: Arial; line-height: 1.5;">
            <h2>Interview Reminder</h2>
            <p>Hello Sarah,</p>
            <p>This is a quick reminder that your interview with <strong>John Doe</strong> for the position 
            of <strong>Software Engineer</strong> will start in <strong>5 minutes</strong>.</p>
            <p><a href="https://meet.companyexample.com/hr-room-123" 
                style="background-color:#007BFF; color:#fff; padding:10px 15px; 
                text-decoration:none; border-radius:5px;">Join the Meeting</a></p>
            <p>Thank you,<br>HR Interview Bot</p>
        </body>
    </html>
    """,
    "Hello Sarah,\n\nThis is a quick reminder that your interview with John Doe for the position of Software Engineer will start in 5 minutes.\n\nJoin the meeting: https://meet.companyexample.com/hr-room-123\n\n- HR Interview Bot",
    0  # 5 minutes in seconds
]
candidate_email = [
    "john.doe@email.com",
    "📅 Interview Confirmation — Software Engineer Position",
    """
    <html>
        <body style="font-family: Arial; line-height: 1.5;">
            <h2>Interview Scheduled</h2>
            <p>Hello John,</p>
            <p>Your interview for the position of <strong>Software Engineer</strong> 
            has been scheduled on <strong>Monday, 21 October 2025 at 09:00 AM</strong>.</p>
            <p>Meeting link: 
            <a href="https://meet.companyexample.com/candidate-room-456">Join Meeting</a></p>
            <p>Please make sure to join on time. Good luck!</p>
            <p>Best regards,<br>Recruitment Team</p>
        </body>
    </html>
    """,
    "Hello John,\n\nYour interview for the position of Software Engineer has been scheduled on Monday, 21 October 2025 at 09:00 AM.\nMeeting link: https://meet.companyexample.com/candidate-room-456\n\nPlease make sure to join on time.\n\nBest,\nRecruitment Team"
]


payload = {
    "hr_email": hr_email,
    "candidate_email": candidate_email,
    "wait": hr_email[4]
}
url ="https://gaxopin551.app.n8n.cloud/webhook-test/send-emails-with-link"

try:
    response = requests.post(url, json=payload, timeout=2)
    print("Request sent successfully:", response.status_code)
    print("Response:", response.text)
except requests.exceptions.Timeout:
    print("✅ Request timed out (expected) — continuing without waiting.")
except requests.exceptions.RequestException as e:
    print("⚠️ Request failed:", e)