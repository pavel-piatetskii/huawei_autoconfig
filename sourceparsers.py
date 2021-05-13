import re
from math import log2


class ReplacementFromFile:

    def __init__(self, sourcefile):

        self.ethport = []
        self.gigaport = []
        self.other_vlans = {}
        self.mixed = 0

        origin_cfg = open(sourcefile).read()
        vendor = re.search('(?<=CONTENT-TYPE: ).+', origin_cfg)[0]

        # Choose parser for Huawei or for D-Link switches
        if vendor == 'h3c':
            self.source_huawei(origin_cfg)
        elif vendor == 'dlink':
            self.source_dlink(origin_cfg)


        # self.print_results()


    def print_results(self):
        for port in self.ethport:
            print(port)
        for port in self.gigaport:
            print(port)
        print(self.other_vlans)
#
# ======================================================================================== HUAWEI CONFIGURATION PARSER ==
#
    def source_huawei(self, origin_cfg):

        model_match = re.search('(! HUAWEI S|! Quidway S).+', origin_cfg)[0]
        model = re.search('(?<= S).+?(?=\D{1,2}-)', model_match)[0]

        if model == '3328' or model == '2350-28':
            eth_rng = 24
            giga_rng = 4
        elif model == '3352' or model == '2352':
            eth_rng = 48
            giga_rng = 4
        elif model == '2320-12':
            eth_rng = 8
            giga_rng = 4
        elif model == '2320-28':
            eth_rng = 20
            giga_rng = 8
        elif model == '2320-52':
            eth_rng = 44
            giga_rng = 8

        self.port_dictionaries(eth_rng, giga_rng)

        # Search for system name
        sysname_match = re.search('sysname.+-sw-\d', origin_cfg)
        if sysname_match:
            self.sysname = (sysname_match[0].split('sysname '))[1]

        core_vlans = []
        # Search for IPTV VLAN and its ID
        viptv_match = re.search('vlan \d{1,4}\n des.+\n(?: igmp.+\n igmp.+suppress| multicast)', origin_cfg)
        if viptv_match:
            self.noiptv = 0
            self.viptv_id = (viptv_match[0].split('\n'))[0].strip('vlan ')
            core_vlans.append(self.viptv_id)            # Add IPTV-vlan to core VLANs list
        else:
            self.viptv_id = ''                          # If no IPTV VLAN, set empty string and "noiptv" flag
            self.noiptv = 1

        # Search for HomeNet VLAN and its ID, then check ports with enabled multicast
        vhnet_match = re.search('vlan \d{1,4}\n.+\n igm.+\n(?: attach| max-)[\D\d]+?(?=#|vlan)', origin_cfg)
        if vhnet_match:
            self.vhnet_id = (vhnet_match[0].split('\n'))[0].strip('vlan ')
            self.vhnet_name = (re.search('desc.+', vhnet_match[0]))[0].strip('description ')
            core_vlans.append(self.vhnet_id)  # Add HomeNet-vlan to core VLANs list
            # self.get_mcast()
            # self.mcast_ena = []
            for mcast_str in re.finditer('max-.+E.+t0.+\n', vhnet_match[0]):
                portnum = (mcast_str[0].split('0/0/'))[1]
                if re.search('attach.+iptv_all_def.+' + portnum, vhnet_match[0], flags=re.IGNORECASE):
                    self.ethport[int(portnum)-1]['mcast'] = 1
        else:
            self.vhnet_id = ''  # If no HomeNet VLAN, set empty string

        # Search for PPPoE VLAN and its ID
        vppp_match = re.search('vlan \d{,4}\n des.+\n protocol.+\n', origin_cfg)
        if vppp_match:
            self.vppp_id = (vppp_match[0].split('\n'))[0].strip('vlan ')
            self.vppp_name = (re.search('desc.+', vppp_match[0]))[0].strip('description ')
            core_vlans.append(self.vppp_id)  # Add PPPoE-vlan to core VLANs list

        # Search for additional or transit VLANs
        for vlans_match in re.finditer('vlan \d{,4}\n description.+\n', origin_cfg):
            # self.get_vlans()
            vid = (vlans_match[0].split('\n'))[0].strip('vlan ')
            vname = (vlans_match[0].split('\n'))[1].strip('description ')
            if vid not in core_vlans:
                self.other_vlans[vid] = vname

        # Search for management IP-interface, fetch address and mask
        ipmask_match = re.search('ip address 192.168.+', origin_cfg)
        if ipmask_match:
            self.ipmgmt = (ipmask_match[0].strip(' ip address ').split(' '))[0]
            directmask = (ipmask_match[0].strip(' ip address ').split(' '))[1]
            self.direct_to_prefix(directmask)

        # Search for DHCP-relay address
        relay_match = re.search('ip address 192.168.+', origin_cfg)
        if relay_match:
            self.iprelay = (relay_match[0].strip(' ip address ').split(' '))[0]

        # Search for Fast Ethernet ports configuration and pass every of these to parse individually
        for eth_match in re.finditer('\nint.+ E.+0/0/\d{,2}[\D\d]+?\n#', origin_cfg):
            # print(self.eth_match[0], '\n------------')
            self.etherport_parcer(eth_match[0])

        # Search for Gigabit Ethernet ports configuration and pass every of these to parse individually
        for giga_match in re.finditer('\nint.+ G.+0/0/\d{,2}[\D\d]+?\n#', origin_cfg):
            # print(self.giga_match[0], '\n------------')
            self.gigaport_parcer(giga_match[0])

        # Search for default route
        gateway_match = re.search('(?<=ip route-static 0.0.0.0 0.0.0.0 ).+', origin_cfg)
        if gateway_match:
            self.gateway = gateway_match[0]
        else:
            self.gateway = ''

        # Search for SNMP location
        location_match = re.search('(?<=snmp-agent sys-info location ).+', origin_cfg)
        if location_match:
            self.location = location_match[0]
        else:
            self.location = ''


    # Calculate prefix from netmask
    def direct_to_prefix(self, directmask):
        dm_oct = directmask.split('.')
        dmdec = 1
        for i in range(0, 4):
            dmdec = dmdec * (256 - int(dm_oct[i]))
        self.prefix = int(32 - log2(dmdec))

    # Fast Ethernet port configuration parser
    def etherport_parcer(self, eth_match):

        # Fetch the port number
        portnum_match = re.search('(?<=interface Ethernet0/0/)\d{1,2}', eth_match)
        index = int(portnum_match[0]) - 1

        # description 
        curr_match = re.search('(?<=description ).+', eth_match)
        if curr_match:
            self.ethport[index]['desc'] = curr_match[0]

        # shutdown or not
        curr_match = re.search('\n shutdown(?=\n)', eth_match)
        if not curr_match:
            self.ethport[index]['active'] = 1

        # Port PVID. If no PVID - set Homenet VLAN. If no HomeNet VLAN - set PPPoE VLAN ID
        curr_match = re.search('(?<=pvid vlan )\d{1,4}', eth_match)
        if curr_match:
            self.ethport[index]['pvid'] = curr_match[0]
        else:
            if self.vhnet_id:
                self.ethport[index]['pvid'] = self.vhnet_id
            else:
                self.ethport[index]['pvid'] = self.vppp_id

        # Check PPPoE only
        curr_match = re.search('traffic-pppoe any any', eth_match)
        if curr_match:
            self.ethport[index]['ppponly'] = 1

        # Search for untagged-VLANS and tagged-VLANS, set flags accordingly (u=0, u+t=1, t+2)
        untag_match = re.search('(?<=hybrid untagged vlan ).+', eth_match)
        tag_match = re.search('(?<=hybrid tagged vlan ).+', eth_match)

        if untag_match:
            self.ethport[index]['uvlans'] = untag_match[0]
        if tag_match:
            self.ethport[index]['tvlans'] = untag_match[0]

        if self.ethport[index]['uvlans'] != '' and self.ethport[index]['tvlans'] == '':

            # Check if it is a usual client port ("normal")
            e1 = self.ethport[index]['uvlans'].split(' ')
            e1.sort()
            e2 = [self.viptv_id, self.vhnet_id, self.vppp_id]
            e2.sort()
            e3 = [self.vhnet_id, self.vppp_id]
            e3.sort()
            if e1 == e2 or e1 == e3:
                self.ethport[index]['normal'] = 1

        # If there is no any VLAN on the port, set is as "normal"
        if self.ethport[index]['uvlans'] == '' and self.ethport[index]['tvlans'] == '':
            self.ethport[index]['normal'] = 1

    # Gigabit Ethernet port configuration parser
    def gigaport_parcer(self, giga_match):

        # Fetch the port number
        portnum_match = re.search('(?<=interface GigabitEthernet0/0/)\d{1,2}', giga_match)
        index = int(portnum_match[0]) - 1

        # description
        curr_match = re.search('(?<=description ).+', giga_match)
        if curr_match:
            self.gigaport[index]['desc'] = curr_match[0]

        # shutdown or not
        curr_match = re.search('\n shutdown(?=\n)', giga_match)
        if not curr_match:
            self.gigaport[index]['active'] = 1

        # uplink or not
        curr_match = re.search('trust dscp', giga_match)
        if curr_match:
            self.gigaport[index]['uplink'] = 1

        # is port speed limited to 100
        curr_match = re.search('speed 100(?=\n)', giga_match)
        if curr_match:
            self.gigaport[index]['sp100'] = 1
