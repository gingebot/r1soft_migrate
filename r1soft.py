#!/usr/bin/python
import base64, urllib2, xml.etree.ElementTree, os, sys, socket, tempfile, subprocess, datetime, traceback
from optparse import OptionParser

def log_shell_cmd(cmd, heading):
    p = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
    (output, err) = p.communicate()
    p.wait()
    writer(heading)
    writer(output)

def writer(string):
    print string
    with open('{0}/r1soft_report'.format(data_dir),'a') as report:
        report.write(string)
        report.write('\n')

def test_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((api_host,api_port))
    sock.close()
    if result != 0:
        writer("\nAPI Service is not listening on port {0}, skipping r1soft analysis\n".format(api_port).upper())
        return False
    return True

def set_header(username,password):
    global headers
    auth_key = base64.b64encode('%s:%s' % (username, password))
    headers = {'Authorization': 'Basic %s' % auth_key}

def api_request(url_end_part,data,headers):
    full_url='%s%s' % ('http://{0}:{1}/'.format(api_host,api_port), url_end_part)
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
                if not val:
                    val = ''
                if (len(val) + 2) > fieldlen[key]:
                    fieldlen[key] = (len(val) + 2)
        for key,val in fieldlen.iteritems():
            fstr += '{%s:<%s}' % (key,val)
        writer('\n{0} CONFIGURATION:\n'.format(title).upper())
        for i in data:
            writer(fstr.format(**i))

def analyse(search):
    x = api_request(search['endpoint'],search['soap'],headers)
    with open('{1}/output_{0}.xml'.format(search['space'],data_dir), 'w') as outfile:
        outfile.write(x)
    xmlroot = xml.etree.ElementTree.fromstring(x)
    sd = xmlroot.findall(search['search_path'])
    data_list = []
    for i in sd:
        data = {}
        for x in search['items']:
            data[x] = i.find(x).text
        data_list.append(data)
    if search['p_processors']:
        for i in search['p_processors']:
            data_list = i(data_list)
    return data_list

def add_mount_point(volumes):
    for i in volumes:
        i['mount'] = find_mount_point(i['path'])
    return volumes

def find_mount_point(path):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path

search_values = [
                {'soap':'''
                        <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                        <getVolumes xmlns="http://volume.api.server.backup.r1soft.com/"/>
                        </Body>
                        </Envelope>
                        ''',
                'endpoint': 'Volume?wsdl',
                'search_path': '{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://volume.api.server.backup.r1soft.com/}getVolumesResponse/return',
                'items': ['name', 'path'],
                'space': 'volume',
                'p_processors': [add_mount_point,],
                },
                {'soap':'''
                        <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                        <getDiskSafes xmlns="http://disksafe.api.server.backup.r1soft.com/"/>
                        </Body>
                        </Envelope>
                        ''',
                'endpoint': 'DiskSafe?wsdl',
                'search_path': '{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://disksafe.api.server.backup.r1soft.com/}getDiskSafesResponse/return',
                'items': ['path', 'description', 'size', 'recoveryPointCount'],
                'space': 'disksafe',
                'p_processors': [],
                },
                {'soap':'''
                        <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                        <getUsers xmlns="http://user.api.server.backup.r1soft.com/"/>
                        </Body>
                        </Envelope>
                        ''',
                'endpoint': 'User?wsdl',
                'search_path': '{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://user.api.server.backup.r1soft.com/}getUsersResponse/return',
                'items': ['username', 'userType'],
                'space' : 'user',
                'p_processors': [],
                },
                {'soap':'''
                        <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                        <getAgents xmlns="http://agent.api.server.backup.r1soft.com/"/>
                        </Body>
                        </Envelope>
                        ''',
                'endpoint': 'Agent?wsdl',
                'search_path': '{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://agent.api.server.backup.r1soft.com/}getAgentsResponse/return',
                'items' : ['description', 'hostname', 'osType'],
                'space' : 'agent',
                'p_processors': [],
                },
                {'soap':'''
                        <Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
                        <Body>
                        <getPolicies xmlns="http://policy.apiV2.server.backup.r1soft.com/"/>
                        </Body>
                        </Envelope>
                        ''',
                'endpoint': 'Policy2?wsdl',
                'search_path': '{http://schemas.xmlsoap.org/soap/envelope/}Body/{http://policy.apiV2.server.backup.r1soft.com/}getPoliciesResponse/return',
                'items' : ['description', 'name', 'enabled', 'replicationScheduleFrequencyType'],
                'space' : 'policy',
                'p_processors': [],
                },
                ]

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-u', '--username', help='r1soft username, overrides default armoradmin', default='armoradmin')
    parser.add_option('-p', '--password', help='r1soft password')
    parser.add_option('-P', '--port', help='api port, default=9080', default='9080')
    parser.add_option('-i', '--host', help='api host IP, default=127.0.0.1', default='localhost')
    options, args = parser.parse_args()
    global api_port
    global api_host
    api_port=int(options.port)
    api_host='127.0.0.1'
    if not options.password:
        print "\noption -p must be used with a valid password\n"
        sys.exit()
    set_header(options.username,options.password)
    global data_dir
    home=os.getenv("HOME")
    suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    data_dir = '{0}/r1soft_migrate_reports_{1}'.format(home,suffix)
    os.mkdir(data_dir)
    try:
        if test_port():
            try:
                for i in search_values:
                    results = analyse(i)
                    print_data(results, i['space'])
            except Exception as e:
                writer("\nr1soft API service failure, skipping r1soft analysis\n".format(api_port).upper())
                writer(traceback.format_exc())
                writer('\nApplication failed with the following error: %s\n' % e)
        log_shell_cmd( "mount | grep -Ev 'type proc|type sysfs|type devpts|type tmpfs| type binfmt_misc'", '\nCURRENT FILESYSTEM MOUNTS :\n')
        log_shell_cmd("df -h | grep -v /dev/shm", '\nCURRENT DISK USAGE :\n')
        log_shell_cmd("grep -iPv '^[^/|u]|^$' /etc/fstab", '\nCURRENT FSTAB ENTRIES :\n')
        log_shell_cmd("pvs;echo;vgs;echo;lvs", '\nCURRENT LVM CONFIGURATION :\n')
        log_shell_cmd("vgcfgbackup -f {0}/vg_backup_%s".format(data_dir), '\nBACKING UP LVM VG CONFIG(S) TO: {0}/vg_backup_vg\n'.format(data_dir))
        log_shell_cmd("ls -d /sys/block/sd*/device/scsi_device/* |awk -F '[/]' '{print $4,\"- SCSI\",$7}'", '\nDISK SCSI IDs :\n')
        print '\nReport written to {0}/r1soft_report\n'.format(data_dir)
    except Exception as e:
        traceback.print_exc()
        print '\nApplication failed with the following error: %s\n' % e

