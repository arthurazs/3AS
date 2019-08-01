import matplotlib.pyplot as plt
from matplotlib import rc, rcParams
from csv import reader
from itertools import islice
import pprint
pp = pprint.PrettyPrinter()
print = pp.pprint

rcParams['font.size'] = 12
rcParams['figure.figsize'] = [9.0, 4.5]
rc('savefig', dpi=300, format='png')
rc('axes', autolimit_mode='round_numbers', xmargin=0, ymargin=0)
# tshark -r ied1.pcap -T fields -e frame.time_epoch -e _ws.col.Protocol
# -E header=y -E separator=, -E quote=d > ~/ied1.csv


def fix_start(time_list, bytes_list):
    time_list.insert(0, 0)
    bytes_list.insert(0, 0)
    time_list.insert(1, time_list[1])
    bytes_list.insert(0, 0)


def fix_start_end(time_list, bytes_list, ending_list):
    time_list.insert(0, 0)
    bytes_list.insert(0, 0)
    time_list.insert(1, time_list[1])
    bytes_list.insert(0, 0)
    time_list.append(time_list[-1])
    bytes_list.append(0)
    time_list.append(ending_list[-1])
    bytes_list.append(0)


time_ied1, kbytes_ied1 = [], []
time_ied2, kbytes_ied2 = [], []
time_auth, kbytes_auth = [], []
time_abac, kbytes_abac = [], []
start_time = None
with open('ied1.csv') as csv_file:
    ied1 = reader(csv_file, delimiter=',')

    for row in islice(ied1, 46, None):  # skip ied1 auth
        if not start_time:
            start_time = float(row[0])
        time = float(row[0]) - start_time
        if (time) <= 20:
            kbytes = int(row[1]) / 1024
            time_ied1.append(time)
            kbytes_ied1.append(kbytes)

with open('ied2.csv') as csv_file:
    ied2 = reader(csv_file, delimiter=',')

    for row in islice(ied2, 1, None):  # skip header
        time = float(row[0]) - start_time
        if (time) <= 20:
            kbytes = int(row[1]) / 1024
            if row[2] == 'GOOSE':
                time_ied2.append(time)
                kbytes_ied2.append(kbytes)
            elif row[2] in ('TCP', 'COTP', 'MMS', 'ACSE'):
                time_abac.append(time)
                kbytes_abac.append(kbytes)
            else:
                time_auth.append(time)
                kbytes_auth.append(kbytes)

fix_start(time_ied2, kbytes_ied2)
fix_start_end(time_auth, kbytes_auth, time_ied1)
fix_start_end(time_abac, kbytes_abac, time_ied1)

plt.plot(time_ied1, kbytes_ied1)
plt.plot(time_ied2, kbytes_ied2)
plt.plot(time_auth, kbytes_auth)
plt.plot(time_abac, kbytes_abac)

plt.xlabel('Time(s)')
plt.ylabel('KBytes/s')

plt.annotate(
    'IED1 Sending GOOSE', xy=(3.3, .25), xytext=(0.3, 1.2),
    bbox=dict(boxstyle="round4", fc="w", facecolor='gray'),
    arrowprops=dict(facecolor='gray', arrowstyle='->'),
)

plt.annotate(
    'IED2 Authenticating', xy=(8, .7), xytext=(3.5, .9),
    bbox=dict(boxstyle="round4", fc="w", facecolor='gray'),
    arrowprops=dict(facecolor='gray', arrowstyle='->'),
)

plt.annotate(
    'IED2 Being Authorized', xy=(9.1, .25), xytext=(4, .51),
    bbox=dict(boxstyle="round4", fc="w", facecolor='gray'),
    arrowprops=dict(facecolor='gray', arrowstyle='->'),
)

plt.annotate(
    'IED2 Receiving GOOSE', xy=(9.5, .25), xytext=(10.4, .4),
    bbox=dict(boxstyle="round4", fc="w", facecolor='gray'),
    arrowprops=dict(facecolor='gray', arrowstyle='->'),
)

plt.show()

# print(time_auth[-1])
