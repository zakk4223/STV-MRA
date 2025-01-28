#!/usr/bin/python



import sys
import os
import re
import xml.etree.ElementTree as ET 
from pathlib import Path




mame_stvhash_file = sys.argv[1]


hashtree = ET.parse(mame_stvhash_file)
hashroot = hashtree.getroot()


def add_rom_part(romroot, crc, name, byteswap=False):
    inter_elem = ET.SubElement(romroot, "interleave", output="64")
    ET.SubElement(inter_elem, "part", crc=crc, name=name, map="21436587" if byteswap else "12345678")

def add_rom(mraroot, romindex, zipfiles, address):
    rom_elem = ET.SubElement(mraroot, "rom", index=romindex, md5="", zip="|".join(zipfiles), address=address)
    return rom_elem

def add_zero_bytes(romroot, length):
    ET.SubElement(romroot, "part", repeat=hex(length)).text = "00"

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



def create_mra_tree(gameinfo, for_region="US"):
    mraroot = create_mra_root()
    add_bios(mraroot, region=for_region)
    zip_names = []
    zip_names.append(f'{gameinfo.attrib['name']}.zip')
    if 'cloneof' in gameinfo.attrib:
        zip_names.append(f'{gameinfo.attrib['cloneof']}.zip')

    rom_root = add_rom(mraroot, romindex="3", zipfiles=zip_names, address="0x34000000")
    mra_filename = f'{descnode.text}.mra'
    mra_filename = mra_filename.replace('/', '-')

    last_loaded_rom_node = None
    current_offset = 0
    for rominfo in gameinfo.iter('rom'):
        rom_offset = int(rominfo.attrib['offset'],0)
        if rom_offset == 1: rom_offset = 0
        if rom_offset > current_offset:
            add_zero_bytes(rom_root, length=rom_offset - current_offset)
            current_offset = current_offset + (rom_offset - current_offset)
        if 'loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'reload' and last_loaded_rom_node is not None:
            rominfo = last_loaded_rom_node
            print(descnode.text)
        if 'name' in rominfo.attrib:
            rom_size = int(rominfo.attrib['size'],0)
            add_rom_part(rom_root, crc=rominfo.attrib['crc'], name=rominfo.attrib['name'], byteswap='loadflag' in rominfo.attrib and rominfo.attrib['loadflag'] == 'load16_word_swap')
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




        






