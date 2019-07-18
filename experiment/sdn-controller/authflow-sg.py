# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib import hub
from hostapd_socket import HostapdSocket
ETH_TYPE_8021x = 0x888E
EAPOL_MAC = '01:80:c2:00:00:03'
SCADA_MAC = '00:00:00:00:00:03'


class ExampleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ExampleSwitch13, self).__init__(*args, **kwargs)
        CONTROLLER_MAC = self.CONF.mac_address
        self.logger.info('>>> SDN Controller MAC ' + CONTROLLER_MAC)

        # known hosts
        self.mac_to_port = {
            1: {
                EAPOL_MAC: 3,               # s1, EAPOL to port 3
                '00:00:00:00:00:02': 3,     # s1, EAPOL to port 3
                CONTROLLER_MAC: 2,          # s1, LOCAL to port 2
                SCADA_MAC: 4,               # s1, SCADA to port 4
            },
            2: {
                EAPOL_MAC: 1,               # s2, EAPOL to port 1
                '00:00:00:00:00:02': 1,     # s2, EAPOL to port 1
                CONTROLLER_MAC: 1,          # s2, LOCAL to port 1
                SCADA_MAC: 1,               # s2, SCADA to port 1
            },
        }

        # authorized hosts
        self.portDict = {
            CONTROLLER_MAC: {
                u'identity': u'controller',
                u'address': CONTROLLER_MAC},
            u'00:00:00:00:00:02':  {
                u'identity': u'authenticator',
                u'address': u'00:00:00:00:00:02'},
            SCADA_MAC: {
                u'identity': u'controller',
                u'address': SCADA_MAC},
        }
        self.hostapd_socket = HostapdSocket(
            self.logger, portDict=self.portDict)
        hub.spawn(self.hostapd_socket.start_socket)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst,
                                hard_timeout=timeout)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        src = eth_pkt.src
        dst = eth_pkt.dst
        if eth_pkt.ethertype == ETH_TYPE_8021x or src in self.portDict:
            self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

            # learn a mac address to avoid FLOOD next time.
            self.mac_to_port[dpid][src] = in_port

            # if the destination mac address is already learned,
            # decide which port to output the packet, otherwise FLOOD.
            out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)

            # construct action list.
            actions = [parser.OFPActionOutput(out_port)]

            # install a flow to avoid packet_in next time.
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(
                    in_port=in_port, eth_dst=dst, eth_type=eth_pkt.ethertype)
                self.add_flow(datapath, 2, match, actions)

            # construct packet_out message and send it.
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=in_port, actions=actions,
                data=msg.data)
            datapath.send_msg(out)
        else:
            self.logger.info(
                '>>> s' + str(dpid) + ' DROP from ' + str(src) +
                ' (port ' + str(in_port) + ') to ' + str(dst))
            match = parser.OFPMatch(
                in_port=in_port, eth_src=src,
                eth_dst=dst, eth_type=eth_pkt.ethertype)
            self.add_flow(datapath, 1, match, [], 1)  # drop
