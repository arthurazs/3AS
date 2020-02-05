from mininet.topo import Topo
# from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
# from mininet.node import RemoteController
from time import sleep as _sleep
from MaxiNet.Frontend import maxinet
from mininet.node import OVSSwitch
# from mininet.cli import CLI

NUM_EV = 20
ROOT = '/home/arthurazs/git/3AS/'
EXPERIMENT = ROOT + 'experiment/'
AUTH_ROOT = EXPERIMENT + 'authenticator/'
IEDS_ROOT = EXPERIMENT + 'ieds/'

LOGS = ROOT + 'logs/'
AUTH_LOGS = LOGS + 'auth/'
PCAP_LOGS = LOGS + 'pcap/'
MMS_LOGS = LOGS + 'mms/'


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
    command = 'wpa_supplicant -i ' + str(node.intfNames()[0]) + ' -D wired'
    # command = 'wpa_supplicant -i ' + str(node.intf()) + ' -D wired'
    config = '-c ' + IEDS_ROOT + 'evs/' + node.name + '.conf -dd -f'
    # config = '-c ' + IEDS_ROOT + str(node) + '.conf -dd -f'
    # log = AUTH_LOGS + 'wpa-' + str(node) + '.log &'
    log = AUTH_LOGS + 'wpa-' + node.name + '.log &'
    node.cmdPrint(command, config, log)


def wpa_cli(node, script, name):
    command = 'wpa_cli -i ' + str(node.intfNames()[0])
    # command = 'wpa_cli -i ' + str(node.intf())
    filename = '-a ' + IEDS_ROOT + script
    log = '> ' + MMS_LOGS + name + '.log 2>&1 &'
    node.cmdPrint(command, filename, log)


def pcap(node, name=None, intf=None, port=None):
    if not name:
        # name = str(node)
        name = node.name
    if not intf:
        # intf = node.intf()
        intf = node.intfNames()[0]
    command = 'tcpdump -i ' + str(intf) + ' -w'
    log = PCAP_LOGS + name + '.pcap'
    tail = 'port not ' + str(port) if port else ''
    node.cmd(command, log, tail, '&')


def sleep(time):
    logger.info('*** Sleeping for {} seconds...\n'.format(time))
    _sleep(time)


MAPPING = {
    "s1": 0,
    "auth": 0,
    "scada": 0,

    "s2": 1,
    "ev1": 1, "ev2": 1, "ev3": 1, "ev4": 1, "ev5": 1,
    "ev6": 1, "ev7": 1, "ev8": 1, "ev9": 1, "ev10": 1,
    "ev11": 1, "ev12": 1, "ev13": 1, "ev14": 1, "ev15": 1,
    "ev16": 1, "ev17": 1, "ev18": 1, "ev19": 1, "ev20": 1,
}


class Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        auth = self.addHost(
            'auth', ip='10.0.1.2/24', mac='00:00:00:00:00:02')
        scada = self.addHost(
            'scada', ip='10.0.1.3/24', mac='00:00:00:00:00:03')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(s1, s2, 1, 1)
        self.addLink(s1, auth, 2, 0)
        self.addLink(s1, scada, 3, 0)

        for index in range(1, NUM_EV + 1):
            ev = self.addHost(
                'ev' + str(index),
                ip='10.0.1.' + str(index + 3) + '/24',
                mac='00:00:00:00:00:' + str(index + 3).zfill(2))
            self.addLink(s2, ev, index + 1, 0)


def main():

    # app.exe > ../logs/save_to.log 2>&1 &
    cluster = maxinet.Cluster()
    mn = maxinet.Experiment(
        cluster, Topology(), switch=OVSSwitch, nodemapping=MAPPING,
        controller='10.0.0.4')
    mn.setup()
    auth = mn.get('auth')
    s1 = mn.get('s1')
    scada = mn.get('scada')

    evs = []
    for h in mn.hosts:
        if 'ev' in h.name:
            evs.append(h)
    ev1 = mn.get('ev1')
    ev10 = mn.get('ev10')
    ev20 = mn.get('ev20')

    for sw in mn.switches:
        sw.cmd('rm -rf /var/run/wpa_supplicant')

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
    pcap(ev1)
    pcap(ev10)
    pcap(ev20)

    # mn.start()

    logger.info("*** Configuring bridge between 'auth' and 'controller'\n")
    s1.cmd('ifconfig s1 10.0.1.1 netmask 255.255.255.0')
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
    for ev in evs:
        wpa(ev)
        sleep(.1)
        wpa_cli(ev, 'ev.sh', ev.name)

    # CLI(mn)
    # mn.stop()
    # exit(0)

    logger.info("*** Running experiment\n")
    sleep(3)

    logger.info("*** Finishing experiment\n")
    for sw in mn.switches:
        sw.cmd('screen -S scada -X quit')
        sw.cmd('pkill -2 wpa_supplicant')
        sleep(2)
        sw.cmd('pkill -2 hostapd')
        sleep(2)
        sw.cmd('pkill -2 freeradius')
        sw.cmd('pkill -2 server_ied')
        sw.cmd('ovs-ofctl dump-flows ' + sw.name +
               ' > ' + LOGS + sw.name + '.log')
        sw.cmd('chmod +r ' + AUTH_LOGS + 'freeradius.log')
        sw.cmd('pkill -2 tcpdump')

    mn.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    main()
