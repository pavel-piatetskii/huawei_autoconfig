from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox
import re
import sourceparsers as sp

# Declaration of lists and dictionaries (to be reworked)

param_to_replace = {}
vid_entries = []
vname_entries = []
eth_vlans_flags = []
vlans_unt_list = []
vlans_tag_list = []
eth_desc_list = []
eth_pvid_list = []
eth_vlans_list = []
mcast_chbox_var = []
mcast_chbox_list = []
active_chbox_list = []
ppponly_chbox_list = []
active_chbox_var = []
ppponly_chbox_var = []
mcast_commands = []
ethvlan_set = []
giga_desc_list = []
g_active_chbox_list = []
g_uplink_chbox_var = []
uplink_chbox_list = []
g_100_chbox_var = []
g_100_chbox_list = []
sp100mask = []
affected_port = [0, 0, 0]
base_column = 0
vw_rnum = 5
sorname = ''
messages = []
sc = None


# ========================================= INITIAL PARAMETERS REQUEST WINDOW =========================================

# ----------------------------------------------------------------- Functions for initial parameters request window  --


# Set specific switch parameters

# all_parameters - ['template file name',
#                   number of FastEthernet ports,
#                   number of FastEthernet ports in each column for two-column layout,
#                   number of GigabitEthernet ports,
#                   number of GigabitEthernet ports in each column for two-column layout]
# speed_100_possibility - mask which is used to allow the "SPEED 100" option
# speed_100_commands - those are specific for 3352/2352 switches, as they don't have combo-ports
def set_sw_param(sw_type):
    all_parameters = []
    speed_100_possibility = []
    speed_100_commands = '\n port media type fiber\n  undo negotiation auto\n  speed 100\n combo-port fiber'
    mcast_commands = ["'iptv_all_def'", "'block'"]
    ethvlan_set = "param_to_replace['[v_iptv]'] + ' '" + \
                  "+ param_to_replace['[v_pppoe]'] + ' ' + param_to_replace['[v_hnet]']"
    if sw_type == 'Huawei S2320-12':
        all_parameters = ['2320-12_vrpcfg.cfg', 8, 8, 4, 4]
        speed_100_possibility = [1, 1, 0, 0]
    elif sw_type == 'Huawei S2320-28':
        all_parameters = ['2320-28_vrpcfg.cfg', 20, 10, 8, 4]
        speed_100_possibility = [0, 0, 0, 0, 1, 1, 0, 0]
    elif sw_type == 'Huawei S2320-52':
        all_parameters = ['2320-52_vrpcfg.cfg', 44, 22, 8, 4]
        speed_100_possibility = [0, 0, 0, 0, 0, 0, 0, 0]
    elif sw_type == 'Huawei S2350-28':
        all_parameters = ['2350_vrpcfg.cfg', 24, 12, 4, 2]
        speed_100_possibility = [0, 0, 1, 1]
    elif sw_type == 'Huawei S3328':
        all_parameters = ['3328_vrpcfg.cfg', 24, 12, 4, 2]
        speed_100_possibility = [0, 0, 1, 1]
        mcast_commands = ["'\\n attach multicast-profile iptv_all_def interface Ethernet0/0/' + str(i)", "''"]
        ethvlan_set = "param_to_replace['[v_pppoe]'] + ' ' + param_to_replace['[v_hnet]']"
    elif sw_type == 'Huawei S2352/S3352':
        all_parameters = ['2352_3352_vrpcfg.cfg', 48, 24, 4, 2]
        speed_100_possibility = [0, 0, 1, 1]
        speed_100_commands = '\n undo negotiation auto\n speed 100'
        mcast_commands = ["'\\n attach multicast-profile iptv_all_def interface Ethernet0/0/' + str(i)", "''"]
        ethvlan_set = "param_to_replace['[v_pppoe]'] + ' ' + param_to_replace['[v_hnet]']"

    return all_parameters, speed_100_possibility, speed_100_commands, mcast_commands, ethvlan_set

# Validate IP-address 
def relay_ip_vald(relay):
    octets = relay.split('.')
    for i in range(0, 4):
        try:
            if int(octets[i]) not in range(0, 256):
                messagebox.showinfo("Error", "You have entered an incorrect DHCP-relay IP-address")
                return True
        except:
            messagebox.showinfo("Error", "You have entered an incorrect DHCP-relay IP-address ")
            return True


def ipmask_valid(ip_addr, mask_prefix):
    octets = ip_addr.split('.')

    # Validate subnet prefix
    try:
        if int(mask_prefix) not in range(0, 33):
            messagebox.showinfo("Error", "You have entered an incorrect subnet prefix (%s)" % mask_prefix)
            return True
    except:
        messagebox.showinfo("Error", "You have entered an incorrect subnet prefix")
        return True

    # Validate managemant IP-address
    for i in range(0, 4):

        try:
            if int(octets[i]) not in range(0, 256):
                messagebox.showinfo("Error", "You have entered an incorrect management IP-address")
                return True
        except:
            messagebox.showinfo("Error", "You have entered an incorrect management IP-address")
            return True
        octets[i] = int(octets[i])
    return octets


# Calculation of the rest network parameters
def ip_calc(ip_addr, mask_prefix):

    octets = ipmask_valid(ip_addr, mask_prefix)
    if octets == True:
        raise Exception()
    dms = []
    wcard = []
    bcast = []

    for i in range(0, 4):

        dms.append(((2 ** (32 - int(mask_prefix)) - 1) ^ 0xffffffff) >> (8 * (3 - i)) & 255)
        octets[i] = int(octets[i]) & dms[i]
        wcard.append(dms[i] ^ 255)
        bcast.append(octets[i] + wcard[i])

        dms[i] = str(dms[i])
        wcard[i] = str(wcard[i])
        octets[i] = str(octets[i])
        bcast[i] = str(bcast[i])

    subnet_addr = '.'.join(octets)
    wildcard_mask = '.'.join(wcard)
    direct_mask = '.'.join(dms)
    broadcast = '.'.join(bcast)
    octets[3] = str(int(octets[3]) + 1)
    gateway = '.'.join(octets)
    net_param_returned = {'[m_subnet]': subnet_addr, '[direct_mask]': direct_mask,
                          '[m_mask_b]': wildcard_mask, '[def_rt]': gateway, '[broadcast]': broadcast}

    return net_param_returned

