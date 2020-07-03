import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt, rc
from os.path import join as p_join

EVS = 1
REP = 3
LOGS = f'logs_{EVS}_{REP}'
FOLDER = p_join('dataset', LOGS, 'pcap')
rc('savefig', format='pdf')


# === FUNC ===

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


def fix_sample(dataframe, interval, unit):
    dataset = dataframe.copy(deep=True)

    new_data = pd.DataFrame()

    for _, row in dataset.iterrows():
        if row.length > 0:
            row.length = 0

            before = row.name - pd.to_timedelta(interval, unit=unit)
            row_before = pd.DataFrame([row], index=[before])

            after = row.name + pd.to_timedelta(interval, unit=unit)
            row_after = pd.DataFrame([row], index=[after])

            new_data = pd.concat([new_data, row_before, row_after])

    dataset = pd.concat([dataset, new_data], verify_integrity=True)

    return dataset


def normalize_time(dataframe):
    def _normalize(current_time, starting_time):
        return (current_time.name - starting_time).total_seconds()

    dataset = dataframe.copy(deep=True)
    first_occurrence = dataset.index.min()

    dataset['time'] = dataset.apply(
        _normalize, axis=1,
        args=[first_occurrence])
    return dataset


# === CODE ===

print('loading datasets...')
radius = load_csv('freeradius', 'radius')
openflow = load_csv('openflow')
scada = load_csv('scada')
hostapd = load_csv('sdn-hostapd', 'hostapd')
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
partial = normalize_time(
    authentication.query('time > 1 and time < 4').drop(columns='time'))
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

csv_list = partial.csv.unique()
csv_list = csv_list[csv_list != 'radius']

# sns.set_palette('Blues', len(protocol_list))
sns.set_palette('Blues', len(csv_list))

sns.lineplot(
    x='time', y='length',
    # hue='protocol', style='csv',
    # hue_order=protocol_list, style_order=csv_list,
    hue='csv',
    hue_order=csv_list,
    data=partial)

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
