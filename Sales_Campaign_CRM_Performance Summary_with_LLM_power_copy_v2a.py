
import pandas as pd
import re
import random
import time
import os
import logging
import concurrent.futures
import requests
import smtplib

from openai import OpenAI
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.blocking import BlockingScheduler
from googleapiclient.discovery import build
from google.oauth2 import service_account



# API Credentials (Use environment variables for security)
NEVERBOUNCE_API_KEY = os.getenv("NEVERBOUNCE_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER_SENDER = os.getenv("SMTP_USER_SENDER")
SMTP_USER_RECIEVER = os.getenv("SMTP_USER_RECIEVER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Configure logging for debugging and tracking process execution
logging.basicConfig(filename='sales_campaign.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')



# Google Sheets API Credentials
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "service_account.json"
SPREADSHEET_ID = os.getenv("google_sheets_id")


# Configurable scheduling interval with dynamic adjustment
SCHEDULER_INTERVAL_HOURS = int(os.getenv("SCHEDULER_INTERVAL_HOURS", 1))

def read_google_sheets():
    """Reads lead data from Google Sheets into a DataFrame."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
    values = result.get('values', [])
    if not values:
        logging.warning("No data found in Google Sheets.")
        return pd.DataFrame()
    df = pd.DataFrame(values[1:], columns=values[0])
    logging.info("Successfully fetched data from Google Sheets.")
    return df

def write_google_sheets(df):
    """Writes updated lead data back to Google Sheets."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    body = {'values': [df.columns.tolist()] + df.values.tolist()}
    sheet.values().update(spreadsheetId=SPREADSHEET_ID, range="Sheet1",
                          valueInputOption="RAW", body=body).execute()
    logging.info("Successfully updated Google Sheets with modified rows.")

def agent_a_verify_leads(df):
    """Agent A verifies lead emails using NeverBounce."""
    if df.empty or 'Email' not in df.columns:
        logging.warning("No leads available for verification.")
        return df
    if 'Email Verified' not in df.columns:
        df['Email Verified'] = pd.Series(pd.NA, index=df.index)
    logging.debug("Starting email verification process using parallel execution.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(verify_email_neverbounce, df['Email']))
    df['Email Verified'] = ['Y' if res else 'N' for res in results]
    logging.info(f"Email verification completed: {df['Email Verified'].value_counts().to_dict()}")
    return df

def verify_email_neverbounce(email):
    """Validates an email using the NeverBounce API."""
    if not NEVERBOUNCE_API_KEY:
        logging.error("NeverBounce API Key is missing. Email verification cannot proceed.")
        return False
    url = "https://api.neverbounce.com/v4/single/check"
    params = {"key": NEVERBOUNCE_API_KEY, "email": email}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or "result" not in data:
            logging.warning(f"Unexpected API response: {data}")
            return False
        return data.get("result", "") == "valid"
    except requests.exceptions.RequestException as e:
        logging.exception(f"NeverBounce API email verification failed for {email}: {e}")
        return False





def consolidate_results(df):
    """
    Summarizes the campaign progress and generates insights using LLM.
    Returns a dictionary with total leads, verified leads, interested leads, insights, and recommendations.
    """
    total_leads = len(df)
    verified_leads = len(df[df['Email Verified'] == 'Y'])
    interested_leads = len(df[df['Response Status'] == 'Interested'])

    # Basic summary
    summary = {
        'Total Leads': total_leads,
        'Verified Leads': verified_leads,
        'Interested Leads': interested_leads
    }

    # Generate insights using LLM
    insights = generate_insights(df)
    recommendations = generate_recommendations(df)

    # Combine summary, insights, and recommendations
    summary['Insights'] = insights
    summary['Recommendations'] = recommendations

    logging.info(f"Campaign Summary: {summary}")
    return summary

def generate_insights(df):
    """
    Generates insights based on the campaign data using LLM.
    """
    total_leads = len(df)
    verified_leads = len(df[df['Email Verified'] == 'Y'])
    interested_leads = len(df[df['Response Status'] == 'Interested'])

    # Example prompt for LLM
    prompt = f"""
    Based on the following campaign data:
    - Total Leads: {total_leads}
    - Verified Leads: {verified_leads}
    - Interested Leads: {interested_leads}
    Provide detailed insights on the campaign performance, including trends, patterns, and areas for improvement.
    """

    # Call OpenAI API to generate recommendations
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.Completion.create(
        prompt=prompt,
        max_tokens=300
    )


    insights = response.choices[0].text.strip()
    logging.info(f"Generated Insights: {insights}")
    return insights

def generate_recommendations(df):
    """
    Generates recommendations based on the campaign data using LLM.
    """
    total_leads = len(df)
    verified_leads = len(df[df['Email Verified'] == 'Y'])
    interested_leads = len(df[df['Response Status'] == 'Interested'])

    # Example prompt for LLM
    prompt = f"""
    Based on the following campaign data:
    - Total Leads: {total_leads}
    - Verified Leads: {verified_leads}
    - Interested Leads: {interested_leads}
    Provide actionable recommendations to improve the campaign performance, focusing on increasing engagement and conversion rates.
    """

    # Call OpenAI API to generate recommendations
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.Completion.create(
        prompt=prompt,
        max_tokens=300
    )

    recommendations = response.choices[0].text.strip()
    logging.info(f"Generated Recommendations: {recommendations}")
    return recommendations



def agent_b_outreach(df):
    """Agent B sends outreach emails using SMTP."""
    def send_email_smtp(lead):
        """Sends email using SMTP with retry mechanism."""
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER_SENDER
            msg['To'] = SMTP_USER_RECIEVER
            msg['Subject'] = "Campaign Performance Summary Report with Insights and Recommendations"
            # Apply consolidate_results to the DataFrame
            summary = consolidate_results(df)

            # Format the summary for email
            email_body = f"""
            Dear Stakeholders,

            Here is the summary of our recent campaign performance:

            Total Leads: {summary['Total Leads']}
            Verified Leads: {summary['Verified Leads']}
            Interested Leads: {summary['Interested Leads']}

            Insights:
            {summary['Insights']}

            Recommendations:
            {summary['Recommendations']}

            Best regards,
            Chief Lead Generation Specialist

            """

            msg.attach(MIMEText(email_body, 'plain'))
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER_SENDER, SMTP_PASSWORD)
            for attempt in range(3):
                try:
                    server.sendmail(SMTP_USER_SENDER, SMTP_USER_RECIEVER, msg.as_string())
                    server.quit()
                    return 'Interested' if random.random() > 0.5 else 'Not Interested'
                except Exception as e:
                    logging.warning(f"SMTP email sending failed (Attempt {attempt+1}/3): {e}")
                    time.sleep(2)
            return 'Failed'
        except Exception as e:
            logging.exception(f"SMTP setup failed: {e}")
            return 'Failed'
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        df['Response Status'] = list(executor.map(send_email_smtp, df.to_dict('records')))
    return df

def scheduled_task():
    """Scheduled task to automate lead processing at configurable intervals."""
    logging.debug("Scheduled task initiated.")
    try:
        leads_df = read_google_sheets()
        if leads_df.empty:
            logging.warning("No valid leads found in Google Sheets. Exiting.")
            return
        leads_df = agent_a_verify_leads(leads_df)
        leads_df = agent_b_outreach(leads_df)
        write_google_sheets(leads_df)
        logging.info("Scheduled task completed successfully.")
    except Exception as e:
        logging.exception("Error occurred during the scheduled task execution.")

scheduler = BlockingScheduler()
scheduler.add_job(scheduled_task, 'interval', hours=SCHEDULER_INTERVAL_HOURS)

if __name__ == '__main__':
    logging.info(f"Starting the scheduler for automated lead processing every {SCHEDULER_INTERVAL_HOURS} hours.")
    scheduler.start()
  