# Validate VLANs set on the Initial screen
def start_vlan_valid(vl_tv, vl_pp, vl_hn):
    start_vls = [vl_tv, vl_pp, vl_hn]
    mbox = ['IPTV', 'PPPoE', 'Homenet']
    for i in range(0, len(start_vls)):
        try:
            if int(start_vls[i]) not in range(0, 4095):
                messagebox.showinfo("Error", "Incorrect VLAN ID " + mbox[i]) 
                return True
        except ValueError:
            messagebox.showinfo("Error", 'Content of the field "vlan ' + mbox[i] + '" is not a number')
            return True

# Validate switch name
def sysname_valid(name):
    if name == '':
        messagebox.showinfo("Error", 'Enter the switch name!')
        return True

# Limit mask field size by 2 characters
def limitSizeMask(*args):
    value = mask_pref.get()
    if len(value) > 2:
        mask_pref.set(value[:2])

# Validate HomeNet VLAN ID and name
def okbut_get_hnet_if_mixed():
    v_hnet = get_hnet_id.get()
    desc_hnet = get_hnet_name.get()
    if v_hnet != '' and desc_hnet != '':
        param_to_replace['[v_hnet]'] = v_hnet
        param_to_replace['[desc_hnet]'] = desc_hnet
        get_hnet.quit()
    else:
        messagebox.showinfo('Attention!', 'Enter required parameters')

# Create pop-up window to ask for the new HomeNet VLAN parameters 
# if the switch which is being replaced used mixed schema
def get_hnet_if_mixed():
    global get_hnet_id, get_hnet_name, get_hnet
    get_hnet = Toplevel()
    get_hnet.focus_force()
    Label(get_hnet, text='Attention! \nExisting switch has \nmixed vlan PPPoE + Homenet.\n'
                        'Enter ID and name of HomeNet VLAN for the new switch').grid(row=1, column=1, columnspan=3)
    Label(get_hnet, text='  ').grid(row=1, column=0)  # border L-UP
    Label(get_hnet, text='ID').grid(row=2, column=1)
    get_hnet_id = Entry(get_hnet, width=4, bd=2)
    get_hnet_id.grid(row=3, column=1)
    Label(get_hnet, text='  ').grid(row=2, column=2)     # border
    Label(get_hnet, text='Name').grid(row=2, column=3)
    get_hnet_name = Entry(get_hnet, width=30, bd=2)
    get_hnet_name.grid(row=3, column=3)
    okbut = Button(get_hnet, text='OK', command=okbut_get_hnet_if_mixed)
    okbut.grid(row=4, column=3)
    Label(get_hnet, text='  ').grid(row=5, column=4)     # border R-DOWN
    get_hnet.mainloop()

# Handler for the "No IPTV and HomeNet" checkbox
def noiptv_clicked(event):
    if noiptv_var.get() == 0:
        relay_ip_ent.delete(0, END)
        relay_ip_ent.config(state=DISABLED)
        viptv_entry.config(state=DISABLED)
        desc_vhnet.delete(0, END)
        vhnet_entry.config(state=DISABLED)
        desc_vhnet.config(state=DISABLED)
    else:
        relay_ip_ent.config(state=NORMAL)
        relay_ip_ent.insert(0, '172.18.')
        viptv_entry.config(state=NORMAL)
        vhnet_entry.config(state=NORMAL)
        desc_vhnet.config(state=NORMAL)
        desc_vhnet.insert(0, 'LOCAL_HOMENET.')

# Read initial parameters from the first screen and transfer IP-address to the calculator function
def get_start():
    global patternname, eth_ports_range, or22or24, giga_ports_range, gi_or2or4, \
        sp100mask, sp100com, mcast_commands, ethvlan_set, sorname, sc, noiptv

    sw_parameters, sp100mask, sp100com, mcast_commands, ethvlan_set = set_sw_param(sw_current_type.get())
    patternname, eth_portnum, or22or24, giga_portnum, gi_or2or4 = sw_parameters

    param_to_replace['[locat]'] = ''
    # If a replacement was chosen read data from an existing configuration file
    if sorname != '':
        sc = sp.ReplacementFromFile(sorname)

        param_to_replace['[sn]'] = sc.sysname
        param_to_replace['[ipmgmt]'] = sc.ipmgmt
        param_to_replace['[m_mask]'] = sc.prefix
        param_to_replace['[relay_ip]'] = sc.iprelay
        param_to_replace.update(ip_calc(param_to_replace.get('[ipmgmt]'), param_to_replace.get('[m_mask]')))
        param_to_replace['[def_rt]'] = sc.gateway
        param_to_replace['[locat]'] = sc.location

        param_to_replace['[v_pppoe]'] = sc.vppp_id
        param_to_replace['[desc_pppoe]'] = sc.vppp_name

        noiptv = sc.noiptv
        if noiptv == 0:
            param_to_replace['[v_iptv]'] = sc.viptv_id
            if sc.mixed == 1:
                get_hnet_if_mixed()
            elif sc.mixed == 0:
                try:
                    param_to_replace['[v_hnet]'] = sc.vhnet_id
                    param_to_replace['[desc_hnet]'] = sc.vhnet_name
                except AttributeError:
                    noiptv = 1
        else:
            ethvlan_set = "param_to_replace['[v_pppoe]']"

    # If it is not a replacement read parameters from the first screen fields
    else:
        param_to_replace['[sn]'] = sn_entry.get()
        if sysname_valid(param_to_replace['[sn]']):
            return True

        param_to_replace['[ipmgmt]'] = ip_ent.get()
        param_to_replace['[m_mask]'] = mask_entry.get()
        param_to_replace.update(ip_calc(param_to_replace.get('[ipmgmt]'), param_to_replace.get('[m_mask]')))
        param_to_replace['[v_pppoe]'] = vpppoe_entry.get()
        param_to_replace['[desc_pppoe]'] = desc_pppoe.get()

        noiptv = noiptv_var.get()
        if noiptv == 0:
            param_to_replace['[relay_ip]'] = relay_ip_ent.get()
            if relay_ip_vald(param_to_replace['[relay_ip]']):
                return True
            param_to_replace['[v_iptv]'] = viptv_entry.get()
            param_to_replace['[v_hnet]'] = vhnet_entry.get()
            param_to_replace['[desc_hnet]'] = desc_vhnet.get()
            if start_vlan_valid(param_to_replace['[v_iptv]'],
                                param_to_replace['[v_pppoe]'],
                                param_to_replace['[v_hnet]']):
                return True
        else:
            ethvlan_set = "param_to_replace['[v_pppoe]']"

    eth_ports_range = range(1, eth_portnum+1)
    giga_ports_range = range(1, giga_portnum + 1)
    start_parameters.quit()
    start_parameters.destroy()

