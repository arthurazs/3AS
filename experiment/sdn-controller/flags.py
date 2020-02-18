from ryu import cfg

CONF = cfg.CONF
CONF.register_cli_opts([
    cfg.StrOpt(
        'num_ev', default=None, help='Total number of EVs'),
    cfg.StrOpt(
        'ev_by_sw', default=None, help='Number of EVs by Switch'),
])
