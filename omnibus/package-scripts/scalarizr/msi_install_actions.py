"""
A set of windows pre- and postinstall actions.
"""
import argparse
import glob
import json
import logging
import os
import psutil
import re
import shutil
import subprocess
import sqlite3
import time
import _winreg
from logging import config

from windows_helpers import (
    get_symbolic_target,
    open_dir,
    check_closed,
    pywin32_update_system,
    ctypes_update_system,
    set_HKLM_key,
    get_HKLM_key,
    delete_HKLM_key)

try:
    from common.utils import sysutil
    from scalarizr.queryenv import QueryEnvService
except ImportError:
    sysutil = None
    QueryEnvService = None

parser = argparse.ArgumentParser()
parser.add_argument('--app_root', dest='APP_ROOT',
                    help="""
a location where all application's VERSION-specific dirs are stored:\n
APP_ROOT/\n
        /CURRENT\n
        /1.2.3\n
        /4.5.6\n
        /etc'\n
""")
parser.add_argument("--projectlocation", dest="PROJECTLOCATION",
                    help="An exact install location: APP_ROOT\\version. See --app_root.")
parser.add_argument("--version", dest="VERSION", help="A version we are installing right now")
parser.add_argument("--phase", dest="PHASE", help="Installation phase: pre, post")
args = parser.parse_args()

if args.APP_ROOT:
    APP_ROOT = args.APP_ROOT.strip().strip("'")
elif args.PROJECTLOCATION:
    PROJECTLOCATION = args.PROJECTLOCATION.strip().strip("'").strip("\\")
    APP_ROOT = os.path.split(PROJECTLOCATION)[0]
VERSION = args.VERSION.strip().strip("'")
PHASE = args.PHASE.strip().strip("'")

# a path to directory symlink pointing to actuall app installation
CURRENT = os.path.abspath(os.path.join(APP_ROOT, 'current'))
ETCDIR = os.path.abspath(os.path.join(APP_ROOT, 'etc'))
LOGDIR = os.path.abspath(os.path.join(APP_ROOT, 'var/log'))
PROCDIR = os.path.abspath(os.path.join(APP_ROOT, 'var/run'))
LOGFILE = os.path.abspath(os.path.join(LOGDIR, 'installscripts-{0}-log.txt'.format(VERSION)))
ETC_BACKUP_DIR = os.path.abspath(os.path.join(APP_ROOT, 'etc_bkp'))
LEGACY_INSTALLDIR = 'C:\\Program Files\\Scalarizr'
STATUS_FILE = os.path.abspath(os.path.join(APP_ROOT, 'service_status'))
HKLM_ENV_KEY = 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment'
START_TIMEOUT = 5
UPDATECLIENT_TIMEOUT = 60
SERVICE_NAMES = ('Scalarizr', 'ScalrUpdClient')
# set default shell for subprocess to use
os.environ['COMSPEC'] = "C:\\Windows\\System32\\cmd.exe"
# Logging will not create log directories, C:\var\log should exist
for dir_ in (LOGDIR, PROCDIR):
    if not os.path.exists(dir_):
        os.makedirs(dir_)


log_settings = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': LOGFILE,
        },

    },
    'formatters': {
        'detailed': {
            'format': '%(asctime)s.%(msecs)03d %(levelname)-4s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'loggers': {
        'extensive': {
            'level': 'DEBUG',
            'handlers': ['file', ]
        },
    }
}
logging.config.dictConfig(log_settings)
LOG = logging.getLogger('extensive')
# we'll put some computations in a simple cache
cache = {}


def main():
    """
    Script entry point.
    """
    try:
        LOG.info(
            '\n\nProcessing the following command call:'
            '\n {0}\\embedded\\python.exe {0}\\embedded\\installscripts\\msi_install_actions.py '
            '--phase="{1}" --projectlocation="{0}" --version="{2}"'.format(
                PROJECTLOCATION,
                PHASE,
                VERSION
            ))
        LOG.info('Starting {0}install sequense'.format(PHASE))
        if PHASE in ('pre', 'preinstall'):
            preinstall_sequence()
        if PHASE in ('post', 'postinstall'):
            postinstall_sequence()
        if PHASE in ('preun', 'preuninstall'):
            preuninstall_sequence()
    except Exception, e:
        LOG.exception(e)


