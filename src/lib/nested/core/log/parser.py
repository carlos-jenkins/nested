# This file is part of Rubber and thus covered by the GPL
# (c) Emmanuel Beffara, 2002--2006
"""
LaTeX document building system for Rubber.

This module defines the class that parses the LaTeX log files.
"""
from __future__ import generators

import re

def _(txt): return txt

class LogParser:
    """
    This class performs all the extraction of information from the log file.
    For efficiency, the instances contain the whole file as a list of strings
    so that it can be read several times with no disk access.
    """

    re_loghead   = re.compile("This is [0-9a-zA-Z-]*(TeX|Omega)")
    re_rerun     = re.compile("(LaTeX|Package longtable|Package bibtopic) Warning:.*Rerun")
    re_rerun2    = re.compile("\(Changebar\).*Rerun")
    re_file      = re.compile("(\\((?P<file>[^ \n\t(){}]*)|\\))")
    re_badbox    = re.compile(r"(Ov|Und)erfull \\[hv]box ")
    re_line      = re.compile(r"(l\.(?P<line>[0-9]+)( (?P<code>.*))?$|<\*>)")
    re_cseq      = re.compile(r".*(?P<seq>\\[^ ]*) ?$")
    re_page      = re.compile("\[(?P<num>[0-9]+)\]")
    re_atline    = re.compile("( detected| in paragraph)? at lines? (?P<line>[0-9]*)(--(?P<last>[0-9]*))?")
    re_reference = re.compile("LaTeX Warning: Reference `(?P<ref>.*)' on page (?P<page>[0-9]*) undefined on input line (?P<line>[0-9]*)\\.$")
    re_label     = re.compile("LaTeX Warning: (?P<text>Label .*)$")
    re_warning   = re.compile("(LaTeX|Package)( (?P<pkg>.*))? Warning: (?P<text>.*)$")
    re_online    = re.compile("(; reported)? on input line (?P<line>[0-9]*)")
    re_ignored   = re.compile("; all text was ignored after line (?P<line>[0-9]*).$")

    #-- Initialization {{{2

    def __init__(self):
        self.lines = []

    def read(self, name):
        """
        Read the specified log file, checking that it was produced by the
        right compiler. Returns true if the log file is invalid or does not
        exist.
        """
        self.lines = []
        try:
            file = open(name)
        except IOError:
            return 2
        line = file.readline()
        if not line:
            file.close()
            return 1
        if not self.re_loghead.match(line):
            file.close()
            return 1
        self.lines = file.readlines()
        file.close()
        return 0

    #-- Process information {{{2

    def errors(self):
        """
        Returns true if there was an error during the compilation.
        """
        skipping = 0
        for line in self.lines:
            if line.strip() == "":
                skipping = 0
                continue
            if skipping:
                continue
            m = self.re_badbox.match(line)
            if m:
                skipping = 1
                continue
            if line[0] == "!":
                # We check for the substring "pdfTeX warning" because pdfTeX
                # sometimes issues warnings (like undefined references) in the
                # form of errors...

                if line.find("pdfTeX warning") == -1:
                    return 1
        return 0

    def run_needed(self):
        """
        Returns true if LaTeX indicated that another compilation is needed.
        """
        for line in self.lines:
            if self.re_rerun.match(line):
                return 1
            if self.re_rerun2.match(line):
                return 1
        return 0

    #-- Information extraction {{{2

    def continued(self, line):
        """
        Check if a line in the log is continued on the next line. This is
        needed because TeX breaks messages at 79 characters per line. We make
        this into a method because the test is slightly different in Metapost.
        """
        return len(line) == 79

    def parse(self, errors=0, boxes=0, refs=0, warnings=0):
        """
        Parse the log file for relevant information. The named arguments are
        booleans that indicate which information should be extracted:
        - errors: all errors
        - boxes: bad boxes
        - refs: warnings about references
        - warnings: all other warnings
        The function returns a generator. Each generated item is a dictionary
        that contains (some of) the following entries:
        - kind: the kind of information ("error", "box", "ref", "warning")
        - text: the text of the error or warning
        - code: the piece of code that caused an error
        - log_line: line where the item appeared
        - file, line, last, pkg: as used by Message.format_pos.
        """
        if not self.lines:
            return
        last_file = None
        pos = [last_file]
        page = 1
        parsing = 0    # 1 if we are parsing an error's text
        skipping = 0   # 1 if we are skipping text until an empty line
        something = 0  # 1 if some error was found
        prefix = None  # the prefix for warning messages from packages
        accu = ""      # accumulated text from the previous line
        log_line = 1   # the current log line
        for line in self.lines:
            log_line = log_line + 1
            line = line[:-1]  # remove the line feed

            # TeX breaks messages at 79 characters, just to make parsing
            # trickier...

            if self.continued(line):
                accu += line
                continue
            line = accu + line
            accu = ""

            # Text that should be skipped (from bad box messages)

            if prefix is None and line == "":
                skipping = 0
                continue

            if skipping:
                continue

            # Errors (including aborted compilation)

            if parsing:
                if error == "Undefined control sequence.":
                    # This is a special case in order to report which control
                    # sequence is undefined.
                    m = self.re_cseq.match(line)
                    if m:
                        error = "Undefined control sequence %s." % m.group("seq")
                m = self.re_line.match(line)
                if m:
                    parsing = 0
                    skipping = 1
                    pdfTeX = error.find("pdfTeX warning") != -1
                    if (pdfTeX and warnings) or (errors and not pdfTeX):
                        if pdfTeX:
                            d = {
                                "kind": "warning",
                                "pkg" : "pdfTeX",
                                "text": error[error.find(":")+2:]
                            }
                        else:
                            d = {
                                "kind": "error",
                                "text": error
                            }
                        d.update( m.groupdict() )
                        m = self.re_ignored.search(error)
                        if m:
                            d["file"] = last_file
                            if d.has_key("code"):
                                del d["code"]
                            d.update( m.groupdict() )
                        elif pos[-1] is None:
                            d["file"] = last_file
                        else:
                            d["file"] = pos[-1]
                        d["log_line"] = log_line
                        yield d
                elif line[0] == "!":
                    error = line[2:]
                elif line[0:3] == "***":
                    parsing = 0
                    skipping = 1
                    if errors:
                        yield    {
                            "kind": "abort",
                            "text": error,
                            "why" : line[4:],
                            "file": last_file,
                            "log_line" : log_line
                            }
                elif line[0:15] == "Type X to quit ":
                    parsing = 0
                    skipping = 0
                    if errors:
                        yield    {
                            "kind": "error",
                            "text": error,
                            "file": pos[-1],
                            "log_line" : log_line
                            }
                continue

            if len(line) > 0 and line[0] == "!":
                error = line[2:]
                parsing = 1
                continue

            if line == "Runaway argument?":
                error = line
                parsing = 1
                continue

            # Long warnings

            if prefix is not None:
                if line[:len(prefix)] == prefix:
                    text.append(line[len(prefix):].strip())
                else:
                    text = " ".join(text)
                    m = self.re_online.search(text)
                    if m:
                        info["line"] = m.group("line")
                        text = text[:m.start()] + text[m.end():]
                    if warnings:
                        info["text"] = text
                        d = { "kind": "warning" }
                        d.update( info )
                        d["log_line"] = log_line
                        yield d
                    prefix = None
                continue

            # Undefined references

            m = self.re_reference.match(line)
            if m:
                if refs:
                    d = {
                        "kind": "warning",
                        "text": _("Reference `%s' undefined.") % m.group("ref"),
                        "file": pos[-1],
                        "log_line" : log_line
                        }
                    d.update( m.groupdict() )
                    yield d
                continue

            m = self.re_label.match(line)
            if m:
                if refs:
                    d = {
                        "kind": "warning",
                        "file": pos[-1],
                        "log_line" : log_line
                        }
                    d.update( m.groupdict() )
                    yield d
                continue

            # Other warnings

            if line.find("Warning") != -1:
                m = self.re_warning.match(line)
                if m:
                    info = m.groupdict()
                    info["file"] = pos[-1]
                    info["page"] = page
                    if info["pkg"] is None:
                        del info["pkg"]
                        prefix = ""
                    else:
                        prefix = ("(%s)" % info["pkg"])
                    prefix = prefix.ljust(m.start("text"))
                    text = [info["text"]]
                continue

            # Bad box messages

            m = self.re_badbox.match(line)
            if m:
                if boxes:
                    mpos = { "file": pos[-1], "page": page }
                    m = self.re_atline.search(line)
                    if m:
                        md = m.groupdict()
                        for key in "line", "last":
                            if md[key]: mpos[key] = md[key]
                        line = line[:m.start()]
                    d = {
                        "kind": "warning",
                        "text": line,
                        "log_line" : log_line
                        }
                    d.update( mpos )
                    yield d
                skipping = 1
                continue

            # If there is no message, track source names and page numbers.

            last_file = self.update_file(line, pos, last_file)
            page = self.update_page(line, page)

    def get_errors(self):
        return self.parse(errors=1)
    def get_boxes(self):
        return self.parse(boxes=1)
    def get_references (self):
        return self.parse(refs=1)
    def get_warnings (self):
        return self.parse(warnings=1)

    def update_file(self, line, stack, last):
        """
        Parse the given line of log file for file openings and closings and
        update the list `stack'. Newly opened files are at the end, therefore
        stack[1] is the main source while stack[-1] is the current one. The
        first element, stack[0], contains the value None for errors that may
        happen outside the source. Return the last file from which text was
        read (the new stack top, or the one before the last closing
        parenthesis).
        """
        m = self.re_file.search(line)
        while m:
            if line[m.start()] == '(':
                last = m.group("file")
                stack.append(last)
            else:
                last = stack[-1]
                del stack[-1]
            line = line[m.end():]
            m = self.re_file.search(line)
        return last

    def update_page(self, line, before):
        """
        Parse the given line and return the number of the page that is being
        built after that line, assuming the current page before the line was
        `before'.
        """
        ms = self.re_page.findall(line)
        if ms == []:
            return before
        return int(ms[-1]) + 1