# If replacement is chosen, read and show switch name 
# from the existing configuration file and disable input fields on the 1st screen
def replacement_file():
    global sorname
    rep_source = fd.askopenfile()
    rep_label.config(text=(re.search('[\D\d]+?(?=\.)', (re.split('[\D\d]+/', rep_source.name))[1]))[0])
    sorname = rep_source.name
    sn_entry.config(state=DISABLED)
    mask_entry.config(state=DISABLED)
    ip_ent.delete(0, END)
    ip_ent.config(state=DISABLED)
    relay_ip_ent.delete(0, END)
    relay_ip_ent.config(state=DISABLED)
    viptv_entry.config(state=DISABLED)
    vpppoe_entry.config(state=DISABLED)
    desc_pppoe.delete(0, END)
    desc_vhnet.delete(0, END)
    desc_pppoe.config(state=DISABLED)
    vhnet_entry.config(state=DISABLED)
    desc_vhnet.config(state=DISABLED)
    noiptv_chbox.config(state=DISABLED)


# Exit button handler for the 1st screen
def start_on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        sys.exit()


# ------------------------------------------------------------------ Draw the initial parameters request window (The 1st screen) --
start_parameters = Tk()
start_parameters.geometry("+300+300")
start_parameters.title('Huawei Autoconfig - Initial parameters')
start_parameters.protocol("WM_DELETE_WINDOW", start_on_closing)

Label(start_parameters, text=' ').grid(row=0, column=0)     # border

header_label = Label(start_parameters, text='Enter required parameters').grid(row=0, column=1, columnspan=2)

sn_label = Label(start_parameters, text='System name  ').grid(row=1, column=1, sticky=E)
sn_entry = Entry(start_parameters, width=23, borderwidth=2)
sn_entry.grid(row=1, column=2, columnspan=3, sticky=W)

ipmask_label = Label(start_parameters, text='IP-address and prefix  ').grid(row=2, column=1, sticky=E)
ip_ent = Entry(start_parameters, width=18, borderwidth=2)
ip_ent.grid(row=2, column=2, sticky=W)
ip_ent.insert(0, '172.31.')

mask_pref = StringVar()
mask_pref.trace('w', limitSizeMask)
mask_label = Label(start_parameters, text='/').grid(row=2, column=3)
mask_entry = Entry(start_parameters, width=2, borderwidth=2, textvariable=mask_pref)
mask_entry.grid(row=2, column=4, sticky=W)

relay_ip_label = Label(start_parameters, text='DHCP-relay IP-address  ').grid(row=3, column=1, sticky=E)
relay_ip_ent = Entry(start_parameters, width=18, borderwidth=2)
relay_ip_ent.grid(row=3, column=2, sticky=W)
relay_ip_ent.insert(0, '172.18.')

viptv_label = Label(start_parameters, text='IPTV vlan ID  ').grid(row=4, column=1, sticky=E)
viptv_entry = Entry(start_parameters, width=4, borderwidth=2)
viptv_entry.grid(row=4, column=2, sticky=W)

vpppoe_label = Label(start_parameters, text='PPPoE vlan ID and name   ').grid(row=5, column=1, sticky=E)
vpppoe_entry = Entry(start_parameters, width=4, borderwidth=2)
vpppoe_entry.grid(row=5, column=2, sticky=W)
desc_pppoe = Entry(start_parameters, width=47, borderwidth=2)
desc_pppoe.grid(row=5, column=2, columnspan=4, sticky=E)
desc_pppoe.insert(0, 'LOCAL_PPPoE.')

vhnet_label = Label(start_parameters, text='Homenet vlan ID and name  ').grid(row=6, column=1, sticky=E)
vhnet_entry = Entry(start_parameters, width=4, borderwidth=2)
vhnet_entry.grid(row=6, column=2, sticky=W)
desc_vhnet = Entry(start_parameters, width=47, borderwidth=2)
desc_vhnet.grid(row=6, column=2, columnspan=4, sticky=E)
desc_vhnet.insert(0, 'LOCAL_HOMENET.')

# Dropdown menu to choose a switch model
sw_types_list = ['Huawei S2320-12', 'Huawei S2320-28',
                 'Huawei S2320-52', 'Huawei S2350-28',
                 'Huawei S3328', 'Huawei S2352/S3352']

sw_current_type = StringVar()
sw_current_type.set(sw_types_list[0])

model_frame = Frame(start_parameters)
model_frame.grid(row=0, column=5, rowspan=5, sticky=NE)
Label(model_frame, text=' ').grid(row=0, column=0)
sw_type_label = Label(model_frame, text='Choose switch model')
sw_type_label.grid(row=0, column=1)
sw_type_choose = OptionMenu(model_frame, sw_current_type, *sw_types_list)
sw_type_choose.grid(row=1, column=1, sticky=E)
sw_type_choose.config(width=23)

#sborder_label1 = Label(start_parameters, text=' ').grid(row=0, column=2)
Label(start_parameters, text='   ').grid(row=0, column=6)

rep_label = Label(model_frame, text='------------------')
rep_label.grid(row=2, column=1)

replace_button = Button(model_frame, text='Replacement', width=10, command=replacement_file)
replace_button.grid(row=3, column=1, sticky=W)

start_button = Button(model_frame, text='Next >>>', width=10, command=get_start)
start_button.grid(row=3, column=1, sticky=E)
sborder_label3 = Label(start_parameters, text=' ').grid(row=8)
noiptv = 0
noiptv_var = IntVar()
noiptv_chbox = Checkbutton(start_parameters, variable=noiptv_var, onvalue=1, offvalue=0,
                            text='No IPTV and HomeNet')
noiptv_chbox.grid(row=7, column=2, columnspan=4, sticky=W)
noiptv_chbox.bind('<Button-1>', noiptv_clicked)

start_parameters.mainloop()


# ================================ MAIN APPLICATION WINDOW - PORTS, VLANS, IP-PARAMETERS ================================

# --------------------------------------------------------------------------------------- Functions of the main window --

# VLANS field dropdown menu functions

# Untagged
def vd_menu_untag():
    global affected_port
    index, row, column = affected_port
    eth_vlans_flags[index] = 0

    try:
        vlans_unt_list[index].grid_forget()
        vlans_tag_list[index].grid_forget()
        param_to_replace['[eth00' + str(index+1) + 'vlans]'] = ''
    except: pass

    eth_vlans_list[index].grid(row=row, column=column)
    eth_vlans_list[index].config(fg='black', bg='white')

