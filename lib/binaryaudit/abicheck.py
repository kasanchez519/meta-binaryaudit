
import subprocess
from xml.etree import ElementTree
import os
import glob
from binaryaudit import util


def is_elf(fn):
    with open(fn, "rb") as fd:
        exp = b"\177ELF"
        head = fd.read(4)
    return head == exp


def get_soname_from_xml(xml):
    r = ElementTree.fromstring(xml)
    try:
        return r.attrib["soname"]
    except (AttributeError, KeyError):
        return ""


def serialize(fn):
    cmd = ["abidw", "--no-corpus-path", fn]
    sout = subprocess.PIPE
    serr = subprocess.STDOUT
    shell = False
    try:
        process = subprocess.Popen(cmd, stdout=sout,
                                   stderr=serr, shell=shell)
        sout, serr = process.communicate()
        out = "".join([out.decode('utf-8') for out in [sout, serr] if out])
    except OSError:
        raise
    # return cmd for logging purposes
    return process.returncode, out, cmd


def compare(ref, cur):
    cmd = ["abidiff", ref, cur]
    sout = subprocess.PIPE
    serr = subprocess.STDOUT
    shell = False
    try:
        process = subprocess.Popen(cmd, stdout=sout,
                                   stderr=serr, shell=shell)
        sout, serr = process.communicate()
        out = "".join([out.decode('utf-8') for out in [sout, serr] if out])
    except OSError:
        raise
    # return cmd for logging purposes
    return process.returncode, out, cmd


def serialize_artifacts(adir, id):
    ''' Recursively serialize binary artifacts starting at the given image directory(id), yields serialized output and filename
    Parameters:
        adir (str): path to abixml directory
        id (str): image directory- result of calling d.getVar("IMG_DIR")
    '''
    for fn in glob.iglob(id + "/**/**", recursive=True):
        if os.path.isfile(fn) and not os.path.islink(fn):
            if not is_elf(fn):
                continue
            # If there's no error, out is the XML representation
            ret, out, cmd = serialize(fn)
            util.note(" ".join(cmd))
            if not 0 == ret:
                util.error(out)
                return
            if not out:
                util.warn("Empty dump output for '{}'".format(fn))
                return

            sn = get_soname_from_xml(out)

            out_fn = util.create_path_to_xml(sn, adir, fn)

            yield out, out_fn


DIFF_OK = 0
DIFF_ERROR = 1
DIFF_USAGE_ERROR = 2
DIFF_CHANGE = 4
DIFF_INCOMPATIBLE_CHANGE = 8


def diff_is_ok(c):
    return 0 == c


def diff_is_error(c):
    return (c & 1) == 1


def diff_is_usage_error(c):
    return (c & 2) == 2


def diff_is_change(c):
    return (c & 4) == 4


def diff_is_incompatible_change(c):
    return (c & 8) == 8


def diff_get_bits(c):
    a = []
    if diff_is_ok(c):
        a.append("OK")
    if diff_is_error(c):
        a.append("ERROR")
    if diff_is_usage_error(c):
        a.append("USAGE_ERROR")
    if diff_is_change(c):
        a.append("CHANGE")
    if diff_is_incompatible_change(c):
        a.append("INCOMPATIBLE_CHANGE")

    return a