def preinstall_sequence():
    """
    A set of acions to run after InstallInitialize.
    """
    LOG.info('Deleting artifacts left from previous scalarizr installations in {0}'.format(APP_ROOT))
    delete_previous()
    stop_szr()


def postinstall_sequence():
    """
    A set of actions to run after InstallFinalize.
    """
    check_for_migration()
    stop_szr()
    copy_configuration()
    toggle_corev2()
    mock_legacy_install()
    register_new_package()
    sysutil.touch(os.path.join(ETCDIR, 'private.d', '.update'))
    check_install_successful()
    rm_r(ETC_BACKUP_DIR)


def register_new_package():
    relink()
    create_bat_files()
    add_binaries_to_path()
    open_firewall()
    install_services()
    db_migrations()
    set_servicewide_pythonpath()
    send_wmisettingschangesignal()


def preuninstall_sequence():
    backup_config()
    uninstall_services()
    unlink_current()


def check_for_migration():
    """
    Check if legacy package is present in system and service hadles are linked to its location.
    """
    LOG.info('Setting migraion status...')
    cache['migration'] = False
    services_path = 'SYSTEM\\CurrentControlSet\\Services\\{0}'

    try:
        got_legacy_service_handles = all([
            get_HKLM_key(
                path=services_path.format(service),
                name='ImagePath'
            ).strip('"').startswith(LEGACY_INSTALLDIR)
            for service in SERVICE_NAMES])
    # will raise WindowsError in case reg path not exists
    except WindowsError:
        got_legacy_service_handles = False

    if (os.path.exists(abspath_join(LEGACY_INSTALLDIR, 'uninst.exe')) and
            'Scalarizr' in powershell_run('Get-Service') and
            got_legacy_service_handles):
        LOG.info('\t\tPositive')
        cache['migration'] = True
    else:
        LOG.info('\t\tNegative')


def uninstall_legacy_package():
    """
    If we are doing second-after-migration install and scalarizr was already running
    before this install, then we can safely uninstall legacy package
    """
    if not all((os.path.exists(LEGACY_INSTALLDIR),
                os.path.exists(CURRENT),
                cache.get('szr_status') is not None)):
        return

    LOG.info("Legacy and new package artifacts present simultaneously.\n")

    LOG.info("Removing legacy {0}".format(LEGACY_INSTALLDIR))
    try:
        subprocess.check_call('cmd.exe /c rmdir /S /Q "{0}"'.format(LEGACY_INSTALLDIR), shell=True)
    except subprocess.CalledProcessError, e:
        LOG.warn('Unable to complete artifats removal. Reason:\n{0}'.format(e))

    LOG.info("Unregistering legacy package")
    try:
        delete_HKLM_key(path='Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall', name='Scalarizr')
    except WindowsError, e:
        LOG.warn('Unable to unregister package, reason:\n {0}'.format(e))
    LOG.info('Legacy package uninstalled')


def mock_legacy_install():
    """
    In case we are doing a migration, a LEGACY_INSTALLDIR/src directory should be created,
    in order legacy update script could confirm that new files were added during install.
    """
    legacy_src = abspath_join(LEGACY_INSTALLDIR, 'src')
    if os.path.exists(LEGACY_INSTALLDIR) and not os.path.exists(legacy_src):
        os.makedirs(legacy_src)


