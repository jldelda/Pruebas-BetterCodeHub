# coding: utf-8
import requests
import pandas as pd
from pandas.io.json import json_normalize
import hashlib
import datetime
import json
import time


MERGE_FIELD_DICT={
    'FNAME': {
        'es': 'Participante',
        'en': 'Participant',
        'pt': 'Participante',
        'fr': 'Participant'
    }
}

def urljoin(*args):
    return '/'.join(args)

def _get(url, **kwargs):
    """
    Generic get
    :param url: mailchimp get api url including api version (e.g. https://xxx.api.mailchimp.com/3.0/ )
    :param kwargs: any extra params, usually at least includes headers
    :return: json url object
    """
    r = requests.get(url, **kwargs)
    return r.json()


def _post(url, **kwargs):
    """
    Generic get
    :param url: mailchimp api version (e.g. https://xxx.api.mailchimp.com/3.0/ )
    :param kwargs: data: data to post and headers
    :return: pandas DataFrame
    """
    r = requests.post(url, **kwargs)
    return r.json()

def _put(url,  **kwargs):
    """
    Generic get
    :param url: mailchimp put api (e.g. https://xxx.api.mailchimp.com/3.0/ )
    :param kwargs: data: data to post and headers
    :return: pandas DataFrame
    """

    r = requests.put(url, **kwargs)
    return r.json()


def get_templates(url, **kwargs):
    """
    Get list
    :param url:  mailchimp url including api version (e.g. https://xxx.api.mailchimp.com/3.0/ )
    :param kwargs: any extra params, usually at least includes headers
    :return: pandas DataFrame with id and name [{:id, :name}]
    """
    templates = pd.DataFrame(_get(urljoin(url, 'templates'), **kwargs)['templates'])
    return templates[['id', 'name']]


def create_merge_field(list, url, **kwargs):
    """
    Define merge_fields on a mail list
    :param list: list id
    :param url: mailchimp url including api version (e.g. https://xxx.api.mailchimp.com/3.0/ )
    :param kwargs: data={merge_field data}, headers
    :return:
    """
    return _post(urljoin(url,'lists',list,'merge-fields'), **kwargs)


def update_list(id, name, language, list_info, users_info,  url, **kwargs):
    """
    Update mail list in mailchimp

    :param id: edx course code
    :param name: edx course name
    :param language: edx course language
    :param list_info: general information about list
    :param users_info: users to update in the list
    :param url: mailchimp url including api version (e.g. https://xxx.api.mailchimp.com/3.0/ )
    :param kwargs: any extra params, usually at least includes headers, data=[users emails]
    :return: mailchimp list id
    """
    mail_lists = pd.DataFrame(_get(urljoin(url, 'lists'), **kwargs)['lists'])[['name', 'id']]
    if id not in mail_lists.name.values:

        merge_fields = [
            {"name":"Course Name", "type":"number", "tag":"COURSE", "default_value":name.encode("utf-8")},
            {"name":"Course Link", "type":"number", "tag":"LINK", "default_value":"https://courses.edx.org/courses/"+id}
        ]

        l_info = {"name": id}
        l_info.update(list_info)
        l_info = json.dumps(l_info)

        list = _post(urljoin(url,'lists'), data=l_info, **kwargs)['id']
        for field_data in merge_fields:
            result = create_merge_field(list, url, data=json.dumps(field_data), **kwargs)
            if result.has_key('status'):
                raise Exception("Unable to create merge field for list {0}:\n{1}".format(id,str(result)))
    else:
        list = mail_lists[mail_lists['name'] == id].id.values[0]

    current_list_members = []
    i=0
    while True:
        tmp = _get(urljoin(url, 'lists', list, 'members'), params={'count': '500', 'offset': i}, **kwargs)['members']
        if len(tmp) > 0:
            current_list_members.extend(tmp)
            i += 500
        else:
            break
    current_list_members = pd.DataFrame(current_list_members)
    if 'email_address' in current_list_members:
        current_list_emails = current_list_members['email_address'].values
    else:
        current_list_emails = []
    new_users=[]
    for email, fname, lname in users_info:
        if len(fname.strip()) == 0:
            fname = MERGE_FIELD_DICT['FNAME'][language]
        data = {"email_address": email,
                "merge_fields": {
                    "FNAME": fname.title(),
                    "LNAME": lname.title().strip()}
                }
        if email in current_list_emails:
            # Update if there are name changes
            subscriber_hash = hashlib.md5()
            subscriber_hash.update(email.lower())
            member_info = current_list_members[current_list_members['email_address'] == email]['merge_fields'].values[0]
            if member_info['FNAME'] != fname.title() or member_info['LNAME'] != lname.title().strip():

                result = json_normalize(_put(urljoin(url, 'lists', list, 'members', subscriber_hash.hexdigest()),
                                             data=json.dumps(data), **kwargs))
                if result['status'].iloc[0] == 400:
                    raise Exception("Unable to update user {0} for list {1}:\n{2}".format(email, id, str(result)))

        else:
            data["status"] = "subscribed"
            new_users.append({
                "method" : "POST",
                "path" : "lists/"+list+"/members",
                "body": json.dumps(data)
            })

    if len(new_users) > 0:
        new_users = {"operations":new_users}
        result = json_normalize(_post(urljoin(url, 'batches'),
                                      data=json.dumps(new_users), **kwargs))

        if isinstance(result['status'].iloc[0], int):
            raise Exception("Unable to add users to list {0}:\n{1}".format(id, str(result)))
        else:
            batch_id = result['id'].iloc[0]
            result = ''
            while result != 'finished':
                time.sleep(10)
                result = json_normalize(_get(urljoin(url, 'batches', batch_id), **kwargs))['status'].iloc[0]

    return list


