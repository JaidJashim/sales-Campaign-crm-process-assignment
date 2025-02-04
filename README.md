# Sales Campaign Automation

This repository contains a Python script designed to automate the process of lead verification and outreach for a sales campaign. The script integrates with **Google Sheets** for data management, uses the **NeverBounce API** for email verification, and leverages the **OpenAI API** for generating **summary**, **insights** and **recommendations**. Additionally, it utilizes **SMTP** for sending outreach emails and schedules tasks using the **APScheduler** library.It ensures efficient sales outreach with **automated scheduling and fallback mechanisms**

## ✨ Features

* **Lead Management:** Reads and updates leads from Google Sheets.
* **Email Verification:** Uses **NeverBounce API** to validate email addresses.
* **Automated Outreach:** Sends personalized emails via **SMTP**.
* **AI-Powered Insights & Recommendations:** Uses **GPT-4** to generate campaign analysis.
* **Automated Scheduling:** Runs at configurable intervals using **APScheduler**.

## 🛠 Technologies Used

* **Python** (version 3.12.8)
* **Google Sheets API**
* **NeverBounce API** (for email verification)
* **OpenAI GPT-4 API** (for AI-generated insights & recommendations)
* **SMTP (smtplib)** (for sending emails)
* **APScheduler** (for automation & scheduling)

## ⚙️ Installation/Setup

1. **Clone the repository**
2. **Install dependencies**
3. **Google Sheets API Credentials**:

   - Create a service account in the Google Cloud Console and download the JSON credentials file.
   - Place the JSON file in the project root and name it `service_account.json`.
4. **Set up environment variables**:
   Create a `.env` file in the project root and add the following environment variables:

   ```env
   NEVERBOUNCE_API_KEY=your_neverbounce_api_key
   SMTP_SERVER=your_smtp_server
   SMTP_PORT=your_smtp_port
   SMTP_USER_SENDER=your_smtp_user_sender
   SMTP_USER_RECIEVER=your_smtp_user_reciever
   SMTP_PASSWORD=your_smtp_password
   OPENAI_API_KEY=your_openai_api_key
   google_sheets_id=your_google_sheets_id
   SCHEDULER_INTERVAL_HOURS=your_scheduler_interval_hours
   ```
5. **Run the script:**

```python
python Sales_Campaign_CRM_Performance Summary_with_LLM_power_copy_v2a.py
```

## 🔍 Functionality & Responsibilities

### 📂 **Lead Management**

* `read_google_sheets()`: Reads lead data from Google Sheets.
* `write_google_sheets(df)`: Updates Google Sheets with lead processing results.

### ✅ **Email Verification**

* `verify_email_neverbounce(email)`: Verifies email validity using NeverBounce API.
* `agent_a_verify_leads(df)`: Processes email verification and updates lead status.

### 📧 **Email Outreach**

* `generate_insights(df)`: Uses GPT-4 to generate insights from campaign data.
* `generate_recommendations(df)`: Uses GPT-4 to generate actionable recommendations.
* `send_email_smtp(lead)`: Sends emails via SMTP, retries on failure, and logs execution.

### 📊 **Campaign Analysis & Reporting**

* `consolidate_results(df)`: Summarizes campaign performance and generates insights.
* `agent_b_outreach(df)`: Sends campaign summary emails to stakeholders.

### 🔄 **Automation & Scheduling**

* `scheduled_task()`: Orchestrates lead verification, email outreach, and result storage at scheduled intervals.
* `APScheduler`: Manages periodic execution of the lead processing pipeline.

## 📌 Usage Guide

### 1️⃣ **Ensure Leads Are Available** in Google Sheets with the following structure:

* Lead Name
* Email
* Contact Number
* Company
* Industry
* Email Verified (Y/N)
* Response Status
* Notes

### 2️⃣ **Automation Workflow:**

* Reads new leads from Google Sheets.
* Verifies email addresses using NeverBounce.
* Uses GPT-4 to generate **personalized** campaign insights.
* Sends emails via **SMTP**.
* Analyzes campaign performance and updates Google Sheets.

### 3️⃣ Monitor Logs for Debugging:

* The script logs debug information, warnings, and errors to `sales_campaign.log`.
