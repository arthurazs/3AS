import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt, rc
from os.path import join as p_join

EVS = 1
REP = 8
LOGS = f'logs_{EVS}_{REP}'
FOLDER = p_join('dataset', LOGS, 'pcap')
rc('savefig', format='pdf')
rc('figure', figsize=[10, 2.6])
plt.subplots_adjust(top=.98,
                    left=0.06, right=0.995,
                    bottom=0.165)


# === FUNC ===

def epoch_parser(epoch):
    return pd.to_datetime(epoch, unit='s')


def load_csv(name, proto=None):
    if not proto:
        proto = name
    data_frame = pd.read_csv(p_join(FOLDER, f'{name}.csv'), parse_dates=[0],
                             date_parser=epoch_parser)

    data_frame['Traffic'] = proto

    data_frame.rename(inplace=True, columns={
        'frame.time_epoch': 'datetime',
        '_ws.col.Source': 'source',
        '_ws.col.Destination': 'destination',
        '_ws.col.Protocol': 'protocol',
        '_ws.col.Length': 'length',
        '_ws.col.Info': 'information'})

    data_frame.length = data_frame.length.apply(lambda x: x / 1000)

    return data_frame


def fix_sample(data_frame, interval, unit):
    data_set = data_frame.copy(deep=True)

    new_data = pd.DataFrame()

    for _, row in data_set.iterrows():
        if row.length > 0:
            row.length = 0

            before = row.name - pd.to_timedelta(interval, unit=unit)
            row_before = pd.DataFrame([row], index=[before])

            after = row.name + pd.to_timedelta(interval, unit=unit)
            row_after = pd.DataFrame([row], index=[after])

            new_data = pd.concat([new_data, row_before, row_after])

    data_set = pd.concat([data_set, new_data], verify_integrity=True)

    return data_set


def normalize_time(data_frame):
    def _normalize(current_time, starting_time):
        return (current_time.name - starting_time).total_seconds()

    data_set = data_frame.copy(deep=True)
    first_occurrence = data_set.index.min()

    data_set['time'] = data_set.apply(
        _normalize, axis=1,
        args=[first_occurrence])
    return data_set


def load_all():
    print('loading datasets...')
    radius = load_csv('freeradius', 'Authentication')
    openflow = load_csv('openflow', 'OpenFlow')
    scada = load_csv('scada', 'MMS')
    hostapd = load_csv('sdn-hostapd', 'Authentication')
    print('loaded\n')

    print('concatenating datasets...')
    auth_tuple = (radius, openflow, scada, hostapd)
    authentication = pd.concat(auth_tuple)
    print('concatenated\n')

    print('setting index...')
    authentication.set_index('datetime', inplace=True, verify_integrity=True)
    authentication.sort_index(inplace=True)
    print('setted\n')

    print('resampling data...')
    print(authentication.shape)
    authentication = fix_sample(authentication, 1, 'ms')
    authentication.sort_index(inplace=True)
    print(authentication.shape)
    print('resampled\n')

    print('normalizing date...')
    authentication = normalize_time(authentication)
    print('normalized\n')

    print('sampling down...')
    print(authentication.shape)
    partial = authentication
    partial = normalize_time(
        authentication.query('time > 3 and time < 3.3').drop(columns='time'))
    print(partial.shape)
    print('sampled\n')
    return partial


# === CODE ===

try:
    dataset = pd.read_csv('all_experiments_seq.csv')
except FileNotFoundError:
    dataset = load_all()
    dataset.to_csv('all_experiments_seq.csv')

print('plotting...')
sns.set_style('whitegrid')

protocol_list = dataset.protocol.unique()
protocol_list = protocol_list[
    (protocol_list != 'EAPOL') & (protocol_list != 'RADIUS')]

csv_list = dataset.Traffic.unique()

sns.set_palette('mako', len(csv_list))

sns.lineplot(
    x='time', y='length',
    style='Traffic',
    style_order=csv_list,
    hue='Traffic',
    hue_order=csv_list,
    data=dataset)

plt.ylabel('Throughput (kBytes/s)')
plt.xlabel('Time (s)')
plt.yticks(np.arange(0, 1.75, .25))
plt.xticks(np.arange(0, .131, .01))

ax = plt.gca()

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles=handles, labels=labels, title="Traffic", title_fontsize='large')
ax.get_legend()._legend_box.align = "left"

box_style = {'boxstyle': 'round', 'fc': 'w', 'color': 'grey'}
arrow_style = {'arrowstyle': '->', 'color': 'black'}

ax.annotate('Authentication starts', xy=(0, .05), xytext=(-.003, .35), bbox=box_style,
            arrowprops=dict(**arrow_style, connectionstyle="arc3,rad=.3"))
ax.annotate('EV authenticated', xy=(.035, .250), xytext=(.037, .6), bbox=box_style,
            arrowprops=dict(**arrow_style, connectionstyle="arc3,rad=.3"))
ax.annotate('3AS informs ARES', xy=(.0375, .250), xytext=(.042, .4), bbox=box_style,
            arrowprops=dict(**arrow_style, connectionstyle="arc3,rad=-.3"))
ax.annotate('EV opens connection', xy=(.123, 0), xytext=(.102, .4), bbox=box_style,
            arrowprops=dict(**arrow_style, connectionstyle="arc3,rad=-.3"))

plt.savefig(f'seqOfEvents_{EVS}_{REP}.pdf')
