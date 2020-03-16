from matplotlib.pyplot import plot, legend, savefig
# from matplotlib.pyplot import annotate
# from matplotlib.pyplot import xlim, ylim
from matplotlib.pyplot import xlabel, ylabel, subplots_adjust
from matplotlib import rc, rcParams
from csv import reader
from itertools import islice


rcParams['font.family'] = 'Times New Roman'
rcParams['font.size'] = '20'
rcParams['figure.figsize'] = [20, 5]
subplots_adjust(left=.06, bottom=.14, right=.98, top=.97)
rc('savefig', dpi=300, format='png')
rc('axes', autolimit_mode='round_numbers', xmargin=0, ymargin=0)
# ylim(top=1500)
# xlim(0, 110)
xlabel('Time (s)')
ylabel('Throughput (kB/s)')

# tshark -r journal/scada.pcap -T fields -e frame.time_epoch -e \
# _ws.col.Source -e _ws.col.Destination  -e _ws.col.Protocol -e \
# _ws.col.Info -e _ws.col.Length -E header=y -E separator=, -E quote=d \
# > scada.csv

# tshark -r journal/sdn-hostapd.pcap -T fields -e frame.time_epoch -e \
# _ws.col.Source -e _ws.col.Destination  -e _ws.col.Protocol -e \
# _ws.col.Info -e _ws.col.Length -E header=y -E separator=, -E quote=d \
# > sdn-hostapd.csv

# tshark -r journal/freeradius.pcap -T fields -e frame.time_epoch -e \
# _ws.col.Source -e _ws.col.Destination  -e _ws.col.Protocol -e \
# _ws.col.Info -e _ws.col.Length -E header=y -E separator=, -E quote=d \
# > freeradius.csv

# tshark -r journal/openflow.pcap -T fields -e frame.time_epoch -e \
# _ws.col.Source -e _ws.col.Destination  -e _ws.col.Protocol -e \
# _ws.col.Info -e _ws.col.Length -E header=y -E separator=, -E quote=d \
# > openflow.csv

STEP = .5
start = None

of_bytes = [0]
of_time = [0]
with open('openflow.csv') as csv_file:
    of = reader(csv_file, delimiter=',')

    of_step = 0
    for row in islice(of, 1, None):  # skip header
        time, source, destination, protocol, info, length = row
        time = float(time)
        length = float(length) / 1000
        start = start if start else time
        now = time - start
        if now < of_step:
            of_time[-1] = now
            of_bytes[-1] = of_bytes[-1] + length
        else:
            of_time.append(now)
            of_bytes.append(length)
            of_step += STEP

auth_bytes = [0]
auth_time = [0]
rest_bytes = [0]
rest_time = [0]
with open('sdn-hostapd.csv') as csv_file:
    hostapd = reader(csv_file, delimiter=',')

    auth_step = 0
    rest_step = 0
    for row in islice(hostapd, 1, None):  # skip header
        time, source, destination, protocol, info, length = row
        time = float(time)
        length = float(length) / 1000
        now = time - start
        if protocol not in ('TCP', 'HTTP'):
            if now < auth_step:
                auth_time[-1] = now
                auth_bytes[-1] = auth_bytes[-1] + length
            else:
                auth_time.append(now)
                auth_bytes.append(length)
                auth_step += STEP
        else:
            if now < rest_step:
                rest_time[-1] = now
                rest_bytes[-1] = rest_bytes[-1] + length
            else:
                rest_time.append(now)
                rest_bytes.append(length)
                rest_step += STEP

scada_bytes = [0]
scada_time = [0]
with open('scada.csv') as csv_file:
    scada = reader(csv_file, delimiter=',')

    scada_step = 0
    for row in islice(scada, 1, None):  # skip header
        time, source, destination, protocol, info, length = row
        time = float(time)
        length = float(length) / 1000
        now = time - start
        if now < scada_step:
            scada_time[-1] = now
            scada_bytes[-1] = scada_bytes[-1] + length
        else:
            scada_time.append(now)
            scada_bytes.append(length)
            scada_step += STEP

radius_bytes = [0]
radius_time = [0]
with open('freeradius.csv') as csv_file:
    radius = reader(csv_file, delimiter=',')

    radius_step = 0
    for row in islice(radius, 1, None):  # skip header
        time, source, destination, protocol, info, length = row
        time = float(time)
        length = float(length) / 1000
        now = time - start
        if now < radius_step:
            radius_time[-1] = now
            radius_bytes[-1] = radius_bytes[-1] + length
        else:
            radius_time.append(now)
            radius_bytes.append(length)
            radius_step += STEP

plot(
    auth_time, auth_bytes,  # linestyle='--', marker=None,
    label='Authentication')
plot(
    rest_time, rest_bytes,  # linestyle='--', marker=None,
    label='Rest API')
plot(
    scada_time, scada_bytes,  # linestyle='--', marker=None,
    label='MMS')
plot(
    radius_time, radius_bytes,  # linestyle='--', marker=None,
    label='RADIUS')
plot(
    of_time, of_bytes,  # linestyle='--', marker=None,
    label='OpenFlow')

# annotate(
#     'IED2 é autorizado', xy=(11.05, .25), xytext=(9, .6),
#     bbox=dict(boxstyle="round4", fc="w", facecolor='gray'),
#     arrowprops=dict(facecolor='gray', arrowstyle='->'),
# )

legend()
savefig('4plot.png')
