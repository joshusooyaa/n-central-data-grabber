import requests
import base64
import time
import os

class Emailer:
  def __init__(self, config, logger):
    self.client_id = config['microsoft-graph']['client-id']
    self.client_secret = config['microsoft-graph']['client-secret']
    self.tenant_id = config['microsoft-graph']['tenant-id']
    self.token_url = 'https://login.microsoftonline.com/{0}/oauth2/v2.0/token'.format(self.tenant_id)
    self.scope = 'https://graph.microsoft.com/.default'
    self.access_token = None
    self.token_expiration = 0

    self.sender = config['microsoft-graph']['email-details']['sender']
    self.subject = config['microsoft-graph']['email-details']['subject']
    self.body = config['microsoft-graph']['email-details']['body']
    self.recipient = config['microsoft-graph']['email-details']['recipient']
    self.logger = logger
  
  def _get_access_token(self):
    if self.access_token is None or time.time() > self.token_expiration:
      payload = {
        'client_id': self.client_id,
        'scope': self.scope,
        'client_secret': self.client_secret,
        'grant_type': 'client_credentials'
      }
      self.logger.info("Fetching token info from {}".format(self.token_url))
      response = requests.post(self.token_url, data=payload)
      if response.status_code == 200:
        token_info = response.json()
        self.access_token = token_info['access_token']
        self.token_expiration = time.time() + token_info['expires_in'] - 300
      else:
        self.logger.error('Could not obtain access token: {0}'.format(response.text))
        return False

    self.logger.info('Access token obtained')
    return self.access_token

  def _fetch_message(self, subject, files = None):

    if subject == 'api':
      subject = "N-Central Data Collector API Password Expiry"
      body = "The user nocnoticies@ipservices.com has a password expiry soon. Please update the password for this user to prevent the n-central data collection script from failing. Note: Do NOT update the API key. See OA 12916 for more details."
    elif subject == 'graph':
      subject = "N-Central Data Collector Microsoft-Graph Key Expiry"
      body = "The API keys for Microsoft-Graph are set to expire soon. When this expires, the n-central data collection script cannot create a ticket in TOPDesk if it's no longer running."
    elif subject == 'fail':
      subject = "N-Central Data Collector Failed"
      body = """
      The script running in /opt/n-central-data-grabber (main.py) has failed to restart more than 5 times. This is located on 10.30.14.4 (ubuntu server).
      \n
      Steps to potentially resolve this:
      1. Make sure the API user nocnoticies@ipservices.com for N-Central has had a password reset within the last quarter.
      2. If the password reset isn't the issue, you can attempt to restart the service manually:
          - pgrep -f 'main.py'
          - kill (id returned from above)
          - sudo service datamonitor restart
          - view logs in /opt/n-central-data-grabber/logs/log_files/* for details on if it's running properly
          - log.log will tell you immediately if the script is running properly or not, you can check by doing tail -f path-to-log.log to see the latest logs and if it's updating.
      3. All other issues are unknown as these are the only two that have been seen before.
      """

    email = {
      'message': {
        'subject': subject,
        'body': {
          'contentType': 'Text',
          'content': body
        },
        'toRecipients': [
          {
            "emailAddress": {
              "address": self.recipient
            }
          }
        ]
      }
    }

    #if files:
      #attachments = self._configure_files(files)
      #attachment_list = self._fetch_attachments(attachments)
      #if len(attachment_list) >= 1:
      #  email['message']['attachments'] = attachment_list

    self.logger.info('Email configured')
    return email
  
  def _configure_files(self, files):
    attachments = []
    for file in files:
      if file:
        attachments.append({
          'file_path': file,
          'file_name': os.path.basename(file),
          'content_type': 'text/plain'
        })
      else:
        self.logger.error('File does not exist')
    
    return attachments

  def _fetch_attachments(self, attachments):
    attachment_list = []
    for attachment in attachments:
      with open(attachment['file_path'], 'rb') as f:
        content_bytes = f.read()
        content_bytes_base64 = base64.b64encode(content_bytes).decode('utf-8')
      
      attachment_obj = {
        '@odata.type': '#microsoft.graph.fileAttachment',
        'name': attachment['file_name'],
        'contentType': attachment['content_type'],
        'contentBytes': content_bytes_base64
      }
      attachment_list.append(attachment_obj)
      self.logger.info('Attachment appended.')
    
    return attachment_list
  
  def send(self, subject, files=None):
    access_token = self._get_access_token()
    if (access_token):
      url = 'https://graph.microsoft.com/v1.0/users/{0}/sendMail'.format(self.sender)
      headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
        'Content-Type': 'application/json'
      }
      email = self._fetch_message(subject, files)

      response = requests.post(url, headers=headers, json=email)
      if response.status_code == 202:
        self.logger.info('Email successfully sent.')
      else:
        self.logger.error('Could not send email: {0}'.format(response.text))
    else:
      return False