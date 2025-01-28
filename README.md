Generated MRA files for testing ST-V support in the MiSTer Saturn core.


How to use:

* Grab the latest release of this repo and extract it to /media/fat/_Arcade
* Copy the latest Saturn core RBF to /media/fat/_Arcade/cores/Saturn.rbf
* Copy all mame ST-V roms to /media/fat/games/mame. You will also need stvbios.zip. Merged sets are preferred, but split should also work.
* All of the ST-V MRAs should be in ST-V directory in your Arcade list.
* Launch any ST-V game. Open the OSD and change the 'Cart type' to STV. Save your settings.
* Relaunch any ST-V MRA and it will now launch.

The ST-V support in the core is VERY work in progress. Many games will not boot, and some will boot but not allow you to start a game. 

ST-V Bios notes.

These MRAs use the US bios by default. In the case where a game only supports JP bios, that one is used instead.
Games that support both US and JP bios have a second MRA in the "JP Bios" directory that loads the JP one instead of the US one.


