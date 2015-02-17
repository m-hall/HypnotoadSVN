Sublime-TSVN
============
sublimeTSVN is an extension to the [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN).
It is designed specifically to expose as many of the native TortoiseSVN commands to the Sublime Text as possible.
**It runs only on Windows and needs the TortoiseSVN and TortoiseSVN command line tools (TortoiseProc.exe).**

Usage
=====
Install it using [Sublime Package Control](http://wbond.net/sublime_packages/package_control).
If TortoiseSVN is not installed at `C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe`, specify the correct path
by setting property "tortoiseproc_path" in your TortoiseSVN.sublime-settings file. 

The default key bindings are 
- [alt+c] : commit current file.
- [alt+u] : update current file.
- [alt+r] : revert current file.

You can also call TortoiseSVN commands when right-clicking folders or files in the side bar.


Settings
========

If your TortoiseProc.exe path is not the default, please modify the path by selecting 
"Preferences->Package Settings->TortoiseSVN->Settings - User" in the menu.

The default setting is:

    {
        // Auto close update dialog when no errors, conflicts and merges
        "autoCloseUpdateDialog": false,
        "tortoiseproc_path": "C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe"
    }

Resources
=========
- [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN)
- [TortoiseSVN](http://tortoisesvn.net/)
- [Sublime Text](http://www.sublimetext.com/)
- [Sublime Package Control](http://wbond.net/sublime_packages/package_control)