def virtual_network_update(name, vn_project, conf=None, **kwargs):
    '''
    Update Contrail virtual network
    CLI Example:
    .. code-block:: bash
    salt '*' contrail.virtual_network_create name

    salt.cmdRun(pepperEnv, 'ntw01*', 'salt-call contrail.virtual_network_update
    "testicek" "admin" "{"external":"True","ip":"172.16.111.0","prefix":24,
    "asn":64512,"target":10000}" ')

    Parameters:
    name required - name of the new network
    project required - which project use for vn creation

    conf (dict) optional:
        domain (string) optional - which domain use for vn creation
        ip_prefix (string) optional - format is xxx.xxx.xxx.xxx
        ip_prefix_len (int) optional - format is xx
        asn (int) optional - autonomus system number
        target (int) optional - route target number
        external (boolean) optional - set if network is external

        allow_transit (boolean) optional - enable allow transit
        forwarding_mode (any of ['l2_l3','l2','l3']) optional
            - packet forwarding mode for this virtual network
        rpf (any of ['enabled','disabled']) optional
            - Enable or disable Reverse Path Forwarding check
        for this network
        mirror_destination (boolean) optional
            - Mark the vn as mirror destination network
    '''
    if conf is None:
        conf = {}

    # check for domain, is missing set to default-domain
    if 'domain' in conf:
        vn_domain = str(conf['domain'])
    else:
        vn_domain = 'default-domain'

    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': ''}

    # list of existing vn networks
    vn_networks = []
    vnc_client = _auth(**kwargs)
    vn_obj = None

#    gsc_obj = vnc_client.project_read(fq_name=[vn_domain,
#                                               vn_project])
    # check if the network exists
    vn_networks_list = vnc_client._objects_list('virtual_network')
    fq = [vn_domain, vn_project, name]
    for network in vn_networks_list['virtual-networks']:
        if fq == network['fq_name']:
            # if network exist take it and end loop
            vn_obj = vnc_client.virtual_network_read(fq_name=fq)
            break

    if vn_obj is None:
        ret['comment'] = ("Network with name {0} in domain {1} and project " +
                          " {2} does not exists").format(name, vn_domain,
                                                         vn_project)
        return ret

    vn_type_obj = VirtualNetworkType()
    # get ipam from default project and domain
    ipam = vnc_client.network_ipam_read(fq_name=[ipam_domain,
                                                 ipam_project,
                                                 ipam_name])

    # create subnet
    if 'ip_prefix' in conf and 'ip_prefix_len' in conf:
        ipam_subnet_type = IpamSubnetType(subnet=SubnetType(
                                          ip_prefix=conf['ip_prefix'],
                                          ip_prefix_len=conf['ip_prefix_len']))

        vn_subnets_type_obj = VnSubnetsType(ipam_subnets=[ipam_subnet_type])
        vn_obj.add_network_ipam(ipam, vn_subnets_type_obj)

    # add route target to the network
    if 'asn' in conf and 'target' in conf:
        route_target_list_obj = RouteTargetList(["target:{0}:{1}"
                                                 .format(conf['asn'],
                                                         conf['target'])])
        vn_obj.set_route_target_list(route_target_list_obj)

    if 'external' in conf:
        vn_obj.set_router_external(conf['external'])

    if 'allow_transit' in conf:
        vn_type_obj.set_allow_transit(conf['allow_transit'])

    if 'forwarding_mode' in conf:
        if conf['forwarding_mode'] in ['l2_l3', 'l2', 'l3']:
            vn_type_obj.set_forwarding_mode(conf['forwarding_mode'])

    if 'rpf' in conf:
        vn_type_obj.set_rpf(conf['rpf'])

    if 'mirror_destination' in conf:
        vn_type_obj.set_mirror_destination(conf['mirror_destination'])

    vn_obj.set_virtual_network_properties(vn_type_obj)

    # create virtual network
    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = ("Virtual network with name {0} will be created"
                          .format(name))
    else:
        vnc_client.virtual_network_create(vn_obj)
        ret['comment'] = ("Virtual network with name {0} was created"
                          .format(name))
    return ret