# Mixed Untagged + Tagged
def vd_menu_unt_tag():
    global affected_port
    index, row, column = affected_port
    eth_vlans_flags[index] = 1
    eth_vlans_list[index].grid_forget()
    try:
        del (param_to_replace['[eth00' + str(index+1) + 'vlans]'])
    except: pass

    eth_vlans_unt = Entry(eth_ports_frame, width=7, borderwidth=2)
    eth_vlans_unt.grid(row=row, column=column, sticky=W)
    eth_vlans_unt.bind('<Button-3>', vlans_drop_menu)
    vlans_unt_list[index] = eth_vlans_unt

    eth_vlans_tag = Entry(eth_ports_frame, width=7, borderwidth=2)
    eth_vlans_tag.grid(row=row, column=column, sticky=E)
    eth_vlans_tag.config(fg='white', bg='gray55')
    eth_vlans_tag.bind('<Button-3>', vlans_drop_menu)
    vlans_tag_list[index] = eth_vlans_tag

# Tagged
def vd_menu_tagged():
    global affected_port
    index, row, column = affected_port
    eth_vlans_flags[affected_port[0]] = 2
    try:
        vlans_unt_list[index].grid_forget()
        vlans_tag_list[index].grid_forget()
        eth_vlans_list[index].grid(row=row, column=column)
        del (param_to_replace['[eth00' + str(index+1) + 'vlans]'])
    except:
        eth_vlans_list[index].config(fg='white', bg='gray55')

# Bind Functions from above to the dropmenu
def vlans_drop_menu(event):
    global affected_port
    try:
        index = eth_vlans_list.index(event.widget)
    except:
        try:
            index = vlans_unt_list.index(event.widget)
        except:
            index = vlans_tag_list.index(event.widget)
    flag = eth_vlans_flags[index]
    placement = event.widget.grid_info()
    affected_port = [index, placement['row'], placement['column']]

    drop_menu = Menu(root, tearoff=0)
    if flag == 1 or flag == 2:
        drop_menu.add_command(label='Untagged', command=vd_menu_untag)
    if flag == 0 or flag == 2:
        drop_menu.add_command(label='Untagged & Tagged', command=vd_menu_unt_tag)
    if flag == 0 or flag == 1:
        drop_menu.add_command(label='Tagged', command=vd_menu_tagged)
    drop_menu.post(event.x_root, event.y_root)


# Activate all ports
def active_all(event):
    for i in eth_ports_range:
        active_chbox_list[i-1].select()


# Deactivate all ports
def inactive_all(event):
    for i in eth_ports_range:
        active_chbox_list[i-1].deselect()


# enable PPPoE only for all ports
def ppponly_all(event):
    for i in eth_ports_range:
        ppponly_chbox_list[i-1].select()


# disable PPPoE only for all ports
def no_ppponly_all(event):
    for i in eth_ports_range:
        ppponly_chbox_list[i-1].deselect()


# Create headers in the Fast Ethernet ports section
def root_headers():
    int_name_label = Label(eth_ports_frame, text='Interface name').grid(row=1, column=base_column)
    active_box_label = Label(eth_ports_frame, text='Active')
    active_box_label.grid(row=1, column=base_column+1)
    active_box_label.bind("<Button-1>", active_all)
    active_box_label.bind("<Button-3>", inactive_all)
    mcast_box_label = Label(eth_ports_frame, text='IPTV').grid(row=1, column=base_column+2)
    int_desc_label = Label(eth_ports_frame, text='Description').grid(row=1, column=base_column+3)
    border1_label = Label(eth_ports_frame, text='   ').grid(row=1, column=base_column+4)
    int_pvid_label = Label(eth_ports_frame, text='PVID').grid(row=1, column=base_column+5)
    border2_label = Label(eth_ports_frame, text='   ').grid(row=1, column=base_column+6)
    vlans_desc_label = Label(eth_ports_frame, text='VLANS').grid(row=1, column=base_column+7)
    ppponly_label = Label(eth_ports_frame, text='PPPoE    \nonly')
    ppponly_label.grid(row=1, column=base_column+8)
    ppponly_label.bind("<Button-1>", ppponly_all)
    ppponly_label.bind("<Button-3>", no_ppponly_all)
    border3_label = Label(eth_ports_frame, text='   ').grid(row=1, column=base_column+9)


# Add new VLAN
def add_vlan():

    global vw_rnum
    vw_rnum = vw_rnum + 1
    curr_entry = Entry(vlans_frame, width=4, borderwidth=2)
    curr_entry.grid(row=vw_rnum, column=1)
    vid_entries.append(curr_entry)
    curr_entry = Entry(vlans_frame, width=35, borderwidth=2)
    curr_entry.grid(row=vw_rnum, column=2)
    vname_entries.append(curr_entry)
    rem_button.config(state=NORMAL)


# Delete a VLAN
def rem_vlan():

    global vw_rnum
    vid_entries[-1].destroy()
    vname_entries[-1].destroy()
    vid_entries.pop()
    vname_entries.pop()
    vw_rnum = vw_rnum - 1
    if len(vid_entries) == 0:
        rem_button.config(state=DISABLED)


# Save application settings
def save_settings():
    global template_path_folder, result_path_folder, settings_window
    template_path_folder = template_path_entry.get().strip()
    result_path_folder = result_path_entry.get().strip()
    conf_file = open('prefs.cfg', 'w')
    conf_file.write(template_path_folder + '\n' + result_path_folder)
    conf_file.close()
    settings_window.destroy()


# Set path to the templates folder
def template_path():
    global template_path_entry
    new_template_path = fd.askdirectory()
    settings_window.focus_force()
    template_path_entry.delete(0, END)
    template_path_entry.insert(0, new_template_path)


# Set path for the results folder
def result_path():
    global result_path_entry
    new_result_path = fd.askdirectory()
    settings_window.focus_force()
    result_path_entry.delete(0, END)
    result_path_entry.insert(0, new_result_path)


# Open settings window
def settings():
    global template_path_entry, result_path_entry, template_path_folder, result_path_folder, settings_window
    settings_window = Toplevel(root)
    settings_window.title('Settings')
    settings_window.focus_force()
    try:
        conf_file = open('prefs.cfg', 'r').readlines()
        template_path_folder = conf_file[0]
        result_path_folder = conf_file[1]
    except FileNotFoundError:
        conf_file = open('prefs.cfg', 'w+')
        conf_file.write('config_templates/\nresult_configs/')
        conf_file.close()
        template_path_folder = 'config_templates/'
        result_path_folder = 'result_configs/'

    border_l = Label(settings_window, text=' ').grid(row=0, column=0)
    label = Label(settings_window, text='Templates folder:')
    label.grid(row=0, column=1, sticky=W)
    template_path_entry = Entry(settings_window, width=75, bd=2)
    template_path_entry.grid(row=1, column=1)
    template_path_entry.insert(0, template_path_folder)

    label = Label(settings_window, text='Results folder:')
    label.grid(row=2, column=1, sticky=W)
    result_path_entry = Entry(settings_window, width=75, bd=2)
    result_path_entry.grid(row=3, column=1)
    result_path_entry.insert(0, result_path_folder)

    border_l = Label(settings_window, text=' ').grid(row=3, column=2)

    template_path_button = Button(settings_window, text='Choose folder', command=template_path)
    template_path_button.grid(row=1, column=3)
    result_path_button = Button(settings_window, text='Choose folder', command=result_path)
    result_path_button.grid(row=3, column=3)

    border_l = Label(settings_window, text='   ').grid(row=4, column=4)

    bt_frame = Frame(settings_window)
    bt_frame.grid(row=4, column=1)
    Label(bt_frame, text='\t\t\t').grid(column=0)
    save_button = Button(bt_frame, text='Save', command=save_settings)
    save_button.grid(row=0, column=1)
    Label(bt_frame, text='   ').grid(column=2)
    cancel_button = Button(bt_frame, text='Cancel', command=lambda: settings_window.destroy())
    cancel_button.grid(row=0, column=3)

    settings_window.mainloop()


# Validation of IP-parameters
def validation():
    # Network parameters. First, calculate of parameters from IP and mask, then compare with entered ones  --------------
    par2compare = ip_calc(param_to_replace['[ipmgmt]'], param_to_replace['[m_mask]'])

    if par2compare['[m_subnet]'] != param_to_replace['[m_subnet]']:
        messagebox.showinfo("Error", "Management subnet does not match address and mask")
        return True

    if par2compare['[direct_mask]'] != param_to_replace['[direct_mask]']:
        messagebox.showinfo("Error", "Subnet mask does not match prefix")
        return True

    if par2compare['[m_mask_b]'] != param_to_replace['[m_mask_b]']:
        messagebox.showinfo("Error", "Wildcard mask does not match prefix")
        return True

    if noiptv == 0:
        if relay_ip_vald(relay_ip_ent.get()):
            return True

    if param_to_replace['[ipmgmt]'] == param_to_replace['[m_subnet]']:
        messagebox.showinfo("Error", "management IP-address is the same as subnet address")
        return True

    if param_to_replace['[ipmgmt]'] == param_to_replace['[def_rt]']:
        messagebox.showinfo("Error", "management IP-address is the same as gateway address")
        return True

    if param_to_replace['[ipmgmt]'] == par2compare['[broadcast]']:
        messagebox.showinfo("Error", "management IP-address is the same as network broadcast address")
        return True

    # Calulate once again to validate the gateway address
    par2compare = ip_calc(param_to_replace['[def_rt]'], param_to_replace['[m_mask]'])

    if par2compare['[m_subnet]'] != param_to_replace['[m_subnet]']:
        messagebox.showinfo("Error", "Gateway IP-address does not match management subnet")
        return True

    if param_to_replace['[def_rt]'] == par2compare['[broadcast]']:
        messagebox.showinfo("Error", "Gateway IP-address is the same as network broadcast address")
        return True

    # Check VLANs on ports, etc. ---------------------------------------------------------------------------------
    for i in eth_ports_range:
        if eth_vlans_flags[i-1] == 0 or eth_vlans_flags[i-1] == 2:
            vlan_string = eth_vlans_list[i-1].get()
        else:
            vlan_string = vlans_unt_list[i-1].get() + " " + vlans_tag_list[i-1].get()

        vlan_set = vlan_string.split(' ')

        all_vlans = []
        for vlans in range(0, len(vid_entries)):
            all_vlans.append(vid_entries[vlans].get())

        if noiptv == 0:
            all_vlans = all_vlans + [param_to_replace['[v_iptv]'],
                                     param_to_replace['[v_pppoe]'],
                                     param_to_replace['[v_hnet]']]
        else:
            all_vlans = all_vlans + [param_to_replace['[v_pppoe]']]

        # print(all_vlans)
        for vlans in range(0, len(vlan_set)):
            try:
                if int(vlan_set[vlans]) not in range(0, 4095):
                    messagebox.showinfo("Error", "Incorrect ID of one or more "
                                        "VLANs in VLANs field for port Ethernet0/0/" + str(i))
                    return True
                if vlan_set[vlans] not in all_vlans:
                    messagebox.showinfo("Error", "VLAN " + vlan_set[vlans] +
                                        ", allowed for port Ethernet0/0/" + str(i) + " is not created")
                    return True
            except ValueError:
                messagebox.showinfo("Error", "Content of the VLANs field for port Ethernet0/0/" + str(i) +
                                    " is not a number or a group of numbers")
                return True
        try:
            if int(param_to_replace['[eth00' + str(i) + 'pvid]']) not in range(0, 4095):
                messagebox.showinfo("Error", "Incorrect VLAN ID in PVID field for port Ethernet0/0/" + str(i))
                return True
        except ValueError:
            messagebox.showinfo("Error", "Content of PVID field for port Ethernet0/0/" + str(i) + " is not a number")
            return True

        if param_to_replace['[eth00' + str(i) + 'pvid]'] not in vlan_set:
            messagebox.showinfo("Error", "PVID of Ethernet0/0/" + str(i) +
                                " does not match any of VLANs allowed on this port")
            return True


