#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__license__ = 'GPL v3'

# Standard Python modules.
from typing import Any, Literal, overload
import os, sys, traceback, subprocess

#@@CALIBRE_COMPAT_CODE@@

from . import PLUGIN_NAME, PLUGIN_VERSION


class NoWinePython3Exception(Exception):
    pass


class MissingWinePythonDependencyException(Exception):
    pass


class WinePythonCLI:
    py3_test: str = "import sys; sys.exit(0 if (sys.version_info.major==3) else 1)"
    wineprefix: str | None
    python_path: str | None
    python_exec: list[str]

    def __init__(self, wineprefix: str = "", python_path: str | None = None, dependencies: list[tuple[str, str]] | None = None):
        dependencies = dependencies or []

        if wineprefix != "":
            wineprefix = os.path.abspath(os.path.expanduser(os.path.expandvars(wineprefix)))

        if wineprefix != "" and os.path.exists(wineprefix):
            self.wineprefix = wineprefix
        else:
            self.wineprefix = None

        self.python_path = python_path

        candidate_execs = [
            ["wine", "py.exe", "-3"],
            ["wine", "python3.exe"],
            ["wine", "python.exe"],
        ]
        for e in candidate_execs:
            self.python_exec = e
            try:
                self.check_call(["-c", self.py3_test])
                print("{0} v{1}: Python3 exec found as {2}".format(
                    PLUGIN_NAME, PLUGIN_VERSION, " ".join(self.python_exec)
                ))
                break
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    print("{0} v{1}: {2} is not python3".format(
                        PLUGIN_NAME, PLUGIN_VERSION, " ".join(self.python_exec)
                    ))
                elif e.returncode == 53:
                    print("{0} v{1}: {2} does not exist".format(
                        PLUGIN_NAME, PLUGIN_VERSION, " ".join(self.python_exec)
                    ))
        else:
            import tempfile
            import requests

            installer_url = "https://www.python.org/ftp/python/3.14.6/python-3.14.6-amd64.exe"
            installer_filename = "python-3.14.6-amd64.exe"
            install_args = ["/passive",  "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0"]

            with tempfile.TemporaryDirectory() as tmpdir:
                installer_path = os.path.join(tmpdir, installer_filename)
                with open(installer_path, "wb") as installer_file:
                    print(f"{PLUGIN_NAME} v{PLUGIN_VERSION}: Downloading Windows Python installer")
                    r = requests.get(installer_url, stream=True)
                    for chunk in r.iter_content(chunk_size=None):
                        _ = installer_file.write(chunk)
                try:
                    print(f"{PLUGIN_NAME} v{PLUGIN_VERSION}: Running installer")
                    _ = subprocess.check_call(["wine", installer_path] + install_args,
                        stdin=None, stdout=sys.stdout,
                        stderr=subprocess.STDOUT, close_fds=False,
                        bufsize=1
                    )
                except subprocess.CalledProcessError:
                    raise NoWinePython3Exception("Could not install python3 on specified wine prefix")

            self.python_exec = ["wine", "python.exe"]
            try:
                self.check_call(["-c", self.py3_test])
            except subprocess.CalledProcessError:
                raise NoWinePython3Exception("Could run installed python on specified wine prefix")

        for package, requirement in dependencies:
            dep_check = f"import {package}"
            try:
                self.check_call(["-c", dep_check])
            except subprocess.CalledProcessError:
                self.install_package(requirement)
                try:
                    self.check_call(["-c", dep_check])
                except subprocess.CalledProcessError:
                    raise MissingWinePythonDependencyException(
                        f"Could not use package: {package}",
                    )


    def install_package(self, requirement_specifier: str):
        print(f"{PLUGIN_NAME} v{PLUGIN_VERSION}: Installing dependency {requirement_specifier}")
        try:
            self.check_call(["-m", "pip", "install", requirement_specifier])
        except subprocess.CalledProcessError:
            raise MissingWinePythonDependencyException(
                f"Could not install required dependency: {requirement_specifier}",
            )


    def check_call(self, cli_args: list[str]):
        env_dict = dict(os.environ)

        if self.python_path is not None:
            env_dict["PYTHONPATH"] = self.python_path
        else:
            env_dict["PYTHONPATH"] = ""

        if self.wineprefix is not None:
            env_dict["WINEPREFIX"] = self.wineprefix

        _ = subprocess.check_call(self.python_exec + cli_args, env=env_dict,
                              stdin=None, stdout=sys.stdout,
                              stderr=subprocess.STDOUT, close_fds=False,
                              bufsize=1)

@overload
def WineGetKeys(python_path: str, python_module: str, outdirpath: str, extension: Literal[".k4i"], wineprefix: str = "", dependencies: list[tuple[str, str]] | None = None) -> tuple[list[Any], list[str]]: ...
@overload
def WineGetKeys(python_path: str, python_module: str, outdirpath: str, extension: str, wineprefix: str = "", dependencies: list[tuple[str, str]] | None = None) -> tuple[list[bytes], list[str]]: ...

def WineGetKeys(python_path: str, python_module: str, outdirpath: str, extension: str, wineprefix: str = "", dependencies: list[tuple[str, str]] | None = None) -> tuple[list[Any] | list[bytes], list[str]]:

    if extension == ".k4i":
        import json

    try:
        pyexec = WinePythonCLI(wineprefix, python_path, dependencies)
    except NoWinePython3Exception as e:
        print(f'{PLUGIN_NAME} v{PLUGIN_VERSION}: Unable to find python3 executable in WINEPREFIX="{wineprefix}: {e.args[0]}"')
        return [], []

    print("{0} v{1}: Running {2} under Wine".format(PLUGIN_NAME, PLUGIN_VERSION, python_module))

    if not os.path.exists(outdirpath):
        os.makedirs(outdirpath)

    if wineprefix != "":
        wineprefix = os.path.abspath(os.path.expanduser(os.path.expandvars(wineprefix)))

    try:
        pyexec.check_call(["-m", python_module, outdirpath])
    except Exception as e:
        print("{0} v{1}: Wine subprocess call error: {2}".format(PLUGIN_NAME, PLUGIN_VERSION, e.args[0]))

    # try finding winekeys anyway, even if above code errored
    winekeys: list[Any] | list[bytes] = []
    winekey_names: list[str] = []
    # get any files with extension in the output dir
    files = [f for f in os.listdir(outdirpath) if f.endswith(extension)]
    for filename in files:
        fpath = os.path.join(outdirpath, filename)
        try:
            with open(fpath, 'rb') as keyfile:
                if extension == ".k4i":
                    new_key_value = json.loads(keyfile.read())
                else:
                    new_key_value = keyfile.read()
            winekeys.append(new_key_value)
            winekey_names.append(filename)
        except:
            print("{0} v{1}: Error loading file {2}".format(PLUGIN_NAME, PLUGIN_VERSION, filename))
            traceback.print_exc()
        os.remove(fpath)
    print("{0} v{1}: Found and decrypted {2} {3}".format(PLUGIN_NAME, PLUGIN_VERSION, len(winekeys), "key file" if len(winekeys) == 1 else "key files"))
    return winekeys, winekey_names
