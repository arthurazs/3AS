from matplotlib.pyplot import bar, savefig, ylabel, subplots_adjust
from matplotlib import rc, rcParams
from csv import reader
from itertools import islice
from numpy import array as np_array, mean as np_mean
from scipy.stats import sem, t


def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np_array(data)
    n = len(a)
    mean, se = np_mean(a), sem(a)
    error = se * t.ppf((1 + confidence) / 2., n-1)
    return mean, error


# rcParams['font.family'] = 'Times New Roman'
rcParams['font.size'] = '18'
rcParams['figure.figsize'] = [7, 5]
subplots_adjust(left=.13, bottom=.06, right=.99, top=.99)
rcParams['errorbar.capsize'] = 7
rc('savefig', dpi=300, format='png')
ylabel('Milissegundos')
width = .5
blue = (0.2588, 0.4433, 1.0)
# tshark -r pcap/ied1.pcap -T fields -e frame.time_epoch -e frame.len \
# -e _ws.col.Protocol -E header=y -E separator=, -E quote=d > ied1.csv

ied1 = []
for index in range(1, 6):
    ied1_start, ied1_finish = None, 0
    with open(f'experiment2/logs{index}/ied1.csv') as csv_file:
        ied1_data = reader(csv_file, delimiter=',')

        for row in islice(ied1_data, 1, None):  # skip header
            if row[2] in ('EAPOL', 'EAP', 'TLSv1', 'TLSv1.2'):
                if not ied1_start:
                    ied1_start = float(row[0])
                else:
                    ied1_finish = float(row[0]) - ied1_start
    ied1.append(ied1_finish * 1000)

ied2 = []
for index in range(1, 6):
    ied2_start, ied2_finish = None, 0
    with open(f'experiment2/logs{index}/ied2.csv') as csv_file:
        ied2_data = reader(csv_file, delimiter=',')

        for row in islice(ied2_data, 1, None):  # skip header
            if row[2] in ('EAPOL', 'EAP', 'TLSv1', 'TLSv1.2'):
                if not ied2_start:
                    ied2_start = float(row[0])
                else:
                    ied2_finish = float(row[0]) - ied2_start
    ied2.append(ied2_finish * 1000)

ied1_mean, ied1_error = mean_confidence_interval(ied1)
ied2_mean, ied2_error = mean_confidence_interval(ied2)

bar('Certificados', ied1_mean, width, color=blue,
    edgecolor='black', yerr=ied1_error)
bar('Credenciais', ied2_mean, width, color=blue,
    edgecolor='black', yerr=ied2_error)

savefig('experiment2/certs_vs_creds_delay.png')

print(ied1_mean, ied2_mean)
