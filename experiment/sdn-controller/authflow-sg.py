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
import ast

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.exception import RyuException
from ryu.ofproto import ofproto_v1_3
from ryu.lib import ofctl_v1_3
from ryu.app.wsgi import ControllerBase
from ryu.app.wsgi import Response
from ryu.app.wsgi import WSGIApplication

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

from abac import guard
from vakt import Inquiry
from mms_client import Mms

LOG = logging.getLogger('ryu.app.ofctl_rest')

# supported ofctl versions in this restful app
supported_ofctl = {ofproto_v1_3.OFP_VERSION: ofctl_v1_3}

ETH_TYPE_8021X = 0x888E
EAPOL_MAC = u'01:80:c2:00:00:03'
SCADA_MAC = u'00:00:00:00:00:03'
BROADCAST_MAC = u'ff:ff:ff:ff:ff:ff'


class CommandNotFoundError(RyuException):
    message = 'No such command : %(cmd)s'


class PortNotFoundError(RyuException):
    message = 'No such port info: %(port_no)s'


def stats_method(method):
    def wrapper(self, req, dpid, *args, **kwargs):
        # Get datapath instance from DPSet
        try:
            dp = self.dpset.get(int(str(dpid), 0))
        except ValueError:
            LOG.exception('Invalid dpid: %s', dpid)
            return Response(status=400)
        if dp is None:
            LOG.error('No such Datapath: %s', dpid)
            return Response(status=404)

        # Get lib/ofctl_* module
        try:
            ofctl = supported_ofctl.get(dp.ofproto.OFP_VERSION)
        except KeyError:
            LOG.exception('Unsupported OF version: %s',
                          dp.ofproto.OFP_VERSION)
            return Response(status=501)

        # Invoke StatsController method
        try:
            ret = method(self, req, dp, ofctl, *args, **kwargs)
            return Response(content_type='application/json',
                            body=json.dumps(ret))
        except ValueError:
            LOG.exception('Invalid syntax: %s', req.body)
            return Response(status=400)
        except AttributeError:
            LOG.exception('Unsupported OF request in this version: %s',
                          dp.ofproto.OFP_VERSION)
            return Response(status=501)

    return wrapper


def command_method(method):
    def wrapper(self, req, *args, **kwargs):
        # Parse request json body
        try:
            if req.body:
                body = ast.literal_eval(req.body.decode('utf-8'))
            else:
                body = {}
        except SyntaxError:
            LOG.exception('Invalid syntax: %s', req.body)
            return Response(status=400)

        # Get datapath_id from request parameters
        dpid = body.get('dpid', None)
        if not dpid:
            try:
                dpid = kwargs.pop('dpid')
            except KeyError:
                LOG.exception('Cannot get dpid from request parameters')
                return Response(status=400)

        # Get datapath instance from DPSet
        try:
            dp = self.dpset.get(int(str(dpid), 0))
        except ValueError:
            LOG.exception('Invalid dpid: %s', dpid)
            return Response(status=400)
        if dp is None:
            LOG.error('No such Datapath: %s', dpid)
            return Response(status=404)

        # Get lib/ofctl_* module
        try:
            ofctl = supported_ofctl.get(dp.ofproto.OFP_VERSION)
        except KeyError:
            LOG.exception('Unsupported OF version: version=%s',
                          dp.ofproto.OFP_VERSION)
            return Response(status=501)

        # Invoke StatsController method
        try:
            method(self, req, dp, ofctl, body, *args, **kwargs)
            return Response(status=200)
        except ValueError:
            LOG.exception('Invalid syntax: %s', req.body)
            return Response(status=400)
        except AttributeError:
            LOG.exception('Unsupported OF request in this version: %s',
                          dp.ofproto.OFP_VERSION)
            return Response(status=501)
        except CommandNotFoundError as e:
            LOG.exception(e.message)
            return Response(status=404)
        except PortNotFoundError as e:
            LOG.exception(e.message)
            return Response(status=404)

    return wrapper


class StatsController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(StatsController, self).__init__(req, link, data, **config)
        self.waiters = data['waiters']
        self.authorized = data['authorized']

    @stats_method
    def get_port_stats(self, req, dp, ofctl, port, **kwargs):
        if port == "ALL":
            port = None
        return ofctl.get_port_stats(dp, self.waiters, port)

    @command_method
    def mod_flow_entry(self, req, dp, ofctl, flow, cmd, **kwargs):
        cmd_convert = {
            'add': dp.ofproto.OFPFC_ADD,
            'modify': dp.ofproto.OFPFC_MODIFY,
            'modify_strict': dp.ofproto.OFPFC_MODIFY_STRICT,
            'delete': dp.ofproto.OFPFC_DELETE,
            'delete_strict': dp.ofproto.OFPFC_DELETE_STRICT,
        }
        mod_cmd = cmd_convert.get(cmd, None)
        if mod_cmd is None:
            raise CommandNotFoundError(cmd=cmd)

        ofctl.mod_flow_entry(dp, flow, mod_cmd)

    def auth_user(self, req, mac, identity, **_kwargs):
        self.authorized[mac] = {'address': mac, 'identity': identity}
        with Mms('10.0.0.4') as ied:
            goose_group = ied.read_goose_group()
        publish_goose = Inquiry(
            action={'type': 'publish', 'dest': goose_group},
            resource='GOOSE',
            subject=identity)
        if guard.is_allowed(publish_goose):
            LOG.info(">>> {'AUTH-OK':" + str(self.authorized[mac]) + '}')
            body = json.dumps("{'AUTH-OK':" + str(self.authorized[mac]) + '}')
            return Response(content_type='application/json', body=body)
        else:
            LOG.info(">>> {'NOT-OK':" + str(self.authorized[mac]) + '}')
            return Response(status=400)


class RestStatsApi(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __init__(self, *args, **kwargs):
        super(RestStatsApi, self).__init__(*args, **kwargs)

        CONTROLLER_MAC = self.CONF.mac_address
        LOG.info('>>> SDN Controller MAC ' + CONTROLLER_MAC)

        self.dpset = kwargs['dpset']
        wsgi = kwargs['wsgi']
        self.waiters = {}
        self.data = {}
        self.data['dpset'] = self.dpset
        self.data['waiters'] = self.waiters
        mapper = wsgi.mapper

        # authorized hosts
        self.authorized = {
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

        # device discovery
        self.hosts = {
            # mac: (dpid, port),
        }

        self.data['authorized'] = self.authorized

        wsgi.registory['StatsController'] = self.data

        uri = '/port/{dpid}/{port}'
        mapper.connect('stats', uri,
                       controller=StatsController, action='get_port_stats',
                       conditions=dict(method=['GET']))

        uri = '/flowentry/{cmd}'
        mapper.connect('stats', uri,
                       controller=StatsController, action='mod_flow_entry',
                       conditions=dict(method=['POST']))

        uri = '/authenticated/{mac}/{identity}'
        mapper.connect('stats', uri,
                       controller=StatsController, action='auth_user',
                       conditions=dict(method=['GET']))

    @set_ev_cls([ofp_event.EventOFPStatsReply,
                 ofp_event.EventOFPDescStatsReply,
                 ofp_event.EventOFPFlowStatsReply,
                 ofp_event.EventOFPAggregateStatsReply,
                 ofp_event.EventOFPTableStatsReply,
                 ofp_event.EventOFPTableFeaturesStatsReply,
                 ofp_event.EventOFPPortStatsReply,
                 ofp_event.EventOFPQueueStatsReply,
                 ofp_event.EventOFPQueueDescStatsReply,
                 ofp_event.EventOFPMeterStatsReply,
                 ofp_event.EventOFPMeterFeaturesStatsReply,
                 ofp_event.EventOFPMeterConfigStatsReply,
                 ofp_event.EventOFPGroupStatsReply,
                 ofp_event.EventOFPGroupFeaturesStatsReply,
                 ofp_event.EventOFPGroupDescStatsReply,
                 ofp_event.EventOFPPortDescStatsReply
                 ], MAIN_DISPATCHER)
    def stats_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath

        if dp.id not in self.waiters:
            return
        if msg.xid not in self.waiters[dp.id]:
            return
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)

        flags = 0
        if dp.ofproto.OFP_VERSION >= ofproto_v1_3.OFP_VERSION:
            flags = dp.ofproto.OFPMPF_REPLY_MORE

        if msg.flags & flags:
            return
        del self.waiters[dp.id][msg.xid]
        lock.set()

    @set_ev_cls([ofp_event.EventOFPSwitchFeatures,
                 ofp_event.EventOFPQueueGetConfigReply,
                 ofp_event.EventOFPRoleReply,
                 ], MAIN_DISPATCHER)
    def features_reply_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath

        if dp.id not in self.waiters:
            return
        if msg.xid not in self.waiters[dp.id]:
            return
        lock, msgs = self.waiters[dp.id][msg.xid]
        msgs.append(msg)

        del self.waiters[dp.id][msg.xid]
        lock.set()

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
        src = eth_pkt.src.lower()
        dst = eth_pkt.dst.lower()
        if eth_pkt.ethertype == ETH_TYPE_8021X or (
                src in self.authorized and dst in self.authorized):
            LOG.info("packet in %s %s %s %s", dpid, src, dst, in_port)

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
            unauthorized = dst if src in self.authorized else src
            LOG.info(
                '>>> ' + unauthorized + ' is not authenticated\n'
                '>>> s' + str(dpid) + ' DROP from ' + str(src) +
                ' (port ' + str(in_port) + ') to ' + str(dst)
            )
            match = parser.OFPMatch(
                in_port=in_port, eth_src=src,
                eth_dst=dst, eth_type=eth_pkt.ethertype)
            self.add_flow(datapath, 1, match, [], 1)  # drop
