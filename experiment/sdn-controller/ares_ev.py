# Copyright (C) 2012 Nippon Telegraph and Telephone Corporation.
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

import logging
import json

from ryu import cfg
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import WSGIApplication

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

from ryu.ofproto.ether import ETH_TYPE_IP
from datetime import datetime


def ceil(dividend, divisor):
    return -(-dividend // divisor)


def ip_adder(value):
    # IP Address Adder for netmask /16
    rest, network, host = value.rsplit('.', 2)
    host = (int(host) % 254) + 1
    network = int(network) + int(host == 1)
    return rest + '.' + str(network) + '.' + str(host)


LOG = logging.getLogger('ryu.app.ofctl_rest')

MMS_IP = '10.0.1.3'
MMS_TCP = 102
ETH_TYPE_8021X = 0x888E
ETH_TYPE_GOOSE = 0x88B8
EAPOL_MAC = u'01:80:c2:00:00:03'
SCADA_MAC = u'00:00:00:00:00:03'
BROADCAST_MAC = u'ff:ff:ff:ff:ff:ff'
CONTROLLER_MAC = u'00:00:00:00:00:01'
AUTH_MAC = '00:00:00:00:00:02'

NUM_EV = int(cfg.CONF.num_ev)
EV_BY_SW = int(cfg.CONF.ev_by_sw)
evs = {}
ip = '10.0.1.3'
for index in range(1, NUM_EV + 1):
    port = ((index - 1) % EV_BY_SW) + 2
    ip = ip_adder(ip)
    evs['ev' + str(index)] = {
        'ip': ip,
        'port': port
    }

mms_auth = {1: 1}
for index in range(2, ceil(NUM_EV, EV_BY_SW) + 2):
    mms_auth[index] = 1

mms_controller = {1: ofproto_v1_3.OFPP_LOCAL}
for index in range(2, ceil(NUM_EV, EV_BY_SW) + 2):
    mms_controller[index] = 1

mms_scada = {1: 2}
for index in range(2, ceil(NUM_EV, EV_BY_SW) + 2):
    mms_scada[index] = 1


def log(message):
    LOG.info('>>> %s %s' % (datetime.now(), message))


def add_authenticator_flow(datapath):
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    inst_to = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [
        parser.OFPActionOutput(ofproto_v1_3.OFPP_LOCAL)])]
    match_to = parser.OFPMatch(
        in_port=1, eth_src='00:00:00:00:00:02', eth_dst=CONTROLLER_MAC)

    inst_from = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, [
        parser.OFPActionOutput(1)])]
    match_from = parser.OFPMatch(
        in_port=ofproto_v1_3.OFPP_LOCAL, eth_dst='00:00:00:00:00:02',
        eth_src=CONTROLLER_MAC)

    mod = parser.OFPFlowMod(
        datapath=datapath, priority=1,
        match=match_to, instructions=inst_to,
        command=ofproto.OFPFC_ADD)
    datapath.send_msg(mod)

    mod = parser.OFPFlowMod(
        datapath=datapath, priority=1,
        match=match_from, instructions=inst_from,
        command=ofproto.OFPFC_ADD)
    datapath.send_msg(mod)


def add_mms_flow(datapath, mac, ip, port):
    dpid = datapath.id
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    inst_to = [parser.OFPInstructionActions(
        ofproto.OFPIT_APPLY_ACTIONS,
        [parser.OFPActionOutput(port)])]
    match_to = parser.OFPMatch(
        eth_type=ETH_TYPE_IP, ip_proto=6,
        in_port=mms_scada[dpid], eth_src=SCADA_MAC,
        eth_dst=mac, ipv4_src=MMS_IP, ipv4_dst=ip, tcp_src=MMS_TCP)

    inst_from = [parser.OFPInstructionActions(
        ofproto.OFPIT_APPLY_ACTIONS,
        [parser.OFPActionOutput(mms_scada[dpid])])]
    match_from = parser.OFPMatch(
        eth_type=ETH_TYPE_IP, ip_proto=6,
        in_port=port, eth_src=mac, eth_dst=SCADA_MAC,
        ipv4_src=ip, ipv4_dst=MMS_IP, tcp_dst=MMS_TCP)

    mod = parser.OFPFlowMod(
        datapath=datapath, priority=3,
        match=match_to, instructions=inst_to,
        command=ofproto.OFPFC_ADD)
    datapath.send_msg(mod)

    mod = parser.OFPFlowMod(
        datapath=datapath, priority=3,
        match=match_from, instructions=inst_from,
        command=ofproto.OFPFC_ADD)
    datapath.send_msg(mod)


def add_goose_flow(datapath, mac, group, in_port, out_port):
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    actions = [parser.OFPActionOutput(out_port)]
    match = parser.OFPMatch(
        eth_type=ETH_TYPE_GOOSE, in_port=in_port, eth_src=mac, eth_dst=group)

    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    mod = parser.OFPFlowMod(
        datapath=datapath, priority=3,
        match=match, instructions=inst,
        command=ofproto.OFPFC_ADD)
    datapath.send_msg(mod)


