# Side Bar
The Side Bar menu is the context menu that appears when you right-click or context-click on a file or folder in the Side bar. This plugin provides the ability for the user to modify the Side Bar menu for their own perferences. For this reason, the side bar menu is automatically created into the user directory on install.

## Resetting
At any time you can reset the side bar to the current default with the "HypnotoadSVN: Reset Side Bar" command from the command Palette. This is the equivalent of copying the default file overtop of the user file. As such, any modifications to this file will be lost.

This command is intended to assist in the plugin upgrade process, however if the file becomes corrupted and you can not repair it, then this will also allow you to fix it.

## Modifying
You can modify your side bar context by changing the "User/HypnotoadSVN/Side Bar.sublime-menu" file. You can open the file via the "HypnotoadSVN: Side Bar - User" command.
It is recommended that you simply rearrange commands in this file to either be at the top level or in the "SVN" sub-menu.