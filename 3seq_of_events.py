from matplotlib.pyplot import plot, legend, savefig
# from matplotlib.pyplot import annotate
from matplotlib.pyplot import xlim  # , ylim
from matplotlib.pyplot import xlabel, ylabel, subplots_adjust
from matplotlib import rc, rcParams
from csv import reader
from itertools import islice
from decimal import Decimal

rcParams['font.family'] = 'Times New Roman'
rcParams['font.size'] = '20'
rcParams['figure.figsize'] = [20, 5]
subplots_adjust(left=.06, bottom=.14, right=.98, top=.97)
rc('savefig', dpi=300, format='png')
rc('axes', autolimit_mode='round_numbers', xmargin=0, ymargin=0)
# ylim(top=1500)
xlim(2.1, 2.425)
xlabel('Time (s)')
# ylabel('Throughput (kB/s)')

STEPPER = 1
TIME_MEASURE = 1000  # milliseconds
LENGTH_MEASURE = 8 / 1000  # kilobit
ylabel(f'Throughput (Mbps)')  # kb/ms == Mbps


def fix(t_list, l_list):
    copy = list(t_list)
    index = 0
    step = 0
    counter = 0
    while index < len(copy):
        point = copy[index]
        if step == point:
            pass
        elif step < point:
            t_list.insert(index + counter, step)
            l_list.insert(index + counter, 0)
            counter += 1
            t_list.insert(index + counter, point - 1)
            l_list.insert(index + counter, 0)
            counter += 1
            step = point
        else:
            raise KeyError(f'Step {step} higher than point {point}')
        step = step + STEPPER
        index += 1

    for index in range(len(t_list)):
        t_list[index] /= TIME_MEASURE


def graphy(file_name, name, start=None, protocols=None):
    print(f'Running {name}...')
    step = STEPPER

    t_list = [0]
    l_list = [0]

    csv_file_name = f'journal/logs_1_1/pcap/{file_name}.csv'
    with open(csv_file_name) as csv_file:
        csv = reader(csv_file, delimiter=',')
        for row in islice(csv, 1, None):  # skip header
            r_time, r_source, r_destination, r_protocol, r_length, r_info = row
            if protocols:
                if r_protocol not in protocols:
                    continue
            r_time = Decimal(r_time)
            r_length = int(r_length) * LENGTH_MEASURE
            start = start if start else r_time
            now = (r_time - start) * Decimal(TIME_MEASURE)
            if now > step:
                while step < now:
                    step += STEPPER
                t_list.append(step)
                l_list.append(r_length)
            else:
                l_list[-1] += r_length

    t_list.append(t_list[-1] + STEPPER)
    l_list.append(0)

    print(f'Fixing {name}...')
    fix(t_list, l_list)

    print(f'Plotting {name}...')
    plot(
        t_list, l_list,  # linestyle='--', marker=None,
        label=name)
    print(t_list)
    print(l_list)
    print()

    return start


beginning = graphy('openflow', 'OpenFlow')
graphy('freeradius', 'RADIUS', beginning)
graphy('scada', 'MMS', beginning)
graphy('sdn-hostapd', 'EAPoL', beginning,
       ('EAPoL', 'EAP', 'TLSv1.2'))
graphy('sdn-hostapd', 'Rest API', beginning,
       ('TCP', 'HTTP'))

# plot(
#     rest_time, rest_bytes,  # linestyle='--', marker=None,
#     label='Rest API')
# plot(
#     scada_time, scada_bytes,  # linestyle='--', marker=None,
#     label='MMS')
# plot(
#     radius_time, radius_bytes,  # linestyle='--', marker=None,
#     label='RADIUS')

# annotate(
#     'IED2 é autorizado', xy=(11.05, .25), xytext=(9, .6),
#     bbox=dict(boxstyle="round4", fc="w", facecolor='gray'),
#     arrowprops=dict(facecolor='gray', arrowstyle='->'),
# )

legend()
savefig('3seq_of_events.png')
