import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt, rc
from os.path import join as p_join

rc('savefig', format='pdf')
rc('font', size=13)
rc('figure', figsize=[4, 3])
plt.subplots_adjust(top=0.99,
                    left=0.11, right=0.99,
                    bottom=0.16)


# === FUNC ===

def epoch_parser(epoch):
    return pd.to_datetime(epoch, unit='s')


def load_csv(name, proto=None, evs=1, rep=1):
    if not proto:
        proto = name
    data_frame = pd.read_csv(p_join('dataset', f'logs_{evs}_{rep}', 'pcap', f'{name}.csv'),
                             parse_dates=[0], date_parser=epoch_parser)
    data_frame['Traffic'] = proto

    data_frame.rename(inplace=True, columns={
        'frame.time_epoch': 'datetime',
        '_ws.col.Source': 'source',
        '_ws.col.Destination': 'destination',
        '_ws.col.Protocol': 'protocol',
        '_ws.col.Length': 'length',
        '_ws.col.Info': 'information'})

    if name == 'sdn-hostapd':
        data_frame.loc[data_frame['protocol'] == 'TCP', 'Traffic'] = 'API'
        data_frame.loc[data_frame['protocol'] == 'HTTP', 'Traffic'] = 'API'

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


def load(evs, rep, verbose=False):
    if verbose:
        print('loading datasets...')
    radius = load_csv('freeradius', 'RADIUS', evs, rep)
    openflow = load_csv('openflow', 'OpenFlow', evs, rep)
    scada = load_csv('scada', 'MMS', evs, rep)
    hostapd = load_csv('sdn-hostapd', 'EAPoL', evs, rep)
    if verbose:
        print('loaded\n')
        print('concatenating datasets...')
    auth_tuple = (radius, openflow,  scada,
                  hostapd)
    authentication = pd.concat(auth_tuple)
    if verbose:
        print('concatenated\n')
        print('setting index...')
    authentication.set_index('datetime', inplace=True)
    authentication.sort_index(inplace=True)
    if verbose:
        print('setted\n')
        print('normalizing date...')
    authentication = normalize_time(authentication)
    if verbose:
        print('normalized\n')
        print('sampling down...')
        print(authentication.shape)
    helper_type = authentication[authentication.Traffic == 'EAPoL'].values[0][-1]
    aux = authentication.query('time < @helper_type')
    start = aux[aux.information == 'Type: OFPT_PACKET_IN'].values[-1][-1]
    end = authentication[authentication.Traffic == 'MMS'].values[0][-1]
    partial = normalize_time(
        authentication.query('time >= @start and time < @end').drop(columns='time'))
    if verbose:
        print(f'{start} -> {end}')
        print(partial.shape)
        print('sampled\n')
    # media por veiculo
    partial.length = partial.length / evs

    return partial.groupby('Traffic').sum().T


def load_all():
    loaded_dataset = pd.DataFrame()
    for ev in [1, 10, 50, 100, 150]:
        for reps in range(1, 11):
            print(f'loading {ev}_{reps}...')
            loaded = load(ev, reps, verbose=False)
            loaded = loaded.loc['length']
            for name, length in loaded.items():
                aux = pd.DataFrame()
                aux['length'] = [length]
                aux['Traffic'] = [name]
                loaded_dataset = loaded_dataset.append(aux, ignore_index=True)
    return loaded_dataset


# === CODE ===

sns.set_style('whitegrid')
ax = plt.gca()

print('loading...\n')
try:
    dataset = pd.read_csv('all_experiments_load.csv')
except FileNotFoundError:
    dataset = load_all()
    dataset.to_csv('all_experiments_load.csv')

print('Openflow', dataset.query('Traffic == "OpenFlow"').mean())     # 0.96
print('API', dataset.query('Traffic == "API"').mean())               # 0.46
print('EAPoL', dataset.query('Traffic == "EAPoL"').mean())           # 3.32
print('RADIUS', dataset.query('Traffic == "RADIUS"').mean())         # 4.38

print('\nplotting...')
sns.set_palette('mako', 4)

data_order = ['OpenFlow', 'API', 'EAPoL', 'RADIUS']
sns.barplot(x='Traffic', y='length',
            data=dataset,
            errwidth=1, capsize=.1, edgecolor='.2',
            order=data_order)
plt.ylabel('Control Load (kBytes)')

ax.annotate('Authentication', xy=(2, 4.6), xytext=(2, 4.95),
            ha='center', va='bottom',
            arrowprops=dict(arrowstyle='-[, widthB=7.1, lengthB=0.5', color='black'))

plt.savefig(f'controlLoad.pdf')
print('plotted')
