from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
from mininet.node import RemoteController
from mininet.link import Intf
from time import sleep as _sleep
from sys import argv

ROOT = 'experiment/'
AUTH_ROOT = ROOT + 'authenticator/'
IEDS_ROOT = ROOT + 'ieds/'

LOGS = 'logs/'
AUTH_LOGS = LOGS + 'auth/'
PCAP_LOGS = LOGS + 'pcap/'


def hostapd(node):
    command = AUTH_ROOT + './sdn-hostapd '
    config = AUTH_ROOT + 'sdn-hostapd.conf -t '
    log = ' > ' + AUTH_LOGS + 'sdn-hostapd.log 2>&1 &'
    node.cmdPrint(command + config + log)


def freeradius(node):
    command = 'freeradius -t -xx -l '
    log = AUTH_LOGS + 'freeradius.log'
    node.cmdPrint(command + log)


def wpa(node):
    # wpa_supplicant -i INTF -D wired
    # -c config/NAME.conf -dd
    # -f logs/wpa-NAME.log &
    command = 'wpa_supplicant -i ' + str(node.intf()) + ' -D wired '
    config = '-c ' + IEDS_ROOT + str(node) + '.conf -dd -f '
    log = AUTH_LOGS + 'wpa-' + str(node) + '.log &'
    node.cmdPrint(command + config + log)


def wpa_cli(node, script):
    # wpa_cli -i INTF -a experiment/ieds/scada_ping.sh
    command = 'wpa_cli -i ' + str(node.intf())
    filename = ' -a ' + IEDS_ROOT + script
    log = ' > ' + AUTH_LOGS + 'ping.log 2>&1 &'
    node.cmdPrint(command + filename + log)


def pcap(node, name=None, intf=None, port=None):
    # tcpdump -i intf -w logs/name.pcap port not number &
    if not name:
        name = str(node)
    if not intf:
        intf = node.intf()
    command = 'tcpdump -i ' + str(intf) + ' -w '
    log = PCAP_LOGS + name + '.pcap'
    tail = ' port not ' + str(port) if port else ''
    node.cmdPrint(command + log + tail + ' &')


def log_sleep(time):
    logger.info('*** Sleeping for {} seconds...\n'.format(time))
    _sleep(time)


class Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        auth = self.addHost('auth', ip='10.0.0.2', mac='00:00:00:00:00:02')
        scada = self.addHost('scada', ip='10.0.0.3', mac='00:00:00:00:00:03')
        ev = self.addHost('ev', ip='10.0.0.4', mac='00:00:00:00:00:04')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(s1, s2, 1, 1)
        self.addLink(s1, auth, 3, 0)
        self.addLink(s1, scada, 4, 0)
        self.addLink(s2, ev, 2, 0)


def main(mac_address, interface):
    # app.exe > ../logs/save_to.log 2>&1 &
    mn = Mininet(  # TODO Test without static ARP
        topo=Topology(), autoStaticArp=True,
        controller=RemoteController('c0', ip='10.0.0.1', port=6653))
    auth, scada, ev, s1, s2 = mn.get('auth', 'scada', 'ev', 's1', 's2')

    Intf(interface, node=s1, port=2)
    s1.cmd('rm -rf /var/run/wpa_supplicant')

    logger.info("*** Disabling hosts ipv6\n")
    for h in mn.hosts:
        h.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    logger.info("*** Disabling switches ipv6\n")
    for sw in mn.switches:
        sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
        sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

    s1.cmd('mkdir -p ' + PCAP_LOGS)
    s1.cmd('mkdir -p ' + AUTH_LOGS)

    # pcap(s1, name=interface, intf=interface)
    pcap(s1, name='openflow', intf='lo', port='1812')
    pcap(auth, name='freeradius', intf='lo', port='6653')
    pcap(auth, name='sdn-hostapd')
    pcap(ev)
    pcap(scada)

    mn.start()

    # auth won't connect to local interf if I set the ARP
    # auth.setARP('10.0.0.1', mac_address)
    s1.cmd('ifconfig ' + interface + ' 0.0.0.0')
    s1.cmd('ifconfig s1 10.0.0.1 netmask 255.0.0.0')

    freeradius(auth)
    hostapd(auth)

    wpa(ev)
    log_sleep(.1)

    wpa(scada)

    log_sleep(.1)
    wpa_cli(scada, 'scada_ping.sh')

    log_sleep(5)

    s1.cmdPrint('pkill -2 wpa_cli')
    s1.cmdPrint('pkill -2 wpa_supplicant')
    s1.cmdPrint('pkill -2 hostapd')
    s1.cmdPrint('pkill -2 freeradius')
    s1.cmdPrint('ovs-ofctl dump-flows s1 > ' + LOGS + 's1.log')
    s2.cmdPrint('ovs-ofctl dump-flows s2 > ' + LOGS + 's2.log')
    s1.cmdPrint('chmod +r ' + AUTH_LOGS + 'freeradius.log')
    s1.cmdPrint('pkill -2 tcpdump')
    mn.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    main(argv[1], argv[2])
