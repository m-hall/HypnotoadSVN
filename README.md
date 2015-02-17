HypnotoadSVN
=============
HypnotoadSVN is an extension for Sublime Text 2/3 that adds TortoiseSVN features to the folder list and the command palatte.

This plugin started from [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN).
**It runs only on Windows and needs the TortoiseSVN and TortoiseSVN command line tools (TortoiseProc.exe).**

Requirements
------------
- Sublime Text 2/3
- Sublime Package Control
- TortoiseSVN

Installation
------------
1. Open Sublime text.
2. Open Command Palatte.
3. Type "install" and select "Package Control: Install Package".
4. Search for "HypnotoadSVN" and select it.
5. Optionally refer to "Settings" 

Settings
--------

### tortoiseproc_path
If you have installed TortoiseSVN to a directory other than the default, set this value to the location of "TortoiseProc.exe".

Default
```JSON
{
    "tortoiseproc_path": "C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe"
}
```

### autoCloseUpdateDialog
Closes the Update dialog after it is complete provided there are no errors, conflicts or merges.

Default
```JSON
{
    "autoCloseUpdateDialog": false
}
```

### autoCloseCommitDialog
Closes the commit dialog after it is complete provided that there are no errors.

Default
```JSON
{
    "autoCloseCommitDialog": true
}
```

Key Bindings
------------
The default key bindings are 
- [alt+c] : commit current file.
- [alt+u] : update current file.
- [alt+r] : revert current file.

Resources
---------
- [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN)
- [TortoiseSVN](http://tortoisesvn.net/)
- [Sublime Text](http://www.sublimetext.com/)
- [Sublime Package Control](http://wbond.net/sublime_packages/package_control)