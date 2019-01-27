from __future__ import print_function
import os
import httplib2
import re

import datetime
import dateutil.parser

import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from subprocess import call

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# https://developers.google.com/people/quickstart/python
SCOPES = 'https://www.googleapis.com/auth/contacts.readonly'
CLIENT_SECRET_FILE = '/Users/nkugland/.credentials/google_api_nk_local_client_id.json'
APPLICATION_NAME = 'contacts API test'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'contacts-api-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

# http://www.worldofchris.com/blog/2012/12/27/fun-with-oauth-gdata-google-apis-client-library-python/
credentials = get_credentials()
auth2token = gdata.gauth.OAuth2Token(client_id=credentials.client_id,
  client_secret=credentials.client_secret,
  scope=SCOPES,
  access_token=credentials.access_token,
  refresh_token=credentials.refresh_token,
  user_agent='sites-test/1.0')

# https://developers.google.com/google-apps/contacts/v3/
client = gdata.contacts.client.ContactsClient(source='contacts-alerter')

auth2token.authorize(client)

#TODO change this to something smarter
max_results = 10000

start_index = 1
query = gdata.contacts.client.ContactsQuery()
query.max_results = max_results
query.start_index = start_index
query.group = 'http://www.google.com/m8/feeds/groups/nkugland%40gmail.com/base/6'

# print(dir(client))
contacts_feed = client.GetContacts(q=query)
groups_feed = client.GetGroups()


# TODO put these into a config file
followup_groups = {'84f82ca08e556da':4,		#times in weeks
				   '5abdac650bbd1b4c':2,
				   '26eba5f10bd7ce63':8,
				  }

now = datetime.datetime.now()

for i, entry in enumerate(contacts_feed.entry):
	# if i in [1, 0]:
		
	# print(entry)
	if len(entry.group_membership_info) > 0:
		# are they in my "followup every 2w" group?
		followup_times = (sorted([y for y in
											[followup_groups.get(x.href.split('/')[-1])
											for x in entry.group_membership_info]
											if y is not None])
		)
		if len(followup_times) > 0:
			print('\n',i)

			shortest_followup_time_weeks = followup_times[0]
			print(shortest_followup_time_weeks)
			
			last_touch_ds = '1000-01-01'
			last_touch_ds_display = 'never'
			if entry.name and entry.name.full_name:
				full_name = entry.name.full_name.text
			if entry.content and entry.content.text:
				notes = entry.content.text
				# print(notes)
				ds_pattern = "(\d{4}-\d\d-\d\d)"
				re_m = re.search(ds_pattern, notes, re.DOTALL)
				if re_m:
					last_touch_ds = re_m.group(1)
					last_touch_ds_display = "on " + last_touch_ds
			print(full_name, last_touch_ds)
			last_touch_dt = dateutil.parser.parse(last_touch_ds)
			if now - last_touch_dt > datetime.timedelta(weeks=shortest_followup_time_weeks):
				print("time to follow up!")

				# post alert
				# also need to change mac notification preference to display style 'alerts' 
				# so these stay on screen until dismissed (in system preference pane)
				os.system("""osascript -e 'display notification "Last touch {ds}" with title "Reach out to {name}"'""".\
					format(name=full_name.replace("'",""),
						   ds=last_touch_ds_display))


# for i, entry in enumerate(groups_feed.entry):
# 	print(entry)
	# if len(entry.group_membership_info) > 0:
	# 	print((entry.group_membership_info[0]))

# def PrintAllContacts(gd_client):
#   feed = gd_client.GetContacts()
#   for i, entry in enumerate(feed.entry):
#     print '\n%s %s' % (i+1, entry.name.full_name.text)
#     if entry.content:
#       print '    %s' % (entry.content.text)
#     # Display the primary email address for the contact.
#     for email in entry.email:
#       if email.primary and email.primary == 'true':
#         print '    %s' % (email.address)
#     # Show the contact groups that this contact is a member of.
#     for group in entry.group_membership_info:
#       print '    Member of group: %s' % (group.href)
#     # Display extended properties.
#     for extended_property in entry.extended_property:
#       if extended_property.value:
#         value = extended_property.value
#       else:
#         value = extended_property.GetXmlBlob()
#       print '    Extended Property - %s: %s' % (extended_property.name, value)