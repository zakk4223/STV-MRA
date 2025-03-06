Generated MRA files for testing ST-V support in the MiSTer Saturn core.


How to use:

* Grab the latest release of this repo and extract it to /media/fat/_Arcade
* Copy the latest Saturn core RBF to /media/fat/_Arcade/cores/ST-V.rbf
* Copy stvbios.zip and all mame ST-V roms to /media/fat/games/mame. Merged sets are preferred, but split should also work.
* All of the ST-V MRAs should be in ST-V directory in your Arcade list.
* Launch any ST-V MRA.

The ST-V support in the core is VERY work in progress. Many games will not boot, and some will boot but not allow you to start a game. 

ST-V Bios notes.

These MRAs use the US bios by default. In the case where a game only supports JP bios, that one is used instead.
Games that support both US and JP bios have a second MRA in the "JP Bios" directory that loads the JP one instead of the US one.
