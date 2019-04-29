from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
from mininet.node import RemoteController


class Simple_Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        h1 = self.addHost(  # TODO Improve
            'h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01', inNamespace=False)
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(h1, s1)
        self.addLink(s1, s2)
        self.addLink(s2, h2)
        self.addLink(s1, h3)


def main():
    # app.exe > logs/save_to.log 2>&1 &
    mn = Mininet(topo=Simple_Topology(), controller=None)
    mn.addController(
        'c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    auth, ev, scada, s1, s2 = mn.get('h1', 'h2', 'h3', 's1', 's2')

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

    ev.cmd('tcpdump -i h2-eth0 -w logs/ev.pcap &')
    auth.cmd('tcpdump -i h1-eth0 -w logs/auth.pcap &')
    auth.cmd('tcpdump -i lo -w logs/auth-lo.pcap &')
    s1.cmd('tcpdump -i lo -w logs/s1-lo.pcap &')
    scada.cmd('tcpdump -i h3-eth0 -w logs/scada.pcap &')
    mn.start()

    scada.cmd('ping -c 1 10.0.0.2')

    auth.cmdPrint('freeradius -t -xx -l logs/radius.log')
    auth.cmdPrint('./hostapd hostapd.conf -t > logs/hostapd.log 2>&1 &')

    scada.cmdPrint(
        'wpa_supplicant -i h3-eth0 -D wired -c scada.conf '
        '-dd -B -f logs/wpa-scada.log')
    ev.cmdPrint(
        'wpa_supplicant -i h2-eth0 -D wired -c ev.conf '
        '-dd -B -f logs/wpa-ev.log')

    scada.cmd('ping -c 1 10.0.0.2')

    s1.cmdPrint('pkill -2 tcpdump')
    s1.cmdPrint('pkill -2 wpa_supplicant')
    s1.cmdPrint('pkill -2 hostapd')
    s1.cmdPrint('pkill -2 freeradius')
    s1.cmd('ovs-ofctl dump-flows s1 > logs/s1.log')
    s2.cmd('ovs-ofctl dump-flows s1 > logs/s2.log')
    s1.cmdPrint('chmod +r logs/radius.log')
    mn.stop()


if __name__ == '__main__':
    setLogLevel('debug')
    main()
