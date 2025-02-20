#!/usr/bin/python



import sys
import os
import re
import xml.etree.ElementTree as ET 
from pathlib import Path




mame_stvhash_file = sys.argv[1]
mame_xmlinfo_file = sys.argv[2]



hashtree = ET.parse(mame_stvhash_file)
hashroot = hashtree.getroot()


mamexmltree = ET.parse(mame_xmlinfo_file)
mameroot = mamexmltree.getroot()



def add_rom_part(romroot, crc, name, length=None, byteswap=False, skip_byte=False):
    inter_elem = ET.SubElement(romroot, "interleave", output="64")
    byte_map = "21436587" if byteswap else "12345678"
    if skip_byte:
        byte_map = "01030507" if byteswap else "02040608"
    ET.SubElement(inter_elem, "part", crc=crc, name=name, map=byte_map)

def add_rom(mraroot, romindex, zipfiles, address):
    rom_elem = ET.SubElement(mraroot, "rom", index=romindex, md5="", zip="|".join(zipfiles), address=address)
    return rom_elem

def add_zero_bytes(romroot, length):
    zelem = ET.SubElement(romroot, "part", repeat=hex(length))
    zelem.text = "00"
    return zelem

def add_bios(mraroot, region="US"):
    bios_elem = add_rom(mraroot, romindex="2", zipfiles=["stvbios.zip"], address="0x30000000")
    if region == "JP":
        add_rom_part(bios_elem, crc="f688ae60", name="epr-23603.ic8", byteswap=True)
    else:
        add_rom_part(bios_elem, crc="d1be2adf", name="epr-17952a.ic8", byteswap=True)

def create_mra_root():
    mraroot = ET.Element("misterromdescription")
    ET.SubElement(mraroot, "rbf").text = "Saturn"
    ET.SubElement(mraroot, "setname").text = "saturnstv"
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
    mraroot = create_mra_root()
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
    for rominfo in gameinfo.iter('rom'):
        #HEY YOU IN THE FUTURE:
        #_almost_ every game that has load16_byte flags also has an offset like x000001
        #this means it writes every other byte into the region, but starts at byte 1
        #00 xx before byte/word etc swap.
        #a few games are more complicated than this, since you can use this to interleave two roms
        #via offsets of 0x000000 and then 0x000001
        #it might be worth detecting this at some point but for now just set a flag and then 2x the size
        #since we'll be writing 00xx
        #notable game that might need hand fixing: batman
        if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'reload' and last_loaded_rom_node is not None:
            rominfo = last_loaded_rom_node
            print(descnode.text)
        rom_byte_skip = False
        if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'load16_byte': rom_byte_skip = True
        rom_offset = int(rominfo.attrib['offset'],0)
        rom_offset = rom_offset & ~1
        if rom_offset > current_offset:
            add_zero_bytes(rom_root, length=rom_offset - current_offset)
            current_offset = current_offset + (rom_offset - current_offset)
        if 'name' in rominfo.attrib:
            rom_size = int(rominfo.attrib['size'],0)
            if rom_byte_skip: rom_size = rom_size * 2
            do_byteswap = True 
            if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'load16_word_swap':
                do_byteswap = False
            if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'load16_byte':
                do_byteswap = False
            if current_offset < 0x200000:
                do_byteswap = not do_byteswap
            add_rom_part(rom_root, length=rom_size, crc=rominfo.attrib['crc'], name=rominfo.attrib['name'], byteswap=do_byteswap, skip_byte=rom_byte_skip)
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
    
    if region_codes == 'J':
        create_mra_tree(gameinfo, for_region="JP").write(mra_filename)
    else:
        create_mra_tree(gameinfo, for_region="US").write(mra_filename)
        if 'J' in region_codes:
            if not os.path.isdir("_JP Bios"):
                os.makedirs("_JP Bios")
            create_mra_tree(gameinfo, for_region="JP").write(os.path.join("_JP Bios", mra_filename))




        