# Main function to compose switch configuration
def create_config():

    additional_vlans = ''

    for k in eth_ports_range:

        param_to_replace['[eth00' + str(k) + 'desc]'] = eth_desc_list[k-1].get()
        param_to_replace['[eth00' + str(k) + 'pvid]'] = eth_pvid_list[k-1].get()

        if eth_vlans_flags[k-1] == 1:
            # del(param_to_replace['[eth00' + str(k) + 'vlans]'])
            param_to_replace['port hybrid untagged vlan [eth00' + str(k) + 'vlans]'] = \
                'port hybrid untagged vlan ' + vlans_unt_list[k-1].get() + \
                '\n port hybrid tagged vlan ' + vlans_tag_list[k-1].get()

        if eth_vlans_flags[k-1] == 2:
            # del (param_to_replace['[eth00' + str(k) + 'vlans]'])
            param_to_replace['port hybrid untagged vlan ' + '[eth00' + str(k) + 'vlans]'] = \
                'port hybrid tagged vlan ' + eth_vlans_list[k-1].get()
        else:
            param_to_replace['[eth00' + str(k) + 'vlans]'] = eth_vlans_list[k-1].get()

        param_to_replace['[eth00' + str(k) + 'active]'] = active_chbox_var[k-1].get()

        if noiptv == 0:
            param_to_replace['[eth00' + str(k) + 'mcast]'] = mcast_chbox_var[k-1].get()

        param_to_replace['[eth00' + str(k) + 'ppponly]'] = ppponly_chbox_var[k-1].get()

    for k in giga_ports_range:

        param_to_replace['[gi00' + str(k) + 'desc]'] = giga_desc_list[k-1].get()
        param_to_replace['[gi00' + str(k) + 'active]'] = g_active_chbox_list[k-1].get()
        param_to_replace['[gi00' + str(k) + 'uplink]'] = g_uplink_chbox_var[k-1].get()

        if sp100mask[k-1] == 1:
            param_to_replace['[gi00' + str(k) + 'sp100]'] = g_100_chbox_var[k-1].get()
        else:
            param_to_replace['[gi00' + str(k) + 'sp100]'] = ''

    param_to_replace['[sn]'] = sn_entry.get()
    if sysname_valid(param_to_replace['[sn]']):
        return True

    param_to_replace['[ipmgmt]'] = ip_ent.get()
    param_to_replace['[m_mask]'] = mask_entry.get()
    param_to_replace['[m_subnet]'] = snet_entry.get()
    param_to_replace['[def_rt]'] = gateway_entry.get()
    param_to_replace['[direct_mask]'] = direct_entry.get()
    param_to_replace['[m_mask_b]'] = wildcard_entry.get()
    if noiptv == 0:
        param_to_replace['[relay_ip]'] = relay_ip_ent.get()
    param_to_replace['[locat]'] = location_entry.get()

    # Validation of all input data
    if validation():
        return True

    for vlans in range(0, len(vid_entries)):

        additional_vlans = additional_vlans + '\nvlan ' + vid_entries[vlans].get() \
                           + '\n description ' + vname_entries[vlans].get()

    param_to_replace['[additional_vlans]'] = additional_vlans

    # Read application preferences (settings)
    conf_file = open('prefs.cfg', 'r').readlines()
    template_path_folder = conf_file[0].strip()
    result_path_folder = conf_file[1].strip()

    # Read template file to a variable
    initial_conf = open(template_path_folder + '/' + patternname)
    conf_to_modify = initial_conf.read()

    # Modify template if the "No IPTV" checkbox is set
    if noiptv == 1:
        to_delete_match = re.search('\nvlan \[v_hnet\].+(?= \[additional_vlans\])', conf_to_modify, flags=re.DOTALL)
        param_to_replace[to_delete_match[0]] = ''
        to_delete_match = re.search('interface Vlanif\[v_hnet\].+?(?=interface Ethernet0/0/1)',
                                    conf_to_modify, flags=re.DOTALL)
        param_to_replace[to_delete_match[0]] = ''
        param_to_replace['\n l2-multicast-bind vlan [v_hnet] mvlan [v_iptv]'] = ''
        param_to_replace['\n multicast-source-deny vlan [v_hnet]'] = ''


    # Mass-replace parts of template with parameter entered by user
    trp = replace_all(conf_to_modify, param_to_replace)

    # Open the dialog window to offer path and filename (the switch name by default) to save the result configuration
    file_name = fd.asksaveasfile(initialfile=param_to_replace.get('[sn]'),
                                 initialdir=result_path_folder,
                                 defaultextension='cfg',
                                 filetypes=(('Configuration file', '*.cfg'), ('All files', '*.*')))
    # conf_modified = open(param_to_replace.get('[sn]') + '.cfg', 'w+')

    # Create new file, write resulting config to it and close
    conf_modified = open(file_name.name, 'w+')
    conf_modified.write(trp)
    conf_modified.close()
    # print(param_to_replace)

    # TO BE DONE!!!!
    # ADD POP-UP TO INFORM A USER THAT THE FILE WAS SAVED!!!

    root.quit()
    root.destroy()


# Replace pre-made replacement marks in a template with replace_dictionary contents
def replace_all(config_text, replace_dictionary):
    for i, k in replace_dictionary.items():
        config_text = config_text.replace(i, k)
    return config_text


# Quit handler for main window
def root_on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        sys.exit()


# Functions to transfer data read from a source-configuration
# For Fast Ethernet ports
def checkif_ethreplace(x):
    global affected_port
    x -= 1

    if sc.ethport[x]['active'] == 1:
        active_chbox_list[x].select()
    if sc.ethport[x]['mcast'] == 1:
        mcast_chbox_list[x].select()
    eth_desc_list[x].delete(0, END)
    eth_desc_list[x].insert(0, sc.ethport[x]['desc'])
    if sc.ethport[x]['normal'] == 0:
        if sc.ethport[x]['pvid']:
            eth_pvid_list[x].delete(0, END)
            eth_pvid_list[x].insert(0, sc.ethport[x]['pvid'])
        elif not sc.ethport[x]['pvid'] and sc.ethport[x]['uvlans']:
            eth_pvid_list[x].delete(0, END)
            eth_pvid_list[x].insert(0, sc.ethport[x]['uvlans'])

    placement = eth_vlans_list[x].grid_info()
    affected_port = [x, placement['row'], placement['column']]
    if sc.ethport[x]['v_flag'] == 0 and sc.ethport[x]['normal'] == 0 and sc.ethport[x]['uvlans'] != '':
            eth_vlans_list[x].delete(0, END)
            eth_vlans_list[x].insert(0, sc.ethport[x]['uvlans'])
    elif sc.ethport[x]['v_flag'] == 1:
        vd_menu_unt_tag()
        vlans_unt_list[x].insert(0, sc.ethport[x]['uvlans'])
        vlans_tag_list[x].insert(0, sc.ethport[x]['tvlans'])
    elif sc.ethport[x]['v_flag'] == 2:
        vd_menu_tagged()
        eth_vlans_list[x].delete(0, END)
        eth_vlans_list[x].insert(0, sc.ethport[x]['tvlans'])

    if sc.ethport[x]['ppponly'] == 1:
        ppponly_chbox_list[x].select()
    else:
        ppponly_chbox_list[x].deselect()

# For Gigabit Ethernet ports
def checkif_gigareplace(x):
    x -= 1
    if sc.gigaport[x]['active'] == 0:
        g_active_chbox_list[x].deselect()
    giga_desc_list[x].delete(0, END)
    giga_desc_list[x].insert(0, sc.gigaport[x]['desc'])
    if sc.gigaport[x]['uplink'] == 1:
        uplink_chbox_list[x].select()

    if sc.gigaport[x]['sp100'] == 1 and sp100mask[x] == 1:
        g_100_chbox_list[x].select
    elif sc.gigaport[x]['sp100'] == 1 and sp100mask[x] == 0:
        # messagebox.showinfo("Attention!", "Port GE0/0/" + str(x+1) + " does not support SPEED 100")
        giga_desc_list[x].insert(0, '(SPEED 100) ')
        messages.append("Port GE0/0/" + str(x+1) + " does not support SPEED 100")

# For VLANs
def vlans_from_source():
    n = 0
    for vid, vname in sc.other_vlans.items():
        add_vlan()
        vid_entries[n].insert(0, vid)
        vname_entries[n].insert(0, vname)
        n += 1


# -------------------------------------------------------------------------------------- Draw main application window --
root = Tk()
#if not normal:
    #sys.exit()
    #root.destroy()
root.geometry("+100+200")
root.title('Huawei autoconfig - Switch setup')
root.protocol("WM_DELETE_WINDOW", root_on_closing)
root.focus_force()
eth_ports_frame = Frame(root)
eth_ports_frame.grid(row=0, sticky=N)
vlans_frame = Frame(root)
vlans_frame.grid(row=0, rowspan=2, column=1, sticky=N)
net_parameters_frame = Frame(root)
net_parameters_frame.grid(row=0, column=2, sticky=N)

# ------------------------------------------------------------------------------------ Setting up Fast Ethernet ports --
root_headers()

for i in eth_ports_range:

    # If a number of ports is more than a certain threshold (half for all switches besides 2320-12),
    # change 1-column to 2-column layout
    if i == or22or24+1:
        base_column = 9        # base_column is a starting point to choose a column in grid
        root_headers()

    if i > or22or24:
        rnum = i-or22or24
    else:
        rnum = i

    # Ports labels
    eth_label = Label(eth_ports_frame, text='Ethe0/0/' + str(i)).grid(row=rnum+1, column=base_column)

    # checkboxes for a port activation
    active_chbox_var.append(StringVar())
    active_chbox = Checkbutton(eth_ports_frame, variable=active_chbox_var[i-1], onvalue='',
                               offvalue='\n shutdown')
    active_chbox.deselect()
    active_chbox.grid(row=rnum+1, column=base_column+1)
    active_chbox_list.append(active_chbox)

    # checkboxes for multicast activation on each port
    mcast_chbox_var.append(StringVar())
    mcast_chbox = Checkbutton(eth_ports_frame, variable=mcast_chbox_var[i-1],
                              onvalue=eval(mcast_commands[0]), offvalue=eval(mcast_commands[1]))
    mcast_chbox.deselect()
    mcast_chbox.grid(row=rnum+1, column=base_column+2)
    mcast_chbox_list.append(mcast_chbox)

    # Fields for port description
    curr_entry = Entry(eth_ports_frame, width=30, borderwidth=2)
    curr_entry.grid(row=rnum+1, column=base_column+3)
    param_to_replace['[eth00' + str(i) + 'desc]'] = '###'
    eth_desc_list.append(curr_entry)
    curr_entry.insert(0, param_to_replace['[eth00' + str(i) + 'desc]'])

    # PVID fields
    curr_entry = Entry(eth_ports_frame, width=4, borderwidth=2)
    curr_entry.grid(row=rnum+1, column=base_column+5)
    if noiptv == 0:
        param_to_replace['[eth00' + str(i) + 'pvid]'] = param_to_replace['[v_hnet]']
    else:
        param_to_replace['[eth00' + str(i) + 'pvid]'] = param_to_replace['[v_pppoe]']
    eth_pvid_list.append(curr_entry)
    curr_entry.insert(0, param_to_replace['[eth00' + str(i) + 'pvid]'])

    # VLANs fields
    curr_entry = Entry(eth_ports_frame, width=15, borderwidth=2)
    curr_entry.grid(row=rnum+1, column=base_column+7)
    param_to_replace['[eth00' + str(i) + 'vlans]'] = eval(ethvlan_set)
    curr_entry.bind('<Button-3>', vlans_drop_menu)
    eth_vlans_list.append(curr_entry)
    curr_entry.insert(0, param_to_replace['[eth00' + str(i) + 'vlans]'])
    eth_vlans_flags.append(0)
    vlans_unt_list.append(0)
    vlans_tag_list.append(0)

    # checkboxes for "PPPoE only"
    ppponly_chbox_var.append(StringVar())
    ppponly_chbox = Checkbutton(eth_ports_frame, variable=ppponly_chbox_var[i-1],
                                onvalue='\n traffic-pppoe any any', offvalue='')
    if noiptv == 0:
        ppponly_chbox.deselect()
    else:
        ppponly_chbox.select()
    ppponly_chbox.grid(row=rnum+1, column=base_column+8)
    ppponly_chbox_list.append(ppponly_chbox)

    if sc:
        if i <= len(sc.ethport):
            checkif_ethreplace(i)

eth_frame_low_border = Label(eth_ports_frame, text=' ').grid(row=rnum+2, column=base_column)

# --------------------------------------------------------------------------------- Setting up Gigabit Ethernet ports --
base_column = 0
rnum = rnum + 2
active_label = Label(eth_ports_frame, text='Active')
active_label.grid(row=rnum, column=base_column + 1)
uplink_label = Label(eth_ports_frame, text='Uplink')
uplink_label.grid(row=rnum, column=base_column+5)

for i in giga_ports_range:

    # If a number of ports is more than 24 (22 for 2320 series),
    # change 1-column to 2-column layout
    if i == gi_or2or4+1:
        base_column = 9        # base_column is a starting point to choose a column in grid
        rnum = rnum - gi_or2or4
        active_label = Label(eth_ports_frame, text='Active')
        active_label.grid(row=rnum, column=base_column + 1)
        uplink_label = Label(eth_ports_frame, text='Uplink')
        uplink_label.grid(row=rnum, column=base_column + 5)

    if i > gi_or2or4:
        rnum = rnum + 1
    else:
        rnum = rnum + 1

    # Port labels
    giga_label = Label(eth_ports_frame, text='Gi0/0/' + str(i)).grid(row=rnum, column=base_column)

    # checkboxes for port activation
    g_active_chbox_list.append(StringVar())
    active_chbox = Checkbutton(eth_ports_frame, variable=g_active_chbox_list[i-1], onvalue='',
                               offvalue='\n shutdown')
    active_chbox.select()
    active_chbox.grid(row=rnum, column=base_column+1)

    # Fields for port description
    curr_entry = Entry(eth_ports_frame, width=30, borderwidth=2)
    curr_entry.grid(row=rnum, column=base_column+3)
    param_to_replace['[gi00' + str(i) + 'desc]'] = '@@@'
    giga_desc_list.append(curr_entry)
    curr_entry.insert(0, param_to_replace['[gi00' + str(i) + 'desc]'])

    # checkboxes for "uplink"
    g_uplink_chbox_var.append(StringVar())
    uplink_chbox = Checkbutton(eth_ports_frame, variable=g_uplink_chbox_var[i-1],
                               onvalue='pppoe uplink-port trusted\n trust dscp\n dhcp snooping trusted',
                               offvalue='pppoe intermediate-agent information policy keep\n dhcp snooping disable')
    uplink_chbox.deselect()
    uplink_chbox_list.append(uplink_chbox)
    uplink_chbox.grid(row=rnum, column=base_column+5)
    

    # checkboxes for "SPEED 100"
    if sp100mask[i-1] == 1:
        g_100_chbox_var.append(StringVar())
        sp100_chbox = Checkbutton(eth_ports_frame, variable=g_100_chbox_var[i-1],
                                  onvalue=sp100com, offvalue='', text='SPEED 100')
        sp100_chbox.deselect()
        g_100_chbox_list.append(sp100_chbox)
        sp100_chbox.grid(row=rnum, column=base_column+7)
    else:
        g_100_chbox_var.append(0)
        g_100_chbox_list.append(0)
    if sc:
        if i <= len(sc.gigaport):
            checkif_gigareplace(i)

# If switch parameters were not parsed fro existing config, set the last Gigabit Ethernet port as an uplink
if not sc:
    uplink_chbox.select()

glow_border_label = Label(eth_ports_frame, text=' ').grid(row=rnum+2, column=base_column+4)

# ----------------------------------------------------------------------------------------------------- VLANs section --
vw_border1_label = Label(vlans_frame, text="List of VLANs").grid(row=0, column=2, sticky=W)
add_button = Button(vlans_frame, text='Add', command=add_vlan)
add_button.grid(row=1, column=1)
rem_button = Button(vlans_frame, text='Delete', state=DISABLED, command=rem_vlan)
rem_button.grid(row=1, column=2)

id_label = Label(vlans_frame, text='VLAN ID').grid(row=2, column=1)
name_label = Label(vlans_frame, text='VLAN Name', width=30).grid(row=2, column=2)

vw_pppoe_id_label = Label(vlans_frame, text=param_to_replace['[v_pppoe]']).grid(row=4, column=1)
vw_pppoe_name_label = Label(vlans_frame, text=param_to_replace['[desc_pppoe]'], width=35).grid(row=4, column=2)
if noiptv == 0:
    vw_iptv_id_label = Label(vlans_frame, text=param_to_replace['[v_iptv]']).grid(row=3, column=1)
    vw_iptv_name_label = Label(vlans_frame, text='IPTV').grid(row=3, column=2)
    vw_hnet_id_label = Label(vlans_frame, text=param_to_replace['[v_hnet]']).grid(row=5, column=1)
    vw_hnet_name_label = Label(vlans_frame, text=param_to_replace['[desc_hnet]']).grid(row=5, column=2)
vw_border4_label = Label(vlans_frame, text=' ').grid(row=1, column=3)

if sc:
    vlans_from_source()

# ----------------------------------------------------------------------------------------- Network Parameters Section --
sn_label = Label(net_parameters_frame, text='System name').grid(row=2, sticky=E)
sn_entry = Entry(net_parameters_frame, width=23, borderwidth=2)
sn_entry.grid(row=2, sticky=W, columnspan=3, column=1)
sn_entry.insert(0, param_to_replace['[sn]'])

ipmask_label = Label(net_parameters_frame, text='IP-address and prefix ').grid(row=3, sticky=E)
ip_ent = Entry(net_parameters_frame, width=18, borderwidth=2)
ip_ent.grid(row=3, sticky=W, column=1)
ip_ent.insert(0, param_to_replace['[ipmgmt]'])

mask_pref = StringVar()
mask_pref.trace('w', limitSizeMask)
mask_label = Label(net_parameters_frame, text='/').grid(row=3, column=2)
mask_entry = Entry(net_parameters_frame, width=2, borderwidth=2, textvariable=mask_pref)
mask_entry.grid(row=3, column=3, sticky=W)
mask_entry.insert(0, param_to_replace['[m_mask]'])

snet_label = Label(net_parameters_frame, text='Management subnet ').grid(row=4, sticky=E)
snet_entry = Entry(net_parameters_frame, width=18, borderwidth=2)
snet_entry.grid(row=4, column=1, sticky=W)
snet_entry.insert(0, param_to_replace['[m_subnet]'])

gateway_label = Label(net_parameters_frame, text='Gateway ').grid(row=5, sticky=E)
gateway_entry = Entry(net_parameters_frame, width=18, borderwidth=2)
gateway_entry.grid(row=5, column=1, sticky=W)
gateway_entry.insert(0, param_to_replace['[def_rt]'])

direct_label = Label(net_parameters_frame, text='Netmask ').grid(row=6, sticky=E)
direct_entry = Entry(net_parameters_frame, width=18, borderwidth=2)
direct_entry.grid(row=6, column=1, sticky=W)
direct_entry.insert(0, param_to_replace['[direct_mask]'])

wildcard_label = Label(net_parameters_frame, text='Wildcard mask ').grid(row=7, sticky=E)
wildcard_entry = Entry(net_parameters_frame, width=18, borderwidth=2)
wildcard_entry.grid(row=7, column=1, sticky=W)
wildcard_entry.insert(0, param_to_replace['[m_mask_b]'])

if noiptv == 0:
    relay_ip_label = Label(net_parameters_frame, text='DHCP-relay IP-address ').grid(row=8, sticky=E)
    relay_ip_ent = Entry(net_parameters_frame, width=18, borderwidth=2)
    relay_ip_ent.grid(row=8, column=1)
    relay_ip_ent.insert(0, param_to_replace['[relay_ip]'])

location_label = Label(net_parameters_frame, text='SNMP Location ').grid(row=9, sticky=E)
location_entry = Entry(net_parameters_frame, width=18, borderwidth=2)
location_entry.grid(row=9, column=1)
location_entry.insert(0, param_to_replace['[locat]'])

border4_label = Label(net_parameters_frame, text='   ').grid(row=0, column=4)
border5_label = Label(net_parameters_frame, text='   ').grid(row=10)

# ------------------------------------------------------------------------ Settings and Create Config buttons Section --
settings_button = Button(net_parameters_frame, text='Settings', width=13, command=settings)
settings_button.grid(row=11, column=1)

Label(net_parameters_frame, text='------------------').grid(row=12, column=1)

get_button = Button(net_parameters_frame, text='Create config', width=13, command=create_config)
get_button.grid(row=13, column=1)

for message in messages:
    messagebox.showinfo("Attention!", message)

root.mainloop()
