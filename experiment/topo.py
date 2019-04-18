from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, lg as logger
from mininet.node import RemoteController


class Simple_Topology(Topo):
    def __init__(self):
        Topo.__init__(self)

        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        self.addLink(h1, s1)
        self.addLink(s1, s2)
        self.addLink(s2, h2)


def main():
    topo = Simple_Topology()
    mn = Mininet(topo=topo, controller=None)
    mn.addController(
        'c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    h1, h2, s1, s2 = mn.get('h1', 'h2', 's1', 's2')

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

    h2.cmd('tcpdump -i h2-eth0 -w logs/h2.pcap &')
    h1.cmd('tcpdump -i h1-eth0 -w logs/h1.pcap &')
    h1.cmd('tcpdump -i lo -w logs/h1-lo.pcap &')
    s1.cmd('tcpdump -i lo -w logs/s1-lo.pcap &')
    mn.start()
    h1.cmd('ping -c 1 10.0.0.2')
    h1.cmdPrint('freeradius -X > logs/radius.log 2>&1 &')
    h1.cmdPrint('./hostapd hostapd.conf > logs/hostapd.log 2>&1 &')

    h1.cmdPrint('nc -l 10000 > logs/nc.log 2>&1 &')
    h2.cmdPrint(
        'wpa_supplicant -i h2-eth0 -D wired -c scada.conf '
        '> logs/wpa.log 2>&1 &')
    # app.exe > logs/save_to.log 2>&1 &
    h1.cmd('ping -c 1 10.0.0.2')
    h2.cmdPrint('pkill -2 tcpdump')
    s1.cmd('ovs-ofctl dump-flows s1 > logs/s1.log')
    s2.cmd('ovs-ofctl dump-flows s1 > logs/s2.log')
    mn.stop()


topos = {'simple_topo': (lambda: Simple_Topology())}

if __name__ == '__main__':
    setLogLevel('info')
    main()
