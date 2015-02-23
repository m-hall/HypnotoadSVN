HypnotoadSVN
=============
HypnotoadSVN is an extension for Sublime Text 2/3 that adds SVN features to the folder list and the command palatte.

This plugin started from [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN).

Requirements
------------
- Sublime Text 2/3
- Sublime Package Control

Installation
------------
1. Open Sublime text.
2. Open Command Palatte.
3. Type "install" and select "Package Control: Install Package".
4. Search for "HypnotoadSVN" and select it.
5. Optionally refer to "Settings" 

Settings
--------

### Update To Revision
Update to revision command can be modified to disable the history if you find it to be too slow.

Default
```
{
    "updateToRevisionHistory": true, // Set this to false to simply enter the desired revision number
    "updateToRevisionHistorySize": 20 // This changes the number of items in the revision history panel
}
```

Resources
---------
- [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN)
- [Sublime Text](http://www.sublimetext.com/)
- [Sublime Package Control](http://wbond.net/sublime_packages/package_control)