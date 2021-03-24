from mininet.topo import Topo
# from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
# from mininet.node import RemoteController
from time import sleep as _sleep
from MaxiNet.Frontend import maxinet
from mininet.node import OVSSwitch
from sys import argv

NUM_EV = int(argv[1])
EV_BY_SW = int(argv[2])
EXT_MACH = int(argv[3])
ROOT = '/home/arthurazs/git/3AS/'
EXPERIMENT = ROOT + 'experiment/'
AUTH_ROOT = EXPERIMENT + 'authenticator/'
IEDS_ROOT = EXPERIMENT + 'ieds/'

LOGS = ROOT + 'logs/'
AUTH_LOGS = LOGS + 'auth/'
PCAP_LOGS = LOGS + 'pcap/'
MMS_LOGS = LOGS + 'mms/'


def ceil(dividend, divisor):
    return -(-dividend / divisor)


def ip_adder(value):
    # IP Address Adder for netmask /16
    rest, network, host = value.rsplit('.', 2)
    host = (int(host) % 254) + 1
    network = int(network) + int(host == 1)
    return rest + '.' + str(network) + '.' + str(host)


def mac_adder(value):
    # MAC Address Adder
    rest, network, host = value.rsplit(':', 2)
    host = (int(host, 16) % 254) + 1
    network = int(network, 16) + int(host == 1)
    host = hex(host)[2:].zfill(2).upper()
    network = hex(network)[2:].zfill(2).upper()
    return rest + ':' + network + ':' + host


def hostapd(node):
    command = AUTH_ROOT + './sdn-hostapd'
    config = AUTH_ROOT + 'sdn-hostapd.conf -t'
    log = '> ' + AUTH_LOGS + 'sdn-hostapd.log 2>&1 &'
    node.cmdPrint(command, config, log)


def freeradius(node):
    command = 'freeradius -t -xx -l'
    log = AUTH_LOGS + 'freeradius.log'
    node.cmdPrint(command, log)


def wpa(node):
    command = 'wpa_supplicant -W -i ' + str(node.intfNames()[0]) + ' -D wired'
    config = '-c ' + IEDS_ROOT + 'evs/' + node.name + '.conf -dd -f'
    log = AUTH_LOGS + 'wpa-' + node.name + '.log &'
    node.cmdPrint(command, config, log)


def wpa_cli(node, script, name):
    command = 'wpa_cli -i ' + str(node.intfNames()[0])
    filename = '-a ' + IEDS_ROOT + script
    log = '> ' + MMS_LOGS + name + '.log 2>&1 &'
    node.cmdPrint(command, filename, log)


def pcap(node, name=None, intf=None, port=None):
    if not name:
        name = node.name
    if not intf:
        intf = node.intfNames()[0]
    command = 'tcpdump -i ' + str(intf) + ' -w'
    log = PCAP_LOGS + name + '.pcap'
    tail = 'port not ' + str(port) if port else ''
    node.cmd(command, log, tail, '&')


def sleep(time, msg):
    logger.info('*** {}: Sleeping for {} seconds...\n'.format(msg, time))
    _sleep(time)


mapping = {
    "s1": 0,
    "auth": 0,
    "scada": 0,
}

for index in range(2, ceil(NUM_EV, EV_BY_SW) + 2):
    mapping['s' + str(index)] = ((index - 2) % EXT_MACH) + 1

for index in range(1, NUM_EV + 1):
    mapping['ev' + str(index)] = (((index - 1) / EV_BY_SW) % EXT_MACH) + 1


class Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        auth = self.addHost(
            'auth', ip='10.0.1.2/16', mac='00:00:00:00:00:02')
        scada = self.addHost(
            'scada', ip='10.0.1.3/16', mac='00:00:00:00:00:03')

        ss = []
        s1 = self.addSwitch('s1')
        self.addLink(s1, auth, 1, 0)
        self.addLink(s1, scada, 2, 0)
        for index in range(2, ceil(NUM_EV, EV_BY_SW) + 2):
            switch = self.addSwitch('s' + str(index))
            self.addLink(s1, switch, index + 1, 1)
            ss.append(switch)

        ip = '10.0.1.3'
        mac = '00:00:00:00:00:03'
        for index in range(1, NUM_EV + 1):
            ip = ip_adder(ip)
            mac = mac_adder(mac)
            ev = self.addHost('ev' + str(index), ip=ip + '/16', mac=mac)
            switch = (index - 1) / EV_BY_SW
            port = ((index - 1) % EV_BY_SW) + 2
            self.addLink(ss[switch], ev, port, 0)