def delete_previous():
    """
    Delete all directories inside scalarizr location
    except one that is symlinked to CURRENT
    """
    LOG.info('Cleaning up application root')
    if not os.path.exists(CURRENT):
        return
    real_location = realpath(CURRENT)
    LOG.debug('\t\t{0} points to {1}'.format(CURRENT, real_location))
    confdir = abspath_join(APP_ROOT, 'etc')
    vardir = abspath_join(APP_ROOT, 'var')
    excludes = (real_location, CURRENT, vardir, confdir, ETC_BACKUP_DIR)
    excludes = [loc.capitalize() for loc in excludes]
    LOG.debug('Excludes are {0}'.format(excludes))
    for location in glob.glob(APP_ROOT + '\\*'):
        if location.capitalize() in excludes:
            LOG.debug('\t\t\tleaving {0} intact'.format(location))
            continue
        LOG.debug('\t\t\t{0} not in excludes'.format(location))
        LOG.debug('\t\t\tRemoving {0}'.format(location))
        rm_r(location)


def unlink_current():
    """
    Unlink CURRENT application VERSION
    """
    if os.path.exists(CURRENT):
        LOG.info('\t\t- Removing {0}'.format(CURRENT))
        try:
            subprocess.check_call('rmdir /S /Q "{0}"'.format(CURRENT), shell=True)
        except subprocess.CalledProcessError, e:
            LOG.warn('Unable to complete artifats removal. Reason:\n{0}'.format(e))


def link_current(target):
    """
    Create link for the VERSION that is being installed.
    """
    LOG.info('\t\t- Linking {0} to {1}'.format(CURRENT, target))
    subprocess.check_call('cmd.exe /c mklink /D "{0}" "{1}"'.format(CURRENT, target), shell=True)


def relink():
    LOG.info('Resetting "APP_ROOT\\current" symlink target.')
    unlink_current()
    new = abspath_join(APP_ROOT, VERSION)
    link_current(new)


def add_binaries_to_path():
    """
    Add application's binary files location to a
    systemwide PATH environment variable.
    """
    LOG.info('Adding {0}\\bin to current user\'s PATH environment variable'.format(CURRENT))
    binaries = ";".join([abspath_join(CURRENT, 'bin'), APP_ROOT])
    if not on_path(binaries):
        add_to_path(binaries)


def create_bat_files():
    """
    Create .bat files  with a deprecation notification
    in a root installation dir.
    """
    LOG.info('Creating .bat files in {0}'.format(APP_ROOT))
    binaries = abspath_join(CURRENT, 'bin')
    contents = ('echo "{0}.bat is deprecated you can use {0} instead"\n'
                'start /d \"%s\" {0}.exe\npause') % (binaries)
    for executable in ('scalarizr', 'szradm', 'scalr-upd-client'):
        bat_location = abspath_join(APP_ROOT, '{0}.bat'.format(executable))
        with open(bat_location, 'w+') as fp:
            fp.write(contents.format(executable))


def copy_configuration():
    """
    Copy configuration files from previous installation(if any)
    into new installation and then into APP_ROOT/etc.
    Overwrite when copying to APP_ROOT/VERSION/etc.
    Do not overwrite when copying to APP_ROOT/etc.
    """
    legacy_conf_dir = abspath_join(LEGACY_INSTALLDIR, "etc")
    new_conf_dir = abspath_join(APP_ROOT, VERSION, 'etc')
    root_conf_dir = abspath_join(APP_ROOT, 'etc')
    if os.path.exists(CURRENT):
        previous_conf_dir = abspath_join(realpath(CURRENT), 'etc')
        if os.path.exists(ETC_BACKUP_DIR):
            cp_r(ETC_BACKUP_DIR, new_conf_dir, overwrite=True)  # first get configs from backup dir
        cp_r(previous_conf_dir, new_conf_dir, overwrite=True)  # then copy from previous symlink target
    elif os.path.exists(legacy_conf_dir):
        cp_r(legacy_conf_dir, root_conf_dir)
    cp_r(new_conf_dir, root_conf_dir)
    if cache.get('migration'):
        for name in SERVICE_NAMES:
            backup_service_registration(name)


def cp_r(source, destination, overwrite=False):
    if overwrite:
        flags = '/E'
        info = 'Overwriting existing'
    else:
        flags = '/E /XN /XO /XC'
        info = 'No overwrite'

    LOG.info('Copying files and dirs from {0} to {1}. {2}'.format(source, destination, info))
    if source == destination:
        LOG.debug('\t\t- Source and destination match. Skipping action.')
        return
    if not os.path.exists(source):
        LOG.info('\t\t- {0} does not exist. Skipping action.'.format(source))
        return
    # robocopy will want you to say 'from sourcedir to destdir copy thefile': 'robocopy source dest file'
    source, thefile, flags = (os.path.split(source) + ('',)) if os.path.isfile(source) else (source, '', flags)
    if not os.path.exists(destination):
        LOG.debug('\t\t- {0} does not exist. Creating.'.format(source))
        os.makedirs(destination)
    subprocess.call(
        'C:\\Windows\\System32\\Robocopy.exe "{0}" "{1}" {2} {3}'.format(source, destination, thefile, flags))


def open_firewall():
    """
    Open firewall ports 8008-8014
    """
    LOG.info('Opening firewall ports 8008-8014')
    try:
        subprocess.check_call(
            'C:\\Windows\\system32\\netsh.EXE '
            'advfirewall firewall add rule name=Scalarizr '
            'dir=in protocol=tcp localport=8008-8014 action=allow',
            shell=True)
    except subprocess.CalledProcessError:
        LOG.info('Negative. Firewall is not running')


def install_services():
    subprocess.check_call('"{0}\\bin\\scalarizr.exe" --install-win-services'.format(CURRENT), shell=True)
    subprocess.check_call('"{0}\\bin\\scalr-upd-client.exe" --startup auto install'.format(CURRENT), shell=True)


def db_migrations():
    db_path = '{0}\\private.d\\db.sqlite'.format(ETCDIR)
    if not os.path.exists(db_path):
        return
    LOG.info('Running database migrations')
    with sqlite3.Connection(db_path) as conn:
        cur = conn.cursor()

        # add column 'format' to 'p2p_message'
        cur.execute('pragma table_info(p2p_message)')
        p2p_message_info = cur.fetchall()
        if p2p_message_info and not any(row for row in p2p_message_info if row[1] == 'format'):
            LOG.info(" - add column 'format' to 'p2p_message'")
            cur.execute("alter table p2p_message add column format TEXT default 'xml'")

        cur.execute('pragma table_info(tasks)')
        tasks_info = cur.fetchall()
        if not tasks_info:
            # create table 'tasks'
            LOG.info(" - create table 'tasks'")
            cur.execute(
                """create table tasks (
                    "task_id" TEXT PRIMARY KEY,
                    "name" TEXT,
                    "args" TEXT,
                    "kwds" TEXT,
                    "state" TEXT,
                    "result" TEXT,
                    "traceback" TEXT,
                    "start_date" TEXT,
                    "end_date" TEXT,
                    "worker_id" TEXT,
                    "soft_timeout" FLOAT,
                    "hard_timeout" FLOAT,
                    "callbacks" TEXT,
                    "meta" TEXT)
                """)
        elif not any(row for row in tasks_info if row[1] == 'callbacks'):
            LOG.info(" - add column 'callbacks' and 'meta' columns to 'tasks'")
            cur.execute("alter table tasks add column callbacks TEXT")
            cur.execute("alter table tasks add column meta TEXT")

        conn.commit()


def check_install_successful():
    """
    Start scalarizr if it was previously running.
    On migration check if scalarizr can run from a
    new location and rollback or cleanup legacy artifacts.
    """
    szr_stopped_by_us = cache.get('szr_status') == 'was_stopped' or os.path.exists(STATUS_FILE)
    LOG.info("Checking if we are doing a manual update")
    manual_update = not updateps1_running() and ('in-progress' not in update_state())
    LOG.info("Update is {}".format('manual' if manual_update else 'automatic'))
    if manual_update:
        try:
            powershell_run('Stop-Service ScalrUpdClient')
        except Exception, e:
            LOG.exception('Unable to stop ScalrUpdClient. Reason:\n {}'.format(e))

    if not cache.get('migration'):
        if szr_stopped_by_us and manual_update:
            LOG.info('Starting scalarizr, as it was previously stopped by this script')
            resume_szr()
        return

    # If we are doing a migration, we should check early
    # that scalarizr can be started, or restore service registration
    LOG.info('An nsis to msi migration took place.')
    LOG.info('Verifying if Scalarizr can run from a new location...')
    try:
        powershell_run('Start-Service Scalarizr')
        time_elapsed = 0
        while time_elapsed < START_TIMEOUT and not scalarizr_running():
            time.sleep(1)
            time_elapsed += 1
    except subprocess.CalledProcessError, e:
        LOG.exception(e)
    finally:
        if scalarizr_running():
            LOG.info('Success. Scalarizr can run from a new location.')
            try:
                if not szr_stopped_by_us and manual_update:
                    LOG.info('Installscripts have started Scalarizr, but it was not running before this install.')
                    LOG.info('Stopping Scalarizr.')
                    powershell_run('Stop-Service Scalarizr')
            except subprocess.CalledProcessError, e:
                LOG.exception(e)
            finally:
                # An update.ps1 should be stopped before it fails on missing
                # registry entries and stops scalarizr and updateclient.
                # The only time we get to executing this is on successful
                # nsis-to-msi migration.
                kill_updateps1()
                uninstall_legacy_package()

        else:
            LOG.error('Scalarizr did not start after {0} second timeout.'.format(START_TIMEOUT))
            rollback_migration()


def rollback_migration():
    LOG.info('Doing rollback.')
    revert_registry_changes()
    unlink_current()

    if not updateps1_running():
        if any((cache.get('szr_status') == 'was_stopped', os.path.exists(STATUS_FILE))):
            resume_szr()
        LOG.info('Rollback complete')
        return

    LOG.info('An automatic update via update.ps1 detected.')
    LOG.info('Starting scalarizr from legacy location')
    try:
        resume_szr()
    except subprocess.CalledProcessError, e:
        # if scalarizr fails to start, at least try to start updclient
        # in order to maintain update-ability on an instance
        LOG.exception(e)
        LOG.error('Scalarizr was unable to start from a legacy location')
        LOG.info('Trying to start ScalrUpdClient')
        powershell_run('Start-Service ScalrUpdClient')
        LOG.info('Success')
    finally:
        LOG.info('Rollback complete')


def update_status():
    status_file = abspath_join(APP_ROOT, 'etc', 'private.d', 'update.status')
    LOG.info('Checking if {} exists'.format(status_file))
    if not os.path.exists(status_file):
        return None
    with open(status_file, 'r+') as fp:
        return json.load(fp)


def update_state():
    status = update_status()
    if not status:
        LOG.info('Negative')
        return ''
    state = status.get('state', "")
    LOG.info('Positive. "state" is "%s"', state)
    return state


def updateps1_running():
    """
    Find a powershell.exe process running 'update.ps1' script.
    If none found, then it's a manual update.
    """
    LOG.info('Checking if update.ps1 running')
    for process in psutil.process_iter():
        if ('powershell.exe' in process.name() and
                any(('update.ps1' in arg) for arg in process.cmdline())):
            cache['update.ps1'] = process
            LOG.info('Positive.')
            return True
    LOG.info('Negative.')
    return False


def kill_updateps1():
    if 'update.ps1' in cache:
        proc = cache.get('update.ps1')
        proc.kill()


def resume_szr():
    powershell_run('Start-Service Scalarizr')
    rm_r(STATUS_FILE)


