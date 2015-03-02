# Settings
This document explains the available settings for the HypnotoadSVN plugin

## Debug
Adds extra output to the Sublime console. By default debug is turned off.
This should only be used for development or if there are unexpected behaviours.

```Javascript
"debug": false,
```

## Command base files
Sets the files to use for global commands.
Set this value to "project" to use the root folders/files of the project.
Set this value to "current" to use the active view.

```Javascript
"commandBaseFiles": "project",
```

## Native SVN
Native SVN commands are available on all systems capable of using this plugin.
The only requirements is the the SVN command line program is installed.

### Disable
Allows the user to disable all native SVN commands.

```Javascript
"disable": false,
```

### Output
Specifies the way SVN commands send their output.
The default option is "panel".

```Javascript
"outputTo": "panel",
```

#### Options
- *panel*: opens an output panel at the bottom of the window (default)
- *tab*: opens a new tab for output
- *dialog*: opens an alert dialog for the results of each command

### Update to Revision
Update to revision can optionally show a list of recent revisions for the user to select.

```Javascript
"updateToRevisionHistory": true,
"updateToRevisionHistorySize": 20,
```

### Logs
You can change the maximum number of revisions to show when gettings logs.

```Javascript
"logHistorySize": 20,
```


## Tortoise SVN
As TortoiseSVN is only available for Windows, this section only applies to Windows users.

### Disable
Allows the user to disable all TortoiseSVN commands

```Javascript
"disable": false,
```

### Tortoise Proc
Specifies the location of the TortoiseProc.exe executable file.
This is required to be valid for TortoiseSVN commands to run properly.
You should only change this if TortoiseSVN has been installed to a location other than the default.
```Javascript
"tortoiseproc_path": "C:\\Program Files\\TortoiseSVN\\bin\\TortoiseProc.exe",
```

## Prefers
For each available command, specifies whether to use Native SVN or TortoiseSVN

### Default
The default preference for commands is "nativeSVN". This can be changed to tortoiseSVN

```Javascript
"default": "nativeSVN",
```

### Commands
Each command can individually prefer native or tortoise.
By default, all commands use the default, except for diff and blame, which prefer tortoiseSVN.

#### Supported commands
- update
- commit
- add
- delete
- rename
- revert
- log
- status
- cleanup
- lock
- unlock
- diff
- blame

#### Unsupported commands
- resovle
- switch
- branch
- checkout