#
# ======================================================================================== D-LINK CONFIGURATION PARSER ==
#
    def source_dlink(self, origin_cfg):

        self.iprelay = ''

        # Define the model and form lists for ports
        model = (re.search('DES-.+?(?=( \D|FL |F |G ))', origin_cfg)[0])[-2:]
        # print(model)
        if model == '10':
            eth_rng = 8
        elif model == '18':
            eth_rng = 16
        elif model == '26' or model == '28':
            eth_rng = 24
        elif model == '52':
            eth_rng = 48
        giga_rng = int(model) - eth_rng

        self.port_dictionaries(eth_rng, giga_rng)

        # Search for system name
        sysname_match = re.search('(?<= system_name ).+-sw-\d{,2}', origin_cfg)
        if sysname_match:
            self.sysname = sysname_match[0]

        # Search for management IP-address and prefix
        ip_pref_match = re.search('(?<= ipaddress )\d{1,3}(\.\d{1,3}){3}/\d{1,2}', origin_cfg)
        self.ipmgmt = (ip_pref_match[0].split('/'))[0]
        self.prefix = (ip_pref_match[0].split('/'))[1]

        # Search for gateway address
        self.gateway = re.search('(?<= iproute default )\d{1,3}(\.\d{1,3}){3}', origin_cfg)[0]

        # Search for SNMP location
        location_match = re.search('(?<=snmp system_location ).+', origin_cfg)
        if location_match:
            self.location = location_match[0]
        else:
            self.location = ''

        # Search for IPTV VLAN and its ID, then check ports with enabled multicast
        mcast_ena_match = None
        viptv_id_match_x = re.search('create igmp.+', origin_cfg)
        if viptv_id_match_x:
            self.noiptv = 0
            viptv_id_match = re.search('(?<= )\d{1,4}', viptv_id_match_x[0])
            self.viptv_id = viptv_id_match[0]
            mcast_ena_match = re.search('(?<= member_port ).+(?= )', origin_cfg)

            if mcast_ena_match:
                ports = self.rng_to_array(mcast_ena_match[0])
                for i in ports:
                    self.ethport[i-1]['mcast'] = 1
        else:
            self.noiptv = 1

        core_vlans = []
        # Search for HomeNet VLAN
        vhnet_id_match = re.search('(?<=dhcp_relay add vlanid )\d{1,4}', origin_cfg)
        if vhnet_id_match:
            self.vhnet_id = vhnet_id_match[0]
            self.vhnet_name = re.search('(?<=create vlan ).+(?= tag ' + self.vhnet_id + ')', origin_cfg)[0]
            core_vlans.append(self.vhnet_id)
        else:
            self.vhnet_id = ''

        # Search for PPPoE VLAN
        # vppp_match = re.search('create vlan.+(_PPP[oO]E|VE)[\._][\d\D]+?untagged[\d\D]+?(?=create)', origin_cfg)[0]
        # self.vppp_id = re.search('(?<= tag )\d{1,4}', vppp_match)[0]
        # self.vppp_name = re.search('(?<=create vlan ).+(?= tag )', vppp_match)[0]
        # core_vlans.append(self.vppp_id)
        for vppp_match in re.finditer('create vlan.+(_PPP[oO]E|VE)[\._][\d\D]+?(?=(create|disable qinq|disable gvrp))', origin_cfg):
            if re.search('add untagged \d', vppp_match[0]):
                self.vppp_id = re.search('(?<= tag )\d{1,4}', vppp_match[0])[0]
                self.vppp_name = re.search('(?<=create vlan ).+(?= tag )', vppp_match[0])[0]
                core_vlans.append(self.vppp_id)

        # Templates for "normal" port
        if self.vppp_id == self.vhnet_id:
            self.mixed = 1
            normal_pattern = ''
        else:
            self.mixed = 0
            normal_pattern = [self.vppp_id, self.vhnet_id]
            normal_pattern.sort()
            normal_pattern = ' '.join(normal_pattern)

        # Search for PVIDs
        for pvid_match in re.finditer('(?<=g port_vlan |config gvrp ).+pvid \d{1,4}', origin_cfg):
            port_match = re.search('[\d,-]+(?= )', pvid_match[0])
            port_range = self.rng_to_array(port_match[0])
            pvid = re.search('(?<=pvid )\d{1,4}', pvid_match[0])

            for i in port_range:
                if i <= eth_rng:
                    self.ethport[i-1]['pvid'] = pvid[0]
                    #if pvid[0] == '1' and self.ethport[i-1]['desc'][:2] == '@@@':
                    #    self.ethport[i-1]['uvlans'] = '1'
                    #elif pvid[0] == '1' and self.ethport[i-1]['desc'][:2] != '@@@':
                    #    self.ethport[i-1]['normal'] = 1

        # Fetch VLANs data
        # Name and ID
        for vmatch in re.finditer('create vlan [\D\d]+?(?=(create|disable qinq|disable gvrp))', origin_cfg):
            vid = re.search('(?<= tag )\d{1,4}', vmatch[0])[0]
            vname = re.search('(?<=vlan ).+?(?= tag )', vmatch[0])[0]
            if vid not in core_vlans:
                self.other_vlans[vid] = vname

            # Define ports where this vlan is allowed and whether it is untagged or tagged
            untag_match = re.search('(?<= add untagged )[\d,-]+', vmatch[0])
            if untag_match:
                ports = self.rng_to_array(untag_match[0])
                for i in ports:
                    if i <= eth_rng:
                        self.ethport[i-1]['uvlans'] = (self.ethport[i-1]['uvlans'] + ' ' + vid).strip()

            tag_match = re.search('(?<= add tagged )[\d,-]+', vmatch[0])
            if tag_match:
                ports = self.rng_to_array(tag_match[0])
                for i in ports:
                    if i <= eth_rng:    # Ignore tagged vlans on uplink ports
                        self.ethport[i-1]['tvlans'] = (self.ethport[i-1]['tvlans'] + ' ' + vid).strip()

        # Search for Fast Ethernet ports parameters (name, active or not)
        for port_match in re.finditer('config ports .+speed.+state.+', origin_cfg):

            num = re.search('(?<=config ports )[\d,-]+', port_match[0])[0]
            # print(num)

            desc_match = re.search('(?<= description ).+', port_match[0])
            if desc_match:
                if re.search(' trap ', desc_match[0]):
                    desc_match = re.search('.+(?= trap )', desc_match[0])
                desc = desc_match[0].strip('"')

            active_match = re.search('state enable', port_match[0])

            try:
                num_rng = [int(num)]
            except ValueError:
                num_rng = self.rng_to_array(num)

            # Check for speed 100 command
            sp100 = re.search('speed 100_full', port_match[0])

            for i in num_rng:
                # Set parameters in Fast Ethernet ports dictionaries
                if i <= eth_rng:
                    if desc_match:
                        self.ethport[i-1]['desc'] = desc
                    if active_match:
                        self.ethport[i-1]['active'] = 1

                    # Set VLAN flags according to uvlans and tvland flags
                    if self.ethport[i-1]['uvlans'] != '' and self.ethport[i-1]['tvlans'] == '':

                        # If a port has just 2 untagged VLANs (PPPoE and HomeNet) it is "normal" port
                        # Also a port is "normal" if it has only PPPoE with enabled DHCP (mexed=1)
                        uvlans = self.ethport[i-1]['uvlans'].split()
                        uvlans.sort()
                        uvlans = ' '.join(uvlans)
                        # if self.ethport[i-1]['uvlans'] == np1 or self.ethport[i-1]['uvlans'] == np2:

                        if uvlans == normal_pattern or (uvlans == self.vppp_id and self.mixed == 1):
                            self.ethport[i-1]['normal'] = 1
                        if uvlans == self.vppp_id and self.noiptv == 1:
                            self.ethport[i-1]['normal'] = 1

                        # If there is only unmixed PPPoE VLAN on the port, the "PPPoE only" flag is set
                        if self.ethport[i-1]['uvlans'] == self.vppp_id and self.mixed == 0:
                            self.ethport[i-1]['ppponly'] = 1

                    if self.ethport[i-1]['uvlans'] != '' and self.ethport[i-1]['tvlans'] != '':
                        self.ethport[i - 1]['v_flag'] = 1

                    if self.ethport[i-1]['uvlans'] == '' and self.ethport[i-1]['tvlans'] != '':
                        self.ethport[i - 1]['v_flag'] = 2

                # Set parameters in Gigabit Ethernet ports dictionaries
                if i > eth_rng:
                    ig = i - eth_rng
                    if self.gigaport[ig-1]['desc'] == '@@@' and desc_match:
                        self.gigaport[ig-1]['desc'] = desc

                    # It is impossible to track the uplink port on D-Link, so set "uplink" on every port with description
                    if self.gigaport[ig-1]['desc'] != '@@@':
                        self.gigaport[ig-1]['uplink'] = 1

                    # Set speed 100
                    if sp100:
                        self.gigaport[ig-1]['sp100'] = 1

    # Function to translate range of numbers in D-Link config to a list of numbers (e.g. 3, 6-8 to [3, 6, 7, 8])
    def rng_to_array(self, rngline):
        rng_array = []
        for rng in re.finditer('\d{1,2}-\d{1,2}', rngline):
            for i in range(int(rng[0].split('-')[0]), int(rng[0].split('-')[1]) + 1):
                rng_array.append(i)
        for fix in re.finditer('(?<!\d-|-\d)\d{1,2}(?!(-|\d-))', rngline):
            rng_array.append(int(fix[0]))
        rng_array.sort()
        return rng_array


    def port_dictionaries(self, eth_rng, giga_rng):
        # Compose the list of dictionaries for Fast Ethernet ports
        for i in range(1, eth_rng+1):
            self.ethport.append({'desc': '###', 'active': 0, 'mcast': 0,
                                 'vlans': '', 'uvlans': '', 'tvlans': '', 'pvid': '', 'v_flag': 0,
                                 'normal': 0, 'ppponly': 0})

        # Compose the list of dictionaries for Gigabit Ethernet ports
        for i in range(1, giga_rng+1):
            self.gigaport.append({'desc': '@@@', 'active': 1, 'sp100': 0, 'uplink': 0})


# sourcefile = 'lenina85tc-sw-2.cfg'
# sc = ReplacementFromFile(sourcefile)