def create_segment(list, segment_name, users,  url, **kwargs):
    data = json.dumps({'name':segment_name, 'static_segment':users})
    result = json_normalize(_post(urljoin(url, 'lists', list, 'segments'), data=data, **kwargs))
    if 'status' in result:
        raise Exception("Unable to add segment {0} for list {1}:\n{2}".format(segment_name, list, str(result)))
    return result.id.values[0]


def create_campaign(title, list, segment, template, trigger_time, email_subject, reply_to, business,
                    test_emails, url, **kwargs):
    data = json.dumps({
        'recipients': {'list_id':list, 'segment_opts':{'saved_segment_id':segment}},
        'type': 'regular',
        'settings': {'title': title + '_' + datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                     'subject_line': email_subject,
                     'reply_to': reply_to,
                     'from_name': business,
                     'template_id': template}
    })
    campaign = json_normalize(_post(urljoin(url, 'campaigns'), data=data, **kwargs))
    if campaign['status'].iloc[0] == 400:
        raise Exception("Unable to create campaign {0}:\n{1}".format(title, str(campaign)))

    campaign_id = campaign['id'].iloc[0]

    if len(test_emails) > 0 and (''.join(test_emails)).strip() != '':
        data = json.dumps({
            'test_emails': test_emails,
            'send_type':'html'
        })
        campaign = requests.post(urljoin(url, 'campaigns', campaign_id, 'actions/test'), data=data, **kwargs)

    schedule_campaign(campaign_id, title, trigger_time, url, **kwargs)
    return campaign_id


def unschedule_campaign(campaign_id, title, url, **kwargs):
    r = requests.post(urljoin(url, 'campaigns', campaign_id, 'actions/unschedule'), **kwargs)

    if r.status_code == 204:
        print "Campaign successfully unschedule"
    else:
        raise Exception("Unable to unschedule campaign {0}:\n{1}".format(title, str(r.json())))


def schedule_campaign(campaign_id, title, trigger_time, url, **kwargs):
    schedule_time = trigger_time.strftime("%Y-%m-%dT%H:%M+00:00")

    data = json.dumps({
        'schedule_time': schedule_time,  # 2017-02-04T19:13:00+00:00,
        'timewarp': 'false'
    })

    r = requests.post(urljoin(url, 'campaigns', campaign_id, 'actions/schedule'), data=data, **kwargs)

    if r.status_code == 204:
        print "Campaign successfully schedule"
    else:
        raise Exception("Unable to schedule campaign {0}:\n{1}".format(title, str(r.json())))


def delete_campaign(campaign_id, title, url, **kwargs):
    r = requests.delete(urljoin(url, 'campaigns', campaign_id), **kwargs)

    if r.status_code == 204:
        print "Campaign successfully deleted"
    else:
        raise Exception("Unable to delete campaign {0}:\n{1}".format(title, str(r.json())))


def report_campaign_details(campaign_id, report_type, url, **kwargs):
    r = _get(urljoin(url, 'reports', campaign_id, report_type), **kwargs)

    if 'status' not in r:
        print "Campaign {0} report retrieved".format(report_type)
        return r

    else:
        raise Exception("Unable to retrieve {0} report for {1} campaign:\n{2}".
                        format(report_type, campaign_id, str(r)))


def report_campaign_open_details(campaign_id, url, **kwargs):
    current_list_members = []
    data = {}
    i = 0
    while True:
        tmp = report_campaign_details(campaign_id, 'open-details', url, params={'count': '500', 'offset': i}, **kwargs)
        if len(tmp['members']) > 0:
            current_list_members.extend(tmp['members'])
            i += 500
        else:
            data['total_opened'] = tmp['total_opens']
            data['total_users_opened'] = tmp['total_items']
            break
    current_list_members = pd.DataFrame(current_list_members)
    if len(current_list_members) > 0:
        data['members_open'] = current_list_members['email_address']
    else:
        data['members_open'] = []
    return data


def report_campaign_email_activity(campaign_id, url, **kwargs):
    current_list_members = []
    data = {}
    i = 0
    while True:
        tmp = report_campaign_details(campaign_id, 'email-activity', url, params={'count': '500', 'offset': i}, **kwargs)
        if len(tmp['emails']) > 0:
            current_list_members.extend(tmp['emails'])
            i += 500
        else:
            break
    current_list_members = pd.DataFrame(current_list_members)
    return current_list_members
