# Settings
This document explains the available settings for the HypnotoadSVN plugin

## Debug
Adds extra output to the Sublime console. By default debug is turned off.
This should only be used for development or if there are unexpected behaviors.

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

### Paths
You can also specify any path or list of paths.
In general, it is better to only use the path option if you are setting it in your project settings.

```Javascript
"commandBaseFiles": "~/Projects/my_svn_project"
```
or
```Javascript
"commandBaseFiles": [
    "~/Projects/my_svn_project",
    "~/Projects/my_other_project"
]
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
Modifies the way SVN commands send their output.
The default "outputTo" option is "panel".
OutputScrollTo allows you to change how the auto-scroll behavior works.
You can also optionally include the raw command in the output.
Conflicts will also be highlighted, and the style can be changed for the gutter and highlights.

```Javascript
"outputTo": "panel",
"outputScrollTo": "command",
"outputRawCommand": false,
"outputGutter": "circle",
"outputHighlight": "outline"
```

#### "outputScrollTo" Options
- *command*: When a command is started, scroll the command to the top
- *bottom*: Every time a line is added, make it visible

#### "outputTo" Options
- *panel*: opens an output panel at the bottom of the window (default)
- *tab*: opens a new tab for output
- *dialog*: opens an alert dialog for the results of each command

#### "outputGutter" Options
- *dot*: a small dot
- *circle*: a circle that fills the width of the gutter
- *bookmark*: a small arrow indicating the line
- *none*: no gutter marker

#### "outputHighlight" Options
- *fill*: fills the background of the text
- *outline*: outlines the selected area
- *solid*: adds a solid underline to the selected area
- *squiggly*: adds a squiggly underline to the selected area
- *stippled*: adds a stippled underline to the selected area
- *none*: no highlight

### Commit
Modifies the commit workflow.
A minimum message size can be required.
Also the verification dialog can be disabled.

```Javascript
"commitMessageSize": 
"commitConfirm": true,
```

### Update to Revision
Update to revision can optionally show a list of recent revisions for the user to select.

```Javascript
"updateToRevisionHistory": true,
"updateToRevisionHistorySize": 20,
```

### Logs
You can change the maximum number of revisions to show when getting logs.

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
- resolve
- switch
- branch
- merge
- checkout

## Project Settings
All settings can also be added to the project files. While inside the project, these settings will overwrite the global settings on a case by case basis, so you won't have to copy all settings into each new project.
In the project file, group all settings in the "HypnotoadSVN" object.

### Branches
Branches can only be added to project settings. They are currently not accessible via global settings.
Branches will also automatically be added to you project settings as they are used.
When you are not in a project, branches must be manually entered each 

```Javascript
"branches": [
    'http://source.url/svn/trunk',
    'http://source.url/svn/branches/my_branch'
]
```
