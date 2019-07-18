from ryu import cfg

CONF = cfg.CONF
CONF.register_cli_opts([
    cfg.StrOpt(
        'mac_address', default=None, help='Local ethernet MAC address')
])
