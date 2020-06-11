import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from os.path import join as p_join

evs = 1
rep = 3
logs = f'logs_{evs}_{rep}'
folder = p_join(logs, 'pcap')

radius = pd.read_csv(p_join(folder, 'freeradius.csv'))
radius['csv'] = 'radius'

openflow = pd.read_csv(p_join(folder, 'openflow.csv'))
openflow['csv'] = 'openflow'

scada = pd.read_csv(p_join(folder, 'scada.csv'))
scada['csv'] = 'scada'

hostapd = pd.read_csv(p_join(folder, 'sdn-hostapd.csv'))
hostapd['csv'] = 'hostpad'

for csv in (radius, openflow, scada, hostapd):
    csv.rename(inplace=True, columns={
        'frame.time_epoch': 'datetime',
        '_ws.col.Source': 'source',
        '_ws.col.Destination': 'destination',
        '_ws.col.Protocol': 'protocol',
        '_ws.col.Length': 'length',
        '_ws.col.Info': 'information'})
    csv.datetime = pd.to_datetime(
        csv.datetime, unit='s', origin='unix')

auth_tuple = (
    # radius,
    openflow,
    scada,
    hostapd,
)
authentication = pd.concat(auth_tuple)

authentication.set_index('datetime', inplace=True, verify_integrity=True)
authentication.sort_index(inplace=True)
authentication['time'] = authentication.index

authentication = authentication.groupby(
    ['csv', 'protocol']).resample('100us').sum()
authentication.reset_index(['csv', 'protocol'], inplace=True)
authentication['time'] = authentication.index

starting_time = authentication.time.min()
authentication.time = authentication.time.apply(lambda x: x - starting_time)

authentication.time = authentication.time.abs().dt.total_seconds()

authentication['prev_length'] = authentication.length.shift(1)
authentication['next_length'] = authentication.length.shift(-1)
authentication = authentication.query(
    'length != 0 or '
    '(next_length != 0 or prev_length != 0)')

authentication.sort_index(inplace=True)
print(authentication)

partial_auth = authentication.query('time > 2').drop('time', axis=1)
partial_auth['time'] = partial_auth.index
starting_time = partial_auth.index.min()
partial_auth.time = partial_auth.time.apply(lambda x: x - starting_time)
partial_auth.time = partial_auth.time.abs().dt.total_seconds()
print(partial_auth)

# TODO Validar suavização com pandas
# TODO utilizando media dos protocolos
sns.lineplot(x='time', y='length',
             hue='csv',
             data=partial_auth.query('time < .5'))

# TODO Plotar boxplot separado por protocolo

plt.show()