def revert_registry_changes():
    """
    Make service registry entries point back to LEGACY_INSTALLDIR
    """
    LOG.info('Restoring services registration from cache:')
    LOG.debug(json.dumps(cache['service_registration'], sort_keys=True, indent=4))
    for name in SERVICE_NAMES:
        restore_service_registration(name)
    LOG.info('Restoring  {0}\\Path reg value'.format(HKLM_ENV_KEY))
    set_HKLM_key(path=HKLM_ENV_KEY, name='Path', value=cache['PATH'])
    send_wmisettingschangesignal()


def backup_service_registration(service_name):
    service_key = _winreg.OpenKey(
        _winreg.HKEY_LOCAL_MACHINE,
        "SYSTEM\\CurrentControlSet\\Services\\{0}".format(service_name),
        0,
        _winreg.KEY_ALL_ACCESS
    )

    if 'service_registration' not in cache:
        cache['service_registration'] = {}
    cache['service_registration'][service_name] = {}
    try:
        count = 0
        while 1:
            vname, value, vtype = _winreg.EnumValue(service_key, count)
            cache['service_registration'][service_name][vname] = {'value': value, 'type': vtype}
            count += 1
    except WindowsError:
        pass


def restore_service_registration(service_name):
    # Delete all values  in service related keys
    key_path = "SYSTEM\\CurrentControlSet\\Services\\{0}".format(service_name)
    service_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key_path, 0, _winreg.KEY_ALL_ACCESS)
    # delete all service key values
    try:
        count = 0
        while 1:
            vname, _, vtype = _winreg.EnumValue(service_key, count)
            if vname in cache['service_registration'][service_name]:
                set_HKLM_key(
                    path=key_path,
                    name=vname,
                    value=cache['service_registration'][service_name][vname]['value'],
                    valuetype=vtype)
            else:
                _winreg.DeleteValue(service_key, vname)

            count += 1
    except WindowsError:
        pass


def stop_szr():
    """
    Stop scalarizr if it is running.
    """
    LOG.info('Checking scalarizr is not running.')
    services = powershell_run('Get-Service')
    if 'Scalarizr' not in services:
        return

    LOG.info('\t\t- Found scalarizr in services list')
    if scalarizr_running():
        LOG.info('\t\t- Scalarizr is running. Stopping...')

        powershell_run('Stop-Service Scalarizr')

        # we may already have this set
        # in case we are doing a legacy uninstall
        cache['szr_status'] = cache.get('szr_status') or 'was_stopped'
        LOG.info('\t\t- Stopped scalarizr')
        with open(STATUS_FILE, 'w+') as fp:
            fp.write('was_stopped')
    else:
        LOG.info('\t\t- scalarizr is not running')
        cache['szr_status'] = 'not_running'

    if 'ScalrUpdClient' not in services:
        return
    cache['updclient_status'] = service_status('ScalrUpdClient')
    LOG.debug('ScalrUpdClient is {0}'.format(cache['updclient_status']))


def set_servicewide_pythonpath():
    """
    Create service-scpecific environment to provide pythonpath for scalarizr services.
    """
    LOG.info('Creating service-wide environment to provide pythonpath for Scalarizr services.')
    set_scalrservice_regkeys(
        'Environment',
        ["PYTHONPATH=\"{0}\\src;{0}\\embedded\\Lib;{0}\\embedded\\Lib\\site-packages\"".format(CURRENT)],
        _winreg.REG_MULTI_SZ
    )


def set_scalrservice_regkeys(entryname, value, valuetype):
    """
    Set registry entries for Scalr services.
    """
    path = "SYSTEM\\CurrentControlSet\\Services\\{service_name}"
    for servicename in SERVICE_NAMES:
        set_HKLM_key(
            path=path.format(service_name=servicename),
            name=entryname,
            value=value,
            valuetype=valuetype
        )


def backup_config():
    cp_r(abspath_join(APP_ROOT, 'etc'), ETC_BACKUP_DIR)