def main():

    # app.exe > ../logs/save_to.log 2>&1 &
    cluster = maxinet.Cluster()
    mn = maxinet.Experiment(
        cluster, Topology(), switch=OVSSwitch, nodemapping=mapping,
        controller='10.0.0.4')
    mn.setup()
    auth = mn.get('auth')
    s1 = mn.get('s1')
    scada = mn.get('scada')

    evs = []
    for h in mn.hosts:
        if 'ev' in h.name:
            evs.append(h)

    for sw in mn.switches:
        sw.cmd('rm -rf /var/run/wpa_supplicant')
        sw.cmd('rm -rf /home/arthurazs/git/3AS/logs/s*.log')
        sw.cmd('rm -rf /home/arthurazs/git/3AS/logs/auth')
        sw.cmd('rm -rf /home/arthurazs/git/3AS/logs/mms')
        sw.cmd('rm -rf /home/arthurazs/git/3AS/logs/pcap')

    logger.info("*** Disabling hosts ipv6\n")
    for h in mn.hosts:
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        if h.MAC() == scada.MAC():
            for ev in evs:
                h.setARP(ev.IP(), ev.MAC())
        else:
            h.setARP(scada.IP(), scada.MAC())

    logger.info("*** Disabling switches ipv6\n")
    for sw in mn.switches:
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    logger.info("*** Setting ARP tables\n")
    scada.setARP('10.0.1.1', '00:00:00:00:00:01')
    for ev in evs:
        ev.setARP('10.0.1.1', '00:00:00:00:00:01')

    logger.info("*** Creating log folders\n")
    for sw in mn.switches:
        sw.cmd('mkdir -p ' + PCAP_LOGS)
        sw.cmd('mkdir -p ' + AUTH_LOGS)
        sw.cmd('mkdir -p ' + MMS_LOGS)

    logger.info("*** Setting up traffic dumpers\n")
    pcap(s1, name='openflow', intf='lo', port='1812 and port not 53')
    pcap(auth, name='freeradius', intf='lo')
    pcap(auth, name='sdn-hostapd')
    pcap(scada)

    logger.info("*** Configuring bridge between 'auth' and 'controller'\n")
    s1.cmd('ifconfig s1 10.0.1.1 netmask 255.255.0.0')
    s1.cmd('ovs-vsctl set bridge s1 other-config:hwaddr=00:00:00:00:00:01')
    s1.setARP('10.0.1.2', '00:00:00:00:00:02')
    s1.setARP('10.0.1.3', '00:00:00:00:00:03')
    for ev in evs:
        s1.setARP(ev.IP(), ev.MAC())
    auth.setARP('10.0.1.1', '00:00:00:00:00:01')
    pcap(s1, name='controller', intf='s1', port='53')

    logger.info("*** Starting RADIUS (freeradius) \n")
    logger.info("*** Starting Authenticator (hostapd)\n")
    freeradius(auth)
    hostapd(auth)

    logger.info("*** Starting SCADA\n")
    scada.cmd(
        'screen -L -Logfile', MMS_LOGS + 'scada.log',
        '-S scada -dm python3 ' + IEDS_ROOT + 'scada.py')

    logger.info("*** Starting EVs\n")
    sleep(1, 'Starting EVs')
    for ev in evs:
        wpa(ev)
    
    sleep(1, 'Experiment')

    for ev in evs:
        wpa_cli(ev, 'ev.sh', ev.name)

    logger.info("*** Running experiment\n")
    sleep(5, 'Experiment')

    logger.info("*** Finishing experiment\n")
    for sw in mn.switches:
        sw.cmd('screen -S scada -X quit')
        sw.cmd("kill -2 $(ps aux | grep '[w]ired' | awk '{print $2}')")
        sw.cmd('pkill -2 hostapd')
        sw.cmd('pkill -2 freeradius')
        sw.cmd('pkill -2 server_ied')
        sw.cmd('ovs-ofctl dump-flows ' + sw.name +
               ' > ' + LOGS + sw.name + '.log')
        sw.cmd('chmod +r ' + AUTH_LOGS + 'freeradius.log')
        sw.cmd('pkill -2 tcpdump')

    sleep(5, 'Experiment')

    mn.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    main()
