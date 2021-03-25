import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt, rc
from os.path import join as p_join

rc('savefig', format='pdf')
rc('font', size=13)
rc('figure', figsize=[4, 3])
plt.subplots_adjust(top=0.98,
                    left=0.16, right=0.99,
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
        '_ws.col.Info': 'information',
        'eapol.type': 'eapol_type',
        'eth.src': 'eth_src',
    })

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


def debug(df):
    print(df.to_string())
    print()
    print(df)
    exit()


def helper(data_frame, query):
    row = data_frame.query(query).values[0]
    value = row[-1]
    address = row[0]
    new_data_frame = data_frame.query('source != @address or destination != @address')
    return value, address, new_data_frame


def mac_adder(value):  # INCORRECT!
    # MAC Address Adder
    rest, network, host = value.rsplit(':', 2)
    host = (int(host, 16) % 254) + 1
    network = int(network, 16) + int(host == 1)
    host = hex(host)[2:].zfill(2).lower()
    network = hex(network)[2:].zfill(2).lower()
    return rest + ':' + network + ':' + host


def parse_one(evs, rep, verbose=False):
    if verbose:
        print('loading datasets...')
    # radius = load_csv('freeradius', 'RADIUS', evs, rep)
    openflow = load_csv('openflow', 'OpenFlow', evs, rep)
    scada = load_csv('scada', 'MMS', evs, rep)
    hostapd = load_csv('sdn-hostapd', 'EAPoL', evs, rep)
    if verbose:
        print('loaded\n')
        print('concatenating datasets...')
    auth_tuple = (openflow, scada, hostapd)
    authentication = pd.concat(auth_tuple)
    if verbose:
        print('concatenated\n')
        print('setting index...')
    # authentication.set_index('datetime', inplace=True, verify_integrity=True)
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

    # this_rep = pd.DataFrame()
    current_ev = 0
    counter = 0
    current_mac = '00:00:00:00:00:03'
    aux = {}
    for _ in range(4, evs + 4):
        current_mac = mac_adder(current_mac)
        openflow_start = authentication.query(
            'Traffic == "OpenFlow" and eapol_type == 1 and information == "Type: OFPT_PACKET_IN" '
            f'and eth_src == "00:00:00:00:00:00,{current_mac}"')['time'].values[0]
        mms_start = authentication.query(
            'Traffic == "MMS" and length == 0.074 and protocol == "TCP" and '
            f'eth_src == "{current_mac}"')['time'].values[0]

        current_ev += 1
        counter += 1
        row = {'evs': evs, 'rep': rep, 'ev': current_ev,
               'start': openflow_start, 'end': mms_start,
               'delay': mms_start - openflow_start}
        aux[counter] = row
    this_rep = pd.DataFrame().from_dict(aux, 'index')
    # TODO media de todos veiculos no experimento + media por experimento?
    # TODO e se colocar a media separada por veiculo num grafico de pontos e tals
    this_rep.sort_values(by='start', inplace=True)
    this_rep.reset_index(drop=True, inplace=True)
    return this_rep


def parse_all():
    loaded_dataset = pd.DataFrame()
    # for ev in [1, 10, 300, 1000]:
    for ev in [1, 10, 25, 50, 100, 150]:
        for reps in range(1, 11):
            print(f'loading {ev}_{reps}...')
            q = parse_one(ev, reps, verbose=False)
            loaded_dataset = loaded_dataset.append(q, ignore_index=True)
    return loaded_dataset


def load():
    print('loading...')
    return pd.read_csv('all_experiments.csv')


# === CODE ===

sns.set_style('whitegrid')
ax = plt.gca()

# dataset = parse_all()
# dataset.to_csv('all_experiments_delay.csv')
# exit()
print('loading...')
dataset = pd.read_csv('all_experiments_delay.csv')
print('plotting...')
sns.set_palette('mako', 5)

query = 'evs != 25'
dataset.delay = dataset.delay * 1000
# sns.boxplot(x='evs', y='delay', data=dataset, width=.5)
sns.boxplot(x='evs', y='delay', data=dataset.query(query), width=.5)
# sns.jointplot(x=dataset.query(query).evs, kind='hex', y=dataset.query(query).delay)
plt.ylabel('Delay (ms)')
plt.xlabel('Number of EVs')
# plt.show()
plt.savefig('timeDelay')

exit()

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

# plt.savefig(f'timeDelay.pdf')
plt.show()
print('plotted')
