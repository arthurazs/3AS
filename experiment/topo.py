from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
from mininet.node import RemoteController
from time import sleep


class Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        h1 = self.addHost(  # TODO Improve
            'h1', inNamespace=False, ip='10.0.0.1', mac='00:00:00:00:00:01')
        scada = self.addHost(
            'scada', ip='10.0.0.2', mac='00:00:00:00:00:02')
        ev = self.addHost(
            'ev', ip='10.0.0.3', mac='00:00:00:00:00:03')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(s1, h1)
        self.addLink(s1, scada)
        self.addLink(s1, s2)
        self.addLink(s2, ev)


def log_sleep(time):
    logger.info('*** Sleeping for {} seconds...\n'.format(time))
    sleep(time)


def main():
    # app.exe > logs/save_to.log 2>&1 &
    mn = Mininet(  # TODO Test without static ARP
        topo=Topology(),  # autoSetMacs=True,
        autoStaticArp=True,
        controller=RemoteController('c0', ip='127.0.0.1', port=6653))
    auth, scada, ev, s1, s2 = mn.get('h1', 'scada', 'ev', 's1', 's2')

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

    s1.cmd('tcpdump -i lo -w logs/openflow.pcap port not 1812 &')
    s1.cmd('tcpdump -i s1-eth1 -w logs/s1-eth1.pcap &')
    s1.cmd('tcpdump -i s1-eth2 -w logs/s1-eth2.pcap &')
    s1.cmd('tcpdump -i s1-eth3 -w logs/s1-eth3.pcap &')
    auth.cmd('tcpdump -i lo -w logs/radius.pcap port not 6653 &')
    auth.cmd('tcpdump -i h1-eth0 -w logs/hostapd.pcap &')
    ev.cmd('tcpdump -i ev-eth0 -w logs/ev.pcap &')
    scada.cmd('tcpdump -i scada-eth0 -w logs/scada.pcap &')
    mn.start()

    # sleep(5)

    # scada.cmd('ping -c 1 10.0.0.2')

    auth.cmdPrint('freeradius -t -xx -l logs/radius.log')
    auth.cmdPrint('./hostapd hostapd.conf -t > logs/hostapd.log 2>&1 &')

    # sleep(5)

    ev.cmdPrint(
        'wpa_supplicant -i ev-eth0 -D wired -c ev.conf '
        '-dd -B -f logs/wpa-ev.log')
    log_sleep(.1)

    scada.cmdPrint(
        'wpa_supplicant -D wired -c scada.conf -i scada-eth0 '
        # '-B -f logs/wpa-scada.log ')
        '-dd -B -f logs/wpa-scada.log ')

    # sleep(.5)
    scada.cmdPrint(
        'wpa_cli -iscada-eth0 -a scada_ping.sh > logs/ping.log 2>&1 &')

    log_sleep(5)

    s1.cmdPrint('pkill -2 wpa_cli')
    s1.cmdPrint('pkill -2 wpa_supplicant')
    s1.cmdPrint('pkill -2 hostapd')
    s1.cmdPrint('pkill -2 freeradius')
    s1.cmdPrint('ovs-ofctl dump-flows s1 > logs/s1.log')
    s2.cmdPrint('ovs-ofctl dump-flows s1 > logs/s2.log')
    s1.cmdPrint('chmod +r logs/radius.log')
    s1.cmdPrint('pkill -2 tcpdump')
    mn.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    main()
