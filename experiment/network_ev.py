from mininet.topo import Topo
# from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
# from mininet.node import RemoteController
from time import sleep as _sleep
from MaxiNet.Frontend import maxinet
from mininet.node import OVSSwitch
# from mininet.cli import CLI


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
    config = '-c ' + IEDS_ROOT + node.name + '.conf -dd -f'
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
    "auth": 0,
    "scada": 0,
    "ev1": 1,
    "ev2": 1,
    "ev3": 1,
    "ev4": 1,
    "ev5": 1,
    "s1": 0,
    "s2": 1
}


class Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        auth = self.addHost(
            'auth', ip='10.0.1.2/24', mac='00:00:00:00:00:02')
        scada = self.addHost(
            'scada', ip='10.0.1.3/24', mac='00:00:00:00:00:03')

        ev1 = self.addHost(
            'ev1', ip='10.0.1.4/24', mac='00:00:00:00:00:04')
        ev2 = self.addHost(
            'ev2', ip='10.0.1.5/24', mac='00:00:00:00:00:05')
        ev3 = self.addHost(
            'ev3', ip='10.0.1.6/24', mac='00:00:00:00:00:06')
        ev4 = self.addHost(
            'ev4', ip='10.0.1.7/24', mac='00:00:00:00:00:07')
        ev5 = self.addHost(
            'ev5', ip='10.0.1.8/24', mac='00:00:00:00:00:08')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(s1, s2, 1, 1)
        self.addLink(s1, auth, 2, 0)
        self.addLink(s1, scada, 3, 0)

        self.addLink(s2, ev1, 2, 0)
        self.addLink(s2, ev2, 3, 0)
        self.addLink(s2, ev3, 4, 0)
        self.addLink(s2, ev4, 5, 0)
        self.addLink(s2, ev5, 6, 0)


def main():

    cluster = maxinet.Cluster()
    mn = maxinet.Experiment(
        cluster, Topology(), switch=OVSSwitch, nodemapping=MAPPING,
        # controller=RemoteController('c0', ip='10.0.0.4', port=6653))
        controller='10.0.0.4')
    # app.exe > ../logs/save_to.log 2>&1 &
    # mn = Mininet(  # TODO Test without static ARP
    #     topo=Topology(), autoStaticArp=True,
    #     controller=RemoteController('c0', ip='127.0.0.1', port=6653))
    # auth, s1, s2 = mn.get('auth', 's1', 's2')
    mn.setup()
    auth = mn.get('auth')
    s1 = mn.get('s1')
    scada = mn.get('scada')
    ev1 = mn.get('ev1')
    ev2 = mn.get('ev2')
    ev3 = mn.get('ev3')
    ev4 = mn.get('ev4')
    ev5 = mn.get('ev5')
    evs = [ev1, ev2, ev3, ev4, ev5]
    # scada, ev1, ev2, ev3, ev4, ev5 = mn.get(
    #     'scada', 'ev1', 'ev2', 'ev3', 'ev4', 'ev5')

    for sw in mn.switches:
        sw.cmd('rm -rf /var/run/wpa_supplicant')

    logger.info("*** Disabling hosts ipv6\n")
    for h in mn.hosts:
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
        if h.MAC() == scada.MAC():
            h.setARP('10.0.1.4', '00:00:00:00:00:04')
            h.setARP('10.0.1.5', '00:00:00:00:00:05')
            h.setARP('10.0.1.6', '00:00:00:00:00:06')
            h.setARP('10.0.1.7', '00:00:00:00:00:07')
            h.setARP('10.0.1.8', '00:00:00:00:00:08')
        else:
            h.setARP(scada.IP(), scada.MAC())

    logger.info("*** Disabling switches ipv6\n")
    for sw in mn.switches:
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    logger.info("*** Setting ARP tables\n")
    scada.setARP('10.0.1.1', '00:00:00:00:00:01')
    ev1.setARP('10.0.1.1', '00:00:00:00:00:01')
    ev2.setARP('10.0.1.1', '00:00:00:00:00:01')
    ev3.setARP('10.0.1.1', '00:00:00:00:00:01')
    ev4.setARP('10.0.1.1', '00:00:00:00:00:01')
    ev5.setARP('10.0.1.1', '00:00:00:00:00:01')

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
    pcap(ev5)

    # mn.start()

    logger.info("*** Configuring bridge between 'auth' and 'controller'\n")
    s1.cmd('ifconfig s1 10.0.1.1 netmask 255.255.255.0')
    s1.cmd('ovs-vsctl set bridge s1 other-config:hwaddr=00:00:00:00:00:01')
    s1.setARP('10.0.1.2', '00:00:00:00:00:02')
    s1.setARP('10.0.1.3', '00:00:00:00:00:03')
    s1.setARP('10.0.1.4', '00:00:00:00:00:04')
    s1.setARP('10.0.1.5', '00:00:00:00:00:04')
    s1.setARP('10.0.1.6', '00:00:00:00:00:04')
    s1.setARP('10.0.1.7', '00:00:00:00:00:04')
    s1.setARP('10.0.1.8', '00:00:00:00:00:04')
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
    sleep(15)

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
