"""Windows utilities"""

import sys
import System.Security.Principal as Principal

def have_admin_rights():
    """"Checks if the process has Administrator rights"""
    identity = Principal.WindowsIdentity.GetCurrent()
    principal = Principal.WindowsPrincipal(identity)
    is_admin = principal.IsInRole(Principal.WindowsBuiltInRole.Administrator)
    return is_admin

def exit_if_not_admin():
    """Exits program if not running as Administrator"""
    if not have_admin_rights():
        sys.exit("Administrator rights are required to run this script!")

def main():
    """Main."""

    is_admin = have_admin_rights()

    if is_admin:
        print "Running as administrator"
    else:
        print "Not running as administrator"

    exit_if_not_admin()

if __name__ == "__main__":
    main()
