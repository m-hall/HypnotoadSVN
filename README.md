# HypnotoadSVN
HypnotoadSVN is an extension for Sublime Text 2/3 that adds SVN features to the folder list and the command palatte.

This plugin started from [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN).

##Requirements
- Sublime Text 3
- Sublime Package Control
- SVN command line

### Optional
- TortoiseSVN

## Installation
1. Open Sublime text.
2. Open Command Palatte.
3. Type "install" and select "Package Control: Install Package".
4. Search for "HypnotoadSVN" and select it.
5. Optionally refer to "Settings" 

## Settings

### Update To Revision
Update to revision command can be modified to disable the history if you find it to be too slow.

#### Default
```Javascript
{
    "updateToRevisionHistory": true, // Set this to false to simply enter the desired revision number
    "updateToRevisionHistorySize": 20 // This changes the number of items in the revision history panel
}
```

### TortoiseSVN (Windows only)
Support for running commands through TortoiseSVN interface.
You MUST have TortoiseSVN installed to be able to use these options.

#### Default
```Javascript
{
    // Windows only
    "useTortoise": false, // allows commands that can only be used via TortoiseSVN
    "alwaysTortoise": false, // makes all commands run using TortoiseSVN only
    "tortoiseproc_path": "C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe", // path to TortoiseProc
}
```

## Resources
- [dexbol/sublime-TortoiseSVN](https://github.com/dexbol/sublime-TortoiseSVN)
- [TortoiseSVN](https://tortoisesvn.net/)
- [Sublime Text](http://www.sublimetext.com/)
- [Sublime Package Control](http://wbond.net/sublime_packages/package_control)
