#!/usr/bin/env python
import io
import os
import sys
import time
import ctypes
import argparse
from shutil import copyfile
from subprocess import call, check_output
from urllib.parse import urlparse
from urllib.request import urlopen

if not sys.version_info >= (3, 0):
    sys.exit("Python 2 is not supported. Exiting...")

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--default", help="Generate the default hosts file.",
                    action="store_true")
parser.add_argument("-u", "--unified", help="Generate new unified hosts file.",
                    action="store_true")
args = parser.parse_args()

DT = time.strftime("%b %d, %Y %H:%M:%S %Z")
DTB = time.strftime("%b %d, %Y %H.%M.%S")

PATH = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(PATH, "sources")
BLACKLIST_FILE = os.path.join(PATH, "blacklist")
WHITELIST_FILE = os.path.join(PATH, "whitelist")
NEW_HOSTS_FILE = os.path.join(PATH, "hosts")
BACKUP_DIR = os.path.join(PATH + "/backups/")
BACKUP_FILE = os.path.join(PATH + "/backups", DTB + ".bak")

MAC = sys.platform == "darwin"
WIN = sys.platform == "win32"
if MAC:
    HOSTS_FILE = "/etc/hosts"
    DEFAULT_HOSTS = os.path.join(PATH + "/defaults/macHosts")
elif WIN:
    HOSTS_FILE = os.environ["WINDIR"] + "/System32/Drivers/etc/hosts"
    DEFAULT_HOSTS = os.path.join(PATH + "/defaults/winHosts")
    ADMIN = ctypes.windll.shell32.IsUserAnAdmin()
    if not ADMIN:
        print("Note: A new hosts file will be generated but not "
              "implemented. Please run this program as Administrator "
              "to implement the new hosts file automatically.\n")
else:
    sys.exit("Your operating system is not supported at this time. Exiting...")

with open(DEFAULT_HOSTS, "r") as f:
    HEADER = f.read().strip()

IP_LIST = ["127.0.0.1", "0.0.0.0"]
PREFIX = "0.0.0.0"


class startProgram():
    def __init__(self, mode=None):
        if len(sys.argv) > 2 and not mode:
            msg("More than 1 argument was used in command line. ")
            args.default = False
            args.unified = False
            self.askUser()
            return
        elif args.default or mode == "d":
            implementHosts(defaultHosts())
        elif args.unified or mode == "u":
            implementHosts(unifiedHosts())
        elif mode == "e":
            sys.exit("Exiting...")
        else:
            self.askUser()
            return
        msg("\nProcess complete.\n")

    def askUser(self):
        modes = ["d", "u", "e"]
        question = ("Please enter:\n"
                    "\t'd' for the default hosts file\n"
                    "\t'u' for a new unified hosts file\n"
                    "\t'e' to exit the program\n> ")
        answer = input(question).strip().lower()
        if answer in modes:
            startProgram(answer)
        else:
            msg("Didn't get that. Let's try again...")
            self.askUser()


class defaultHosts():
    def __init__(self):
        msg("Generating default hosts file...")
        try:
            self.new_hosts_set = set()
            with open(NEW_HOSTS_FILE, "w+") as f:
                f.write(HEADER + "\n")
            msg("done.\n\tSaved to: " + NEW_HOSTS_FILE + "\n")
        except Exception as e:
            msg("failed.\n\t" + str(e), 0)


class unifiedHosts():
    def __init__(self):
        self.sources = []
        self.blacklist = set()
        self.whitelist = set()
        self.sw_set = set()
        self.ew_set = set()
        self.in_set = set()
        self.eq_set = set()
        self.download_set = set()
        self.new_hosts_set = set()
        self.whitelist_set = set()

        self.processLists()
        self.downloadHosts()
        self.makeHosts()

    def processLists(self):
        msg("Processing:\n")
        try:
            msg("\tSources.....")
            if os.path.exists(SOURCES_FILE):
                with open(SOURCES_FILE, "r") as f:
                    seen = set()
                    for line in f:
                        line = line.strip()
                        if (line and not line.startswith("#") and
                                line not in seen):
                            self.sources.append(line)
                            seen.add(line)
                self.source_c = len(self.sources)
                if self.source_c == 0:
                    msg("failed. No source URLs were found.", 0)
                else:
                    msg("ok (" + str(self.source_c) + " urls)\n")
                    url_len = 0
                    for line in self.sources:
                        if len(line) > url_len:
                            url_len = len(line)
                            self.col_max = url_len
            else:
                msg("failed. ('sources' file is missing.)", 0)

            msg("\tBlacklist...")
            if os.path.exists(BLACKLIST_FILE):
                with open(BLACKLIST_FILE, "r") as f:
                    for line in f:
                        line = line.strip().lower()
                        if line and not line.startswith("#"):
                            self.blacklist.add(line)
                self.blacklist_c = len(self.blacklist)
                msg("ok (" + str(self.blacklist_c) + " entries)\n")
            else:
                msg("failed. ('blacklist' file is missing.)\n")

            msg("\tWhitelist...")
            if os.path.exists(WHITELIST_FILE):
                with open(WHITELIST_FILE, "r") as f:
                    for line in f:
                        line = line.strip().lower()
                        if line and not line.startswith("#"):
                            self.whitelist.add(line)
                self.whitelist_c = len(self.whitelist)
                for line in self.whitelist:
                    if line.startswith("*") and line.endswith("*"):
                        line = line.replace("*", "").strip()
                        self.in_set.add(line)
                    elif line.endswith("*"):
                        line = line.replace("*", "").strip()
                        self.sw_set.add(line)
                    elif line.startswith("*"):
                        line = line.replace("*", "").strip()
                        self.ew_set.add(line)
                    elif line:
                        self.eq_set.add(line)
                msg("ok (" + str(self.whitelist_c) + " entries)\n")
            else:
                msg("failed. ('whitelist' file is missing.)\n")
        except Exception as e:
            msg("failed. (" + str(e) + ")", 0)

    def urlStr(self, url, url_c, prog=""):
        spc = 1
        tab = " "*8
        prog_spc = 25
        try:
            offset = self.col_max
            term_size = int(os.get_terminal_size().columns)
            a_spc = term_size - prog_spc - len(tab)
            if a_spc > self.col_max:
                a_spc = self.col_max
            if len(url) > a_spc:
                dots = "..."
                offset = a_spc - len(dots)
            else:
                dots = ""
                spc = a_spc - len(url) + spc
            urlStr = tab + url[:offset] + dots + " "*spc + "| " + prog
            urlStr = urlStr + " "*(term_size - len(urlStr) - len(tab)) + "\r"
        except:
            urlStr = tab + str(url_c) + " "*(3 - len(str(url_c)))
            urlStr = urlStr + " "*(5-len(urlStr)) + "| " + prog + tab + "\r"
        return urlStr

    def downloadHosts(self):
        msg("\nDownloading from following source(s):\n")
        url_c = 0
        err_c = 0
        for url in self.sources:
            self.dom_count = set()
            data = []
            byte_size = 1024
            bytes_down = 0
            url_c += 1
            msg(self.urlStr(url, url_c))
            try:
                content = urlopen(url, timeout=60)
                try:
                    length = float(content.info()["Content-Length"])
                    size = "{0:,.0f} KB".format(length/1024)
                except:
                    size = "??? KB"
                while True:
                    buffer = content.read(byte_size)
                    bytes_down += len(buffer)
                    data.append(buffer)
                    if not len(buffer):
                        break
                    prog = "{0:,.0f} KB".format(bytes_down/1024) + "/" + size
                    msg(self.urlStr(url, url_c, prog))
                download = io.BytesIO(b"".join(data))
                msg(self.urlStr(url, url_c, "Processing..."))
                self.processDownload(download)
                prog = str(len(self.dom_count)) + " domains"
                msg(self.urlStr(url, url_c, prog))
            except Exception as e:
                err_c += 1
                prog = "Failed (" + str(e) + ")"
                msg(self.urlStr(url, url_c, prog))
            msg("\n")
        if err_c == self.source_c:
            msg("Download failed.", 0)

    def processDownload(self, download):
        for line in download:
            try:
                line = line.decode("utf-8").lower()
                if len(line.split()) > 1:
                    line_ip = line.split()[0]
                    line_url = line.split()[1]
                    if line_ip in IP_LIST and line_url not in IP_LIST:
                        line = urlparse("//" + line_url).netloc
                        line = line.encode("idna").decode("utf-8")
                        self.dom_count.add(line)
                        self.download_set.add(line)
            except:
                pass

    def makeHosts(self):
        msg("\nGenerating new unified hosts file...")
        try:
            for line in self.download_set:
                if (any(w in line for w in self.in_set) or
                    any(line.startswith(w) for w in self.sw_set) or
                    any(line.endswith(w) for w in self.ew_set) or
                        line in self.eq_set):
                    self.whitelist_set.add(line)
                if (line not in self.blacklist and
                        line not in self.whitelist_set):
                    self.new_hosts_set.add(line)
            nhs_c = str(len(self.new_hosts_set))
            wls_c = str(len(self.whitelist_set))
            bls_c = str(self.blacklist_c)
            with open(NEW_HOSTS_FILE, "w+") as f:
                f.write(HEADER + "\n\n## Begin unified hosts file ##")
                f.write("\n# Last updated: " + DT + "\n")
                f.write("\n# Blacklisted domains (" + bls_c + "):\n")
                for line in sorted(self.blacklist):
                    f.write(PREFIX + " " + line + "\n")
                f.write("\n# Whitelisted domains (" + wls_c + "):\n")
                for line in sorted(self.whitelist_set):
                    f.write("# " + line + "\n")
                f.write("\n# Blocked domains (" + nhs_c + "):\n")
                for line in sorted(self.new_hosts_set):
                    f.write(PREFIX + " " + line + "\n")
                f.write("## End unified hosts file ##")
            msg("done.\n\tSaved to: " + NEW_HOSTS_FILE + "\n\n")
            msg("\tBlocked " + nhs_c + " unique domains.\n"
                "\tBlacklisted " + bls_c + " domains.\n"
                "\tWhitelisted " + wls_c + " domains.\n")
        except Exception as e:
            msg("failed.\n\t" + str(e), 0)


class implementHosts():
    def __init__(self, cls):
        if WIN and not ADMIN:
            return
        if self.checkHosts(cls):
            msg("\nNote: Newly generated hosts file is same as the "
                "existing hosts file.")
            question = ("\nImplement new hosts file "
                        "anyway (requires admin/root privileges)? (y/n): ")
        else:
            question = ("\nImplement new hosts file now? "
                        "(requires admin/root privileges) (y/n): ")
        self.askUser(question)

    def askUser(self, question):
        answer = input(question).strip().lower()
        if answer == "y":
            self.implementNow()
        elif answer == "n":
            return
        else:
            msg("Didn't get that. Let's try again...")
            self.askUser(question)

    def checkHosts(self, clss):
        try:
            ex_file_set = set()
            with open(HOSTS_FILE, "r") as f:
                for line in f:
                    if "# Last updated" in line:
                        for line in f:
                            if not line.startswith("#"):
                                ex_file_set.add(line.split()[1])
            if ex_file_set == clss.new_hosts_set:
                return True
        except:
            return False

    def implementNow(self):
        if MAC:
            if call(["sudo", "cd"]):
                msg("\nCould not implement hosts file automatically."
                    " Please try implementing it manually.\n")
                return
        self.backupHosts()
        self.replaceHosts()

    def backupHosts(self):
        question = "Backup existing hosts file? (y/n): "
        answer = input(question).strip().lower()
        if answer == "y":
            try:
                if not os.path.exists(BACKUP_DIR):
                    os.makedirs(BACKUP_DIR)
                copyfile(HOSTS_FILE, BACKUP_FILE)
                msg("\tBackup saved to: " + BACKUP_FILE + "\n")
            except Exception as e:
                msg("\tBackup failed. (" + str(e) + ")\n")
        elif answer == "n":
            return
        else:
            msg("Didn't get that. Let's try again...\n")
            self.backupHosts()

    def replaceHosts(self):
        msg("\nReplacing existing hosts file...")
        try:
            if MAC:
                call(["sudo", "cp", NEW_HOSTS_FILE, HOSTS_FILE])
            elif WIN:
                copyfile(NEW_HOSTS_FILE, HOSTS_FILE)
            msg("done.\n")
            self.flushDNS()
        except Exception as e:
            msg("failed.\n\t" + str(e) + "\n")

    def flushDNS(self):
        msg("Flushing DNS cache...")
        try:
            if MAC:
                call(["sudo", "killall", "-HUP", "mDNSResponder"])
                msg("done.\n")
            elif WIN:
                call(["ipconfig", "/flushdns"])
        except Exception as e:
            msg("failed.\n\t" + str(e) + "\n")


class msg():
    def __init__(self, msg, code=None):
        sys.stdout.write(msg)
        sys.stdout.flush()
        if code == 0:
            sys.exit("\nExiting...")


if __name__ == "__main__":
    try:
        startProgram()
    except KeyboardInterrupt:
        sys.exit("\nProcess aborted.")