def uninstall_services():
    LOG.info("Uninstalling Scalarizr and ScalrUpdClient services")
    powershell_run('Stop-Service Scalarizr')
    powershell_run('Stop-Service ScalrUpdClient')
    subprocess.check_call('"{0}\\bin\\scalarizr.exe" --uninstall-win-services'.format(CURRENT), shell=True)
    subprocess.check_call('"{0}\\bin\\scalr-upd-client.exe" remove'.format(CURRENT), shell=True)


def powershell_run(command):
    """
    Execute oneliner via powerhell
    """
    default_shell = os.environ['COMSPEC']
    os.environ['COMSPEC'] = 'C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\Powershell.exe'
    out = subprocess.check_output('{0}'.format(command), shell=True)
    os.environ['COMSPEC'] = default_shell
    return out.strip()


def abspath_join(*args):
    """
    Shortcut conveniece for absolute path.
    """
    return os.path.abspath(os.path.join(*args))


def add_to_path(path):
    """
    Add path argument to System-wide PATH environment variable.
    Persistent change.
    """
    current_path = get_HKLM_key(path=HKLM_ENV_KEY, name='Path').strip('"')
    cache['PATH'] = current_path
    bin_locations = []
    for location in current_path.split(";"):
        if 'scalarizr' in location.lower():
            continue
        # expand %% variables into strings, as windows registry will not expand
        # programmatic(nonGUI) editions
        location = re.sub("%\w+%", lambda m: os.path.expandvars(m.group()), location)
        bin_locations.append(location)

    bin_locations.append(path)
    new_path = ";".join(bin_locations)
    set_HKLM_key(path=HKLM_ENV_KEY, name='Path', value=new_path)


def on_path(path):
    """
    Check if a dir is on path.
    """
    key_dir = 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment'
    current_path = get_HKLM_key(path=key_dir, name='Path').strip('"')
    return path + ";" in current_path or current_path.endswith(path)


def send_wmisettingschangesignal():
    """
    Apply registry key changes immediatley.
    """
    LOG.info("Updating environment via WM_SETTINGCHANGE signal")
    try:
        pywin32_update_system()
    except ImportError:
        ctypes_update_system()


def realpath(path):
    """
    get_symbolic_target for win
    """
    try:
        import win32file
        f = win32file.CreateFile(
            path,
            win32file.GENERIC_READ,
            win32file.FILE_SHARE_READ,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_FLAG_BACKUP_SEMANTICS,
            None
        )
        target = win32file.GetFinalPathNameByHandle(f, 0)
        # an above gives us something like u'\\\\?\\C:\\tmp\\scalarizr\\3.3.0.7978'
        return target.strip('\\\\?\\')
    except ImportError:
        handle = open_dir(path)
        target = get_symbolic_target(handle)
        check_closed(handle)
        return target


def rm_r(path):
    """
    Recursively remove given path. Do not complain if path abscent.
    """
    if not os.path.exists(path):
        return
    try:
        os.remove(path)
    except OSError:
        try:
            os.rmdir(path)
        except (OSError, WindowsError):
            shutil.rmtree(path)


def scalarizr_running():
    return service_status('Scalarizr').lower() == 'running'


def service_status(name):
    return powershell_run('(Get-Service -Name {0}).Status'.format(name))


def toggle_corev2():
    us = update_status()
    if not us:
        LOG.debug('No update_status, cannot toggle CoreV2.')
        return
    creds = (
        us['queryenv_url'],
        us['server_id'],
        os.path.join(ETCDIR, 'private.d', 'keys', 'default'))
    queryenv = QueryEnvService(*creds)
    queryenv = QueryEnvService(*creds, api_version=queryenv.get_latest_version())

    base = queryenv.list_farm_role_params(us['farm_role_id']).get('params', {}).get('base', {})
    for k, v in base.items():
        if not k.startswith('scalr_labs'):
            continue
        flag_file = os.path.join(os.path.join(ETCDIR, 'private.d'), k)
        if v:
            LOG.debug('Enabling feature: %s', k)
            sysutil.touch(flag_file)
        else:
            sysutil.rm_rf(flag_file)


if __name__ == '__main__':
    main()
