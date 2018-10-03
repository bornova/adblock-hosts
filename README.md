# adBlock Hosts File Generator

The inspiration behind this project was the [StevenBlack/hosts repository](https://github.com/StevenBlack/hosts). Special thanks to everyone working hard to make it the awesome tool that it is.

Please note this program currently only works on Windows and macOS. It requires Python 3.x.

## How it works

When you run adBlock.py, it will ask if you want to create a new hosts file or the default hosts file. (You can alternatively use command line options to automate this process.  Please see the [usage section](#usage) below.) If you choose new adBlock (a), the script will download each hosts file listed in the 'sources' file and combine them. It will remove all duplicate lines, comments, and whitespace, then sort each line in alphabetical order. If you choose default (d) option, the script will generate the default hosts file for your OS.

In both cases, the generated hosts file will be saved as 'hosts' in the same folder as the script.

After the new hosts file is generated, you will be asked if you want to replace your existing hosts file with the new one (must run script as Administrator on Windows for this to work). If yes, you will be given the option to backup your existing hosts file before replacing it. To implement the new hosts file, exisiting hosts file will be replaced with newly generated hosts file and DNS cache will be cleared.

## Purpose of each file in this repo

### sources

This is where you would list links to hosts files you want to include in the final generated adBlock hosts file. You can use one url per line.  For demonstration purposes, I have included sources I personally use.  This source list is based on StevenBlack's Unified hosts = (adware + malware) hosts file recipe.  Please [follow this link](https://github.com/StevenBlack/hosts/blob/master/readme.md#sources-of-hosts-data-unified-in-this-variant) for more information about these sources.

### defaults

This is where the default hosts files are kept for both Windows and macOS.  The contents of these files will be inserted at the top of the hosts file depending on your operating system.  These files will also be used when you want to revert back to the original hosts file.  I suggest not modifying these.

### custom

You can add custom entries to this list.  These entries will be written to the adBlock host file as is.  Meaning no host IP (0.0.0.0) will be appended at the beginning of the line. For example, this would be a good place to put static hosts entries such as "ff02::3 ip6-allhosts".

### blacklist

These are domains you would like to block. You can list one domain per line. Note that if an item on this list matches an item in the custom list or the downloaded hosts files, then it will be ignored since it will already be included in the adBlock hosts file.

### whitelist

This is where you would list all domains which you would like to exclude from the adBlock hosts file.  Again, one domain per line. However, this list can include wildcards by using the asterisk '*' operator.  For example:

**`*xyzdomain.com`** Exclude all urls ending with 'xyzdomain.com' such as example.xyzdomain.com

**`xyz*`** Exclude all urls starting with 'xyz' such as xyzdomain.com or xyz.example.com

**`*xyzdomain*`** Exclude all urls containing the phrase 'xyzdomain' such as foo.xyzdomain.com or example.123xyzdomainfoo.com

Tip: In sources, blacklist and whitelist files, you can omit a line by including a '#' at the beginning.

## Usage

### Using Python 3

    python adBlock.py

or depending on the python setup:

    python3 adBlock.py

### Command line options

`-h`, or `--help`: display help.

Modes (use only one):

`-a` or `--adblock`: Generate new adBlock hosts file

`-d` or `--default`: Generate the default hosts file

## Limitations

This script will replace your existing hosts file automatically only if you have administrator privileges.  For Windows systems, you will need to run the command line console as Administrator. For macOS, the script will ask for SUDO password within the terminal before attempting to implement the new hosts file.

If you don't have administrator privileges, the script will still generate a new hosts file and it will save it to the same directory as the script. From there, you can manually try to move it in place. Hosts file is located here:

**macOS**: /etc/hosts folder.

**Windows**: %SystemRoot%\system32\drivers\etc\hosts folder.

## Backup option

Before replacing the existing hosts file, you will be given the option to backup the existing hosts file.  The backup will be saved in a new folder called 'backups'.
