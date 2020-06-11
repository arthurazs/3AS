from matplotlib.pyplot import bar, savefig, ylabel, subplots_adjust
from matplotlib import rc, rcParams
from csv import reader
from itertools import islice
from numpy import array as np_array, mean as np_mean
from scipy.stats import sem, t


def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np_array(data)
    n = len(a)
    mean, se = np_mean(a), sem(a)
    error = se * t.ppf((1 + confidence) / 2., n-1)
    return mean, error


def ip_adder(value):
    # IP Address Adder for netmask /16
    rest, network, host = value.rsplit('.', 2)
    host = (int(host) % 254) + 1
    network = int(network) + int(host == 1)
    return rest + '.' + str(network) + '.' + str(host)


def mac_adder(value):
    # MAC Address Adder
    rest, network, host = value.rsplit(':', 2)
    host = (int(host, 16) % 254) + 1
    network = int(network, 16) + int(host == 1)
    host = hex(host)[2:].zfill(2).lower()
    network = hex(network)[2:].zfill(2).lower()
    return rest + ':' + network + ':' + host


rcParams['font.family'] = 'Times New Roman'
rcParams['font.size'] = '18'
rcParams['figure.figsize'] = [7, 5]
subplots_adjust(left=.13, bottom=.06, right=.99, top=.99)
rcParams['errorbar.capsize'] = 7
rc('savefig', dpi=300, format='png')
ylabel('Time (ms)')
width = .5
blue = (0.2588, 0.4433, 1.0)

NUM_EV = 3000
evs = {}
controller_mac = '10.0.1.1'
auth_ip = '10.0.1.2'
auth_mac = '00:00:00_00:00:02'
scada_ip = '10.0.1.3'
ip = scada_ip
mac = '00:00:00_00:00:03'
mac2ip = {}
for index in range(1, NUM_EV + 1):
    ip = ip_adder(ip)
    mac = mac_adder(mac)
    mac2ip[mac] = ip


with open('scada.csv') as csv_file:
    scada = reader(csv_file, delimiter=',')

    for row in islice(scada, 1, None):  # skip header
        time, source, destination, protocol, info, length = row
        time = float(time) * 1000
        ev = destination if source == scada_ip else source
        if ev not in evs:
            evs[ev] = {'MMS': {'start': time}}
        else:
            if protocol == 'MMS':
                evs[ev]['MMS']['finish'] = time
                evs[ev]['MMS']['total'] = time - evs[ev]['MMS']['start']

with open('sdn-hostapd.csv') as csv_file:
    hostapd = reader(csv_file, delimiter=',')

    rows = islice(hostapd, 1, None)
    for row in rows:  # skip header
        time, source, destination, protocol, info, length = row
        time = float(time) * 1000
        if protocol == 'TCP':
            start = time
            next(rows)
            next(rows)
            info = next(rows)[-2]
            ev_mac = info.split('/')[2]
            ev_mac = ev_mac[:8] + '_' + ev_mac[9:]
            ev = mac2ip[ev_mac]
            next(rows)
            next(rows)
            next(rows)
            next(rows)
            next(rows)
            time = float(next(rows)[0]) * 1000
            evs[ev]['REST'] = {'start': start}
            evs[ev]['REST']['finish'] = time
            evs[ev]['REST']['total'] = time - start
        else:
            ev_mac = destination if source == auth_mac else source
            ev = mac2ip[ev_mac]
            if protocol == 'EAPOL':
                evs[ev]['AUTH'] = {'start': time}
            else:
                evs[ev]['AUTH']['finish'] = time
                evs[ev]['AUTH']['total'] = time - evs[ev]['AUTH']['start']


of = []
mms = []
auth = []
rest = []
total = []
apagar = []
for ev, protocols in evs.items():
    of.append(protocols['MMS']['start'] - protocols['REST']['finish'])
    mms.append(protocols['MMS']['total'])
    auth.append(protocols['AUTH']['total'])
    rest.append(protocols['REST']['total'])
    total.append(protocols['MMS']['finish'] - protocols['AUTH']['start'])

of_mean, of_error = mean_confidence_interval(of)
mms_mean, mms_error = mean_confidence_interval(mms)
auth_mean, auth_error = mean_confidence_interval(auth)
rest_mean, rest_error = mean_confidence_interval(rest)
total_mean, total_error = mean_confidence_interval(total)

bar('MMS', mms_mean, width, color=blue,
    edgecolor='black', yerr=mms_error)
bar('Rest', rest_mean, width, color=blue,
    edgecolor='black', yerr=rest_error)
bar('Auth', auth_mean, width, color=blue,
    edgecolor='black', yerr=auth_error)
bar('OF', of_mean, width, color=blue,
    edgecolor='black', yerr=of_error)
bar('Total', total_mean, width, color=blue,
    edgecolor='black', yerr=total_error)

savefig('3plot.png')
