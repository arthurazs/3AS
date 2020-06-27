import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt, rc
from os.path import join as p_join

EVS = 1
REP = 3
LOGS = f'logs_{EVS}_{REP}'
FOLDER = p_join('dataset', LOGS, 'pcap')
rc('savefig', format='pdf')


def epoch_parser(epoch):
    return pd.to_datetime(epoch, unit='s')


def load_csv(name, proto=None):
    if not proto:
        proto = name
    dataframe = pd.read_csv(p_join(FOLDER, f'{name}.csv'),
                            parse_dates=[0], date_parser=epoch_parser)
    dataframe['csv'] = proto

    dataframe.rename(inplace=True, columns={
        'frame.time_epoch': 'datetime',
        '_ws.col.Source': 'source',
        '_ws.col.Destination': 'destination',
        '_ws.col.Protocol': 'protocol',
        '_ws.col.Length': 'length',
        '_ws.col.Info': 'information'})

    return dataframe


def normalize_date(current_time, starting_time):
    return (current_time.name - starting_time).total_seconds()


print('loading datasets...')
radius = load_csv('freeradius', 'radius')
openflow = load_csv('openflow')
scada = load_csv('scada')
hostapd = load_csv('sdn-hostapd', 'hostapd')
print('loaded\n')

print('concatenating datasets...')
auth_tuple = (
    radius,
    openflow,
    scada,
    hostapd,
)
authentication = pd.concat(auth_tuple)
print('concatenated\n')

print('setting index...')
authentication.set_index('datetime', inplace=True, verify_integrity=True)
authentication.sort_index(inplace=True)
print('setted\n')

print('resampling data...')
authentication = authentication.groupby(
    ['csv', 'protocol']).resample('100us').sum()
authentication.reset_index(['csv', 'protocol'], inplace=True)
authentication.sort_index(inplace=True)
time_of_first_occurrence = authentication.index.min()
print('resampled\n')

print('normalizing date...')
authentication['time'] = authentication.apply(
    normalize_date, axis=1,
    args=[time_of_first_occurrence])
print('normalized\n')

print('adding missing data...')
authentication['prev_length'] = authentication.length.shift(1)
authentication['next_length'] = authentication.length.shift(-1)
print('WARNING this is not working properly')  # TODO Fix
# maybe add protocol for prev/next
authentication = authentication.query(
    'length != 0 or '
    '(next_length != 0 or prev_length != 0)')
print('added\n')

# print('normalizing date again...')
# partial_auth = authentication.query('time > 2').drop('time', axis=1)
# partial_auth['time'] = partial_auth.index
# starting_time = partial_auth.index.min()
# partial_auth.time = partial_auth.time.apply(lambda x: x - starting_time)
# partial_auth.time = partial_auth.time.abs().dt.total_seconds()
# print(partial_auth)
# print('normalized\n')

print('plotting...')
# TODO
# Validar suavização com pandas utilizando media dos protocolos
sns.set_style('whitegrid')
# https://seaborn.pydata.org/tutorial/color_palettes.html
# sns.set_palette('Blues', 3)
protocol_list = [
    'COTP',
    'EAP',
    # 'EAPOL',
    'HTTP',
    'MMS',
    'OpenFlow',
    # 'RADIUS',
    'TCP',
    'TLSv1',
    'TLSv1.2',
]
csv_list = [
    'hostapd',
    'openflow',
    # 'radius',
    'scada',
]
sns.lineplot(
    x='time', y='length',
    hue='protocol', style='csv',
    hue_order=protocol_list, style_order=csv_list,
    # hue='csv',
    # hue_order=csv_list,
    # data=partial_auth.query('time < .5'))
    data=authentication.query('time >= 2 and time <= 2.5'))

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

plt.show()
# plt.savefig('test.pdf')
print('plotted')