class StatsController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(StatsController, self).__init__(req, link, data, **config)
        self.dpset = data['dpset']
        self.waiters = data['waiters']
        self.authenticated = data['authenticated']
        self.switches = []
        for index in range(1, ceil(NUM_EV, EV_BY_SW) + 2):
            self.switches.append(self.dpset.get(index))

    def auth_user(self, req, mac, identity, **_kwargs):
        # TODO Investigate the use of diffie-hellman
        log('%s (%s) authenticated successfuly' % (identity, mac))
        ev_number = int(identity[2:])
        ip = evs[identity]['ip']
        port = evs[identity]['port']
        log('Installing MMS flows (%s <-> scada)' % identity)

        s1_port = ((ev_number - 1) // EV_BY_SW) + 3
        add_mms_flow(self.switches[0], mac, ip, s1_port)
        ev_switch = self.switches[s1_port - 2]
        add_mms_flow(ev_switch, mac, ip, port)

        self.authenticated[mac] = {
            'address': mac, 'identity': identity}
        body = json.dumps(
            "{'AUTH-OK':" + str(self.authenticated[mac]) + '}')
        return Response(content_type='application/json', body=body)

    def deauth_user(self, req, mac, **_kwargs):
        if mac in self.authenticated:
            unauthenticated = self.authenticated[mac]
            identity = unauthenticated['identity']
            del self.authenticated[mac]
            log('%s (%s) deauthenticated successfuly' % (identity, mac))
            log('Removing flows requested by %s' % identity)
            # TODO Remove flow after being unauthenticated
            body = json.dumps(
                "{'AUTH-NOT':" + str(unauthenticated) + '}')
            return Response(content_type='application/json', body=body)
        log("{'NOT-OK': 'MAC not found'}")
        return Response(status=400)


class RestStatsApi(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(RestStatsApi, self).__init__(*args, **kwargs)

        LOG.info('>>> SDN Controller MAC ' + CONTROLLER_MAC)

        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        self.waiters = {}
        self.data = {}
        self.data['dpset'] = self.dpset
        self.data['waiters'] = self.waiters
        mapper = wsgi.mapper

        # authenticated hosts
        self.authenticated = {
            CONTROLLER_MAC: {
                u'identity': u'controller',
                u'address': CONTROLLER_MAC},
            u'00:00:00:00:00:02':  {
                u'identity': u'authenticator',
                u'address': u'00:00:00:00:00:02'},
            SCADA_MAC: {
                u'identity': u'controller',
                u'address': SCADA_MAC},
            BROADCAST_MAC: {
                u'identity': u'broadcast',
                u'address': BROADCAST_MAC},
        }

        # known hosts
        self.mac_to_port = {}

        for index in range(1, ceil(NUM_EV, EV_BY_SW) + 2):
            self.mac_to_port[index] = {
                EAPOL_MAC: mms_auth[index],
                AUTH_MAC: mms_auth[index],
                CONTROLLER_MAC: mms_controller[index],
                SCADA_MAC: mms_scada[index],
            }

        self.data['authenticated'] = self.authenticated

        wsgi.registory['StatsController'] = self.data

        uri = '/authenticated/{mac}/{identity}'
        mapper.connect('stats', uri,
                       controller=StatsController, action='auth_user',
                       conditions=dict(method=['GET']))

        uri = '/deauthenticated/{mac}'
        mapper.connect('stats', uri,
                       controller=StatsController, action='deauth_user',
                       conditions=dict(method=['GET']))

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

        if datapath.id == 1:
            add_authenticator_flow(datapath)

    def add_flow(self, datapath, priority, match, actions, timeout=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst,
                                command=ofproto.OFPFC_ADD,
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
        src = eth_pkt.src.lower()
        dst = eth_pkt.dst.lower()
        if eth_pkt.ethertype == ETH_TYPE_8021X:
            LOG.info(
                '802.1X packet in s%s %s -> %s (port %s)',
                dpid, src, dst, in_port)

            # learn a mac address to avoid FLOOD next time.
            self.mac_to_port[dpid][src] = in_port

            # if the destination is knwon, output the packet to the correct
            # port, otherwise FLOOD.
            out_port = self.mac_to_port[dpid].get(dst, ofproto.OFPP_FLOOD)

            # construct action list.
            actions = [parser.OFPActionOutput(out_port)]

            # install a flow to avoid packet_in next time.
            if out_port != ofproto.OFPP_FLOOD:
                match = parser.OFPMatch(
                    in_port=in_port, eth_src=src,
                    eth_dst=dst, eth_type=eth_pkt.ethertype)
                self.add_flow(datapath, 2, match, actions)

            # construct packet_out message and send it.
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=in_port, actions=actions,
                data=msg.data)
            datapath.send_msg(out)
        else:
            unauthenticated = dst if src in self.authenticated else src
            frame = 'GOOSE' if eth_pkt.ethertype == ETH_TYPE_GOOSE \
                    else eth_pkt.ethertype
            log('s%i: Drop %s %s (port %i) -> %s'
                % (dpid, frame, src, in_port, dst))
            log('REASON: %s is not authenticated' % unauthenticated)
            match = parser.OFPMatch(
                in_port=in_port, eth_src=src,
                eth_dst=dst,
                # eth_type=eth_pkt.ethertype
            )
            self.add_flow(datapath, 1, match, [])  # drop
