from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
from mininet.node import RemoteController
from time import sleep as _sleep


ROOT = 'experiment/'
AUTH_ROOT = ROOT + 'authenticator/'
IEDS_ROOT = ROOT + 'ieds/'

LOGS = 'logs/'
AUTH_LOGS = LOGS + 'auth/'
PCAP_LOGS = LOGS + 'pcap/'


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
    command = 'wpa_supplicant -i ' + str(node.intf()) + ' -D wired'
    config = '-c ' + IEDS_ROOT + str(node) + '.conf -dd -f'
    log = AUTH_LOGS + 'wpa-' + str(node) + '.log &'
    node.cmdPrint(command, config, log)


def wpa_cli(node, script, name):
    command = 'wpa_cli -i ' + str(node.intf())
    filename = '-a ' + IEDS_ROOT + script
    log = '> ' + AUTH_LOGS + name + '.log 2>&1 &'
    node.cmdPrint(command, filename, log)


def pcap(node, name=None, intf=None, port=None):
    if not name:
        name = str(node)
    if not intf:
        intf = node.intf()
    command = 'tcpdump -i ' + str(intf) + ' -w'
    log = PCAP_LOGS + name + '.pcap'
    tail = 'port not ' + str(port) if port else ''
    node.cmdPrint(command, log, tail, '&')


def sleep(time):
    logger.info('*** Sleeping for {} seconds...\n'.format(time))
    _sleep(time)


class Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        auth = self.addHost('auth', ip='10.0.1.2/24', mac='00:00:00:00:00:02')
        # scada = self.addHost('scada', ip='10.0.1.3/24', mac='00:00:00:00:00:03')
        ied1 = self.addHost('ied1', ip='10.0.1.4/24', mac='00:00:00:00:00:04')
        ied2 = self.addHost('ied2', ip='10.0.1.5/24', mac='00:00:00:00:00:05')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(s1, s2, 1, 1)
        self.addLink(s1, auth, 2, 0)
        # self.addLink(s1, scada, 3, 0)
        self.addLink(s2, ied1, 2, 0)
        self.addLink(s2, ied2, 3, 0)


def main():
    # app.exe > ../logs/save_to.log 2>&1 &
    mn = Mininet(  # TODO Test without static ARP
        topo=Topology(), autoStaticArp=True,
        controller=RemoteController('c0', ip='127.0.0.1', port=6653))
    auth, s1, s2 = mn.get('auth', 's1', 's2')
    ied1, ied2 = mn.get('ied1', 'ied2')

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

    ied1.setARP('10.0.1.1', '00:00:00:00:00:01')
    ied2.setARP('10.0.1.1', '00:00:00:00:00:01')

    s1.cmd('mkdir -p ' + PCAP_LOGS)
    s1.cmd('mkdir -p ' + AUTH_LOGS)

    pcap(s1, name='openflow', intf='lo', port='1812')
    pcap(auth, name='freeradius', intf='lo')
    pcap(auth, name='sdn-hostapd')
    pcap(ied1)
    pcap(ied2)

    mn.start()

    s1.cmd('ifconfig s1 10.0.1.1 netmask 255.255.255.0')
    s1.cmd('ovs-vsctl set bridge s1 other-config:hwaddr=00:00:00:00:00:01')
    s1.setARP('10.0.1.4', '00:00:00:00:00:04')
    s1.setARP('10.0.1.5', '00:00:00:00:00:05')
    s1.setARP('10.0.1.2', '00:00:00:00:00:02')
    auth.setARP('10.0.1.1', '00:00:00:00:00:01')
    pcap(s1, name='controller', intf='s1', port='53')

    freeradius(auth)
    hostapd(auth)

    ied1.cmd('experiment/ieds/./server_ied_pub', ied1.intf(), '&')
    ied2.cmd('experiment/ieds/./server_ied_sub', ied2.intf(), '&')

    wpa(ied1)
    sleep(10)
    wpa(ied2)

    sleep(15)
    s1.cmdPrint('pkill -2 wpa_cli')
    s1.cmdPrint('pkill -2 wpa_supplicant')
    sleep(2)
    s1.cmdPrint('pkill -2 hostapd')
    sleep(2)
    s1.cmdPrint('pkill -2 freeradius')
    s1.cmdPrint('pkill -2 server_ied')
    s1.cmdPrint('ovs-ofctl dump-flows s1 > ' + LOGS + 's1.log')
    s2.cmdPrint('ovs-ofctl dump-flows s2 > ' + LOGS + 's2.log')
    s1.cmdPrint('chmod +r ' + AUTH_LOGS + 'freeradius.log')
    s1.cmdPrint('pkill -2 tcpdump')

    mn.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    main()
