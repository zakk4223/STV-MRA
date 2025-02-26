#!/usr/bin/python



import sys
import os
import re
import xml.etree.ElementTree as ET 
from pathlib import Path
from copy import deepcopy




mame_stvhash_file = sys.argv[1]
mame_xmlinfo_file = sys.argv[2]



hashtree = ET.parse(mame_stvhash_file)
hashroot = hashtree.getroot()


mamexmltree = ET.parse(mame_xmlinfo_file)
mameroot = mamexmltree.getroot()



def add_rom_part(romroot, crc, name, length=None, byteswap=False, skip_byte=False, do_inter=True, skip_shift=False):
    inter_elem = None
    if do_inter:
        inter_elem = ET.SubElement(romroot, "interleave", output="64")
    else:
        inter_elem = romroot
    byte_map = "21436587" if byteswap else "12345678"
    if skip_byte:
        if skip_shift: 
            byte_map = "10305070" if byteswap else "20406080"
        else:
            byte_map = "01030507" if byteswap else "02040608"

    ET.SubElement(inter_elem, "part", crc=crc, name=name, map=byte_map)
    return inter_elem

def add_rom(mraroot, romindex, zipfiles, address):
    rom_elem = ET.SubElement(mraroot, "rom", index=romindex, md5="", zip="|".join(zipfiles), address=address)
    return rom_elem

def add_zero_bytes(romroot, length):
    zelem = ET.SubElement(romroot, "part", repeat=hex(length))
    zelem.text = "00"
    return zelem

def add_buttons(mraroot, button_count=3):
    button_names = ["-", "-", "-", "-", "-", "-", "Start", "Coin", "Service", "Test"]
    button_defaults = ["Start", "Select", "L", "R"]
    button_def_base = ["A","B","X","Y","L","R"]


    button_def = button_def_base[0:button_count]
    button_def = button_def + ["Start", "Select"]
    if button_count < 5:
        button_def = button_def + ["R,L"]

    



    for btn_idx in range(min(6,button_count)):
        button_names[btn_idx] = f'Button {btn_idx+1}'

    ET.SubElement(mraroot, "buttons", names=",".join(button_names), default=",".join(button_def))


def add_stv_mode(mraroot, gamename):
    if gamename in ["decathlt", "decathlto"]:
        ET.SubElement(ET.SubElement(mraroot, "rom", index="0"), "part").text = "02"
    if gamename in ["rsgun"]:
        ET.SubElement(ET.SubElement(mraroot, "rom", index="0"), "part").text = "01"

def add_bios(mraroot, region="US"):
    bios_elem = add_rom(mraroot, romindex="2", zipfiles=["stvbios.zip"], address="0x30000000")
    if region == "JP":
        add_rom_part(bios_elem, crc="f688ae60", name="epr-23603.ic8", byteswap=True)
    else:
        add_rom_part(bios_elem, crc="d1be2adf", name="epr-17952a.ic8", byteswap=True)

def create_mra_root(setname):
    mraroot = ET.Element("misterromdescription")
    ET.SubElement(mraroot, "rbf").text = "ST-V"
    ET.SubElement(mraroot, "setname").text = setname

    return mraroot

def add_eeprom(mraroot, gamename, zip_files):
    global mameroot
    mame_nvs = mameroot.find(f"machine[@name='{gamename}']/rom[@region='eeprom']")
    eeprom_elem = add_rom(mraroot, romindex="1", zipfiles=zip_files, address="0x32000000")
    if mame_nvs is not None:
        add_rom_part(eeprom_elem, crc=mame_nvs.attrib['crc'], name=mame_nvs.attrib['name'])
    else:
        add_zero_bytes(eeprom_elem, 128)
    return eeprom_elem


def create_mra_tree(gameinfo, for_region="US"):
    global mameroot
    gamename = gameinfo.attrib['name']
    mraroot = create_mra_root(gameinfo.attrib['name'])
    mame_player1 = mameroot.find(f"machine[@name='{gamename}']/input/control")
    num_buttons = int(mame_player1.attrib["buttons"])
    add_buttons(mraroot, num_buttons)
    add_stv_mode(mraroot, gamename)
    zip_names = []
    zip_names.append(f'{gameinfo.attrib['name']}.zip')
    if 'cloneof' in gameinfo.attrib:
        zip_names.append(f'{gameinfo.attrib['cloneof']}.zip')
    add_eeprom(mraroot, gamename=gameinfo.attrib['name'], zip_files=zip_names)
    add_bios(mraroot, region=for_region)
    rom_root = add_rom(mraroot, romindex="3", zipfiles=zip_names, address="0x34000000")
    mra_filename = f'{descnode.text}.mra'
    mra_filename = mra_filename.replace('/', '-')

    last_loaded_rom_node = None
    current_offset = 0

    offset_map = {}

    for rominfo in gameinfo.iter('rom'):
        rom_offset = int(rominfo.attrib['offset'],0)
        if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'reload' and last_loaded_rom_node is not None:
            rominfo = last_loaded_rom_node
        if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'reload_plain' and last_loaded_rom_node is not None:
            rominfo = last_loaded_rom_node
            if 'loadflag' in rominfo.attrib:
                del rominfo.attrib['loadflag']
        #batman has sound roms in the stv.xml, without designating a sound cpu region. Just skip anything with 'snd' in it 
        if 'snd' not in rominfo.attrib['name'] and 'eeprom' not in rominfo.attrib['name']:
            offset_map[rom_offset] = deepcopy(rominfo)  
            last_loaded_rom_node = rominfo
    rom_inter_node = None
    for rom_offset,rominfo in sorted(offset_map.items()):
        rom_do_interleave = False
        rom_int_offset = rom_offset + 1
        if rom_int_offset in offset_map:
            rom_do_interleave = True
            #interleaved program roms

        rom_byte_skip = False
        if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'load16_byte': rom_byte_skip = True
        rom_offset = rom_offset & ~1
        if rom_offset > current_offset:
            add_zero_bytes(rom_root, length=rom_offset - current_offset)
            current_offset = current_offset + (rom_offset - current_offset)
        if 'name' in rominfo.attrib:
            rom_size = int(rominfo.attrib['size'],0)
            if rom_byte_skip and not rom_do_interleave and rom_inter_node is None: rom_size = rom_size * 2
            do_byteswap = True 
            if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'load16_word_swap':
                do_byteswap = False
                if rom_do_interleave:
                    rom_byte_skip = True
            if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'load16_byte':
                do_byteswap = False
            if current_offset < 0x200000:
                do_byteswap = not do_byteswap
            if rom_inter_node is not None or rom_do_interleave:
                do_byteswap = True
            if rom_inter_node is not None:
                add_rom_part(rom_inter_node, length=rom_size, crc=rominfo.attrib['crc'], name=rominfo.attrib['name'], byteswap=do_byteswap, skip_byte=True, skip_shift=True, do_inter=False)
                rom_inter_node = None 
            else:
                inter_node = add_rom_part(rom_root, length=rom_size, crc=rominfo.attrib['crc'], name=rominfo.attrib['name'], byteswap=do_byteswap, skip_byte=rom_byte_skip, skip_shift=False)
            if rom_do_interleave:
                rom_inter_node = inter_node
            last_loaded_rom_node = rominfo
            current_offset = current_offset + rom_size


    mratree = ET.ElementTree(mraroot)
    ET.indent(mratree, space="\t", level=0)
    return mratree

region_re = re.compile(r'.*\(([A-Z]+)\s+[0-9]')

for gameinfo in hashroot.iter('software'):
    descnode = gameinfo.find('description')
    region_match = region_re.match(descnode.text)
    region_codes = region_match.group(1)

    mra_filename = f'{descnode.text}.mra'
    mra_filename = mra_filename.replace('/', '-')
    mra_filename = mra_filename.replace(':', '-')
    
    if region_codes == 'J':
        create_mra_tree(gameinfo, for_region="JP").write(mra_filename)
    else:
        create_mra_tree(gameinfo, for_region="US").write(mra_filename)
        if 'J' in region_codes:
            if not os.path.isdir("_JP Bios"):
                os.makedirs("_JP Bios")
            create_mra_tree(gameinfo, for_region="JP").write(os.path.join("_JP Bios", mra_filename))




        






