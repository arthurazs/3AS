import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt, rc
from os.path import join as p_join

EVS = 1
REP = 5
LOGS = f'logs_{EVS}_{REP}'
FOLDER = p_join('dataset', LOGS, 'pcap')
rc('savefig', format='pdf')
rc('figure', figsize=[10, 3])
plt.subplots_adjust(top=0.95,
                    left=0.07, right=0.98,
                    bottom=0.2)


# === FUNC ===

def epoch_parser(epoch):
    return pd.to_datetime(epoch, unit='s')


def load_csv(name, proto=None):
    if not proto:
        proto = name
    data_frame = pd.read_csv(p_join(FOLDER, f'{name}.csv'), parse_dates=[0],
                             date_parser=epoch_parser)
    data_frame['Process'] = proto

    data_frame.rename(inplace=True, columns={
        'frame.time_epoch': 'datetime',
        '_ws.col.Source': 'source',
        '_ws.col.Destination': 'destination',
        '_ws.col.Protocol': 'protocol',
        '_ws.col.Length': 'length',
        '_ws.col.Info': 'information'})

    # data_frame.length = data_frame.length.apply(lambda x: x / 1000)
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


# === CODE ===

print('loading datasets...')
radius = load_csv('freeradius', 'Authentication')
openflow = load_csv('openflow', 'SDN')
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
    authentication.query('time > 1 and time < 2.3').drop(columns='time'))
# partial = authentication.query('time >= 2 and time <= 2.2')
print(partial.shape)
print('sampled\n')

print('plotting...')
# TODO
# Validar suavização com pandas utilizando media dos protocolos
sns.set_style('whitegrid')
# https://seaborn.pydata.org/tutorial/color_palettes.html

protocol_list = partial.protocol.unique()
protocol_list = protocol_list[
    (protocol_list != 'EAPOL') & (protocol_list != 'RADIUS')]

csv_list = partial.Process.unique()
csv_list = csv_list[csv_list != 'radius']

# sns.set_palette('Blues', len(protocol_list))
sns.set_palette('mako', len(csv_list))


sns.lineplot(
    x='time', y='length',
    # hue='protocol', style='Process',
    # hue_order=protocol_list, style_order=csv_list,

    style='Process',
    style_order=csv_list,

    hue='Process',
    hue_order=csv_list,
    data=partial)

plt.ylabel('Throughput (kBytes/s)')
plt.xlabel('Time (s)')

# todo
# tamanho boxplot
# - fazer boxplot pro tamanho dos pacotes
# tempo amostra (regplot?)
# - colocar só os pontos (amostras, sem as retas)
# - 'fiz essa sequência de eventos várias vezes e a dispersão fica assim'
# - pintar os pontos pra simbolizar partes do evento
# - 'inicio de X, fim de X'
# tempo boxplot?
# - olhar quanto tempo leva cada evento
# - sabe-se a sequência de eventos (tempo total)

# plt.show()
plt.savefig('seqOfEvents.pdf')
# print('plotted')
