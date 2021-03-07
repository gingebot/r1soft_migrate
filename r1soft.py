#!/usr/bin/python
import base64
import urllib
import urllib2
import xml.etree.ElementTree as ET
import os

username=os.environ.get('username')
password=os.environ.get('password')
base_url='http://localhost:9080/'

auth_key = base64.b64encode('%s:%s' % (username, password))
headers = {'Authorization': 'Basic %s' % auth_key}

def api_request(url_end_part,data,headers):
   
    full_url='%s%s' % (base_url, url_end_part)
    req = urllib2.Request(full_url,data,headers=headers)
    response = urllib2.urlopen(req)
    the_page = response.read()
    return the_page

def print_data(data,title):
    if not data:
        print '\nNO DATA FOUND FOR : {0}\n'.format(title)
    else:
        fstr = ''
        header = {}
        rule = {}
        fieldlen = {}
        for key,val in data[0].iteritems():
            header[key] = key
            fieldlen[key] = 0
            rule[key] = '----'
        data.insert(0,rule)
        data.insert(0,header)
        for i in data:
            for key,val in i.iteritems():
                if (len(val) + 2) > fieldlen[key]:
                    fieldlen[key] = (len(val) + 2)
        for key,val in fieldlen.iteritems():
            fstr += '{%s:<%s}' % (key,val)
        print '\n{0} :\n'.format(title)
        for i in data:
            print fstr.format(**i)



def perform_volumes_tasks():

    data='''<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
        <Body>
            <getVolumes xmlns="http://volume.api.server.backup.r1soft.com/"/>
        </Body>
        </Envelope>
         '''
    x = api_request('Volume?wsdl',data,headers)
    with open('output_volumes.xml','w') as outfile:
        outfile.write(x)
    vd = get_volumes(x)
    vd = add_mount_point(vd)
    print_data(vd,'VOLUME CONFIGURATION')

def get_volumes(response_xml):
    xmlroot = ET.fromstring(response_xml)
    volumes =  xmlroot.findall('{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://volume.api.server.backup.r1soft.com/}getVolumesResponse/return')
    volumes_data=[]
    for i in volumes:
        volume = {}
        volume['name'] = i.find('name').text
        volume['path'] = i.find('path').text
        volumes_data.append(volume)
    return volumes_data

def add_mount_point(volumes):
    for i in volumes:
        i['mount'] = find_mount_point(i['path'])
    return volumes

def find_mount_point(path):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path


def perform_disk_safe_tasks():
    data='''
        <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
    <Body>
        <getDiskSafes xmlns="http://disksafe.api.server.backup.r1soft.com/"/>
    </Body>
</Envelope>
         '''
    x = api_request('DiskSafe?wsdl',data,headers)
    with open('output_disksafe.xml', 'w') as outfile:
        outfile.write(x)
    dsd = get_disk_safes(x)
    print_data(dsd,'DISK SAFE CONFIGURATION')

def get_disk_safes(response_xml):
    xmlroot = ET.fromstring(response_xml)
    disksafes = xmlroot.findall('{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://disksafe.api.server.backup.r1soft.com/}getDiskSafesResponse/return')
    disk_dafe_data = []
    for i in disksafes:
        ds = {}
        ds['path'] = i.find('path').text
        ds['description'] = i.find('description').text
        ds['size'] = i.find('size').text
        ds['recovery points'] = i.find('recoveryPointCount').text
        disk_dafe_data.append(ds)
    return disk_dafe_data

def perform_user_tasks():
    data='''
        <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
        <Body>
            <getUsers xmlns="http://user.api.server.backup.r1soft.com/"/>
        </Body>
        </Envelope>
        '''
    x = api_request('User?wsdl',data,headers)
    with open('output_user.xml', 'w') as outfile:
        outfile.write(x)
    ud = get_users(x) 
    print_data(ud,'USER CONFIRUGRATION')

def get_users(response_xml):
    xmlroot = ET.fromstring(response_xml)
    users = xmlroot.findall('{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://user.api.server.backup.r1soft.com/}getUsersResponse/return')
    user_data = []
    for i in users:
        user = {}
        user['username'] = i.find('username').text
        user['userType'] = i.find('userType').text
        user_data.append(user)
    return user_data


if __name__ == '__main__':
    perform_volumes_tasks()
    perform_disk_safe_tasks()
    perform_user_tasks()
