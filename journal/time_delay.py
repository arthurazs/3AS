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


# def ip_adder(value):  # INCORRECT!
#     # IP Address Adder for netmask /16
#     rest, network, host = value.rsplit('.', 2)
#     host = (int(host) % 254) + 1
#     network = int(network) + int(host == 1)
#     return rest + '.' + str(network) + '.' + str(host)


def mac_adder(value):  # INCORRECT!
    # MAC Address Adder
    rest, network, host = value.rsplit(':', 2)
    host = (int(host, 16) % 254) + 1
    network = int(network, 16) + int(host == 1)
    host = hex(host)[2:].zfill(2).lower()
    network = hex(network)[2:].zfill(2).lower()
    return rest + ':' + network + ':' + host


# mac2ip = {}
# previous_mac = '00:00:00_00:00:03'
# previous_ip = '10.0.1.3'
# for _ in range(4, 1004):
#
#     # TODO we have to use the wrong func here bc our experiment is already done
#     # TODO                  f'00:00:00:00:{index // 256:02x}:{index % 256:02x}'
#     mac = mac_adder(previous_mac)  # TODO this mac_adder is incorrect, use above
#     ip = ip_adder(previous_ip)  # TODO same as above, ip_adder is incorrect
#     mac2ip[mac] = ip
#     previous_mac, previous_ip = mac, ip


def load(evs, rep, verbose=False):
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

    this_rep = pd.DataFrame()
    current_ev = 0
    current_mac = '00:00:00:00:00:03'
    for _ in range(4, evs + 4):
        current_mac = mac_adder(current_mac)
        # current_ip = mac2ip[current_mac]

        openflow_start = authentication.query(
            'Traffic == "OpenFlow" and eapol_type == 1 and information == "Type: OFPT_PACKET_IN" '
            f'and eth_src == "00:00:00:00:00:00,{current_mac}"')['time'].values[0]
        mms_start = authentication.query(
            'Traffic == "MMS" and length == 0.074 and protocol == "TCP" and '
            f'eth_src == "{current_mac}"')['time'].values[0]
        # eapol_start, _, authentication = helper(
        #     authentication, f'Traffic == "EAPoL" and source == "{current_mac}"')
        # mms_start, _, authentication = helper(
        #     authentication, f'Traffic == "MMS" and source == "{current_ip}"')

        aux = pd.DataFrame()
        current_ev += 1
        aux['evs'] = [evs]
        aux['rep'] = [rep]
        aux['ev'] = [current_ev]
        aux['start'] = [openflow_start]
        aux['end'] = [mms_start]
        aux['delay'] = [mms_start - openflow_start]
        this_rep = this_rep.append(aux, ignore_index=True)
        # TODO media de todos veiculos no experimento + media por experimento?
        # TODO e se colocar a media separada por veiculo num grafico de pontos e tals
    # return this_rep
    return this_rep.sort_values(by='start')


def load_all():
    loaded_dataset = pd.DataFrame()
    # for ev in [1, 10, 300, 1000]:
    for ev in [1000]:
        for reps in range(1, 11):
            print(f'loading {ev}_{reps}...')
            q = load(ev, reps, verbose=False)
            print(q)
            exit()
            # q.reset_index(inplace=True)
            q = q.loc['length']
            for name, length in q.items():
                aux = pd.DataFrame()
                aux['evs'] = [ev]
                aux['length'] = [length]
                aux['Traffic'] = [name]
                loaded_dataset = loaded_dataset.append(aux, ignore_index=True)
    return loaded_dataset


# === CODE ===

sns.set_style('whitegrid')
ax = plt.gca()

dataset = load_all()
print(dataset)    # 2.13
print('plotting...')
sns.set_palette('mako', 4)

# data_order = ['OpenFlow', 'API', 'EAPoL', 'RADIUS']
# sns.boxplot(x='Traffic', y='length',
sns.barplot(x='evs', y='length',
            data=dataset,
            errwidth=1, capsize=.1, edgecolor='.2',
            # order=data_order)
            )
plt.ylabel('Control Load (kBytes)')
plt.ylim(0, 9.5)
# plt.xlabel('Time (s)')

# ax.annotate('Authentication', xy=(2, 8.3), xytext=(2, 8.8),
#             ha='center', va='bottom',
#             arrowprops=dict(arrowstyle='-[, widthB=7.1, lengthB=0.5', color='black'))

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

plt.savefig(f'timeDelay.pdf')
# plt.show()
print('plotted')
