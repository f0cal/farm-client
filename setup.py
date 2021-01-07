#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for f0cal.farm.client.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 3.1.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
import sys

from pkg_resources import require, VersionConflict
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.develop import develop as _develop

import glob
import os.path
import black
import yaml
import jinja2
import pathlib

try:
    require('setuptools>=38.3')
except VersionConflict:
    print("Error: version of setuptools is too old (<38.3)!")
    sys.exit(1)

class CodeGen:
    TEMPLATE_PATTERN = "src/**/__codegen__/*.jj2"
    BLOB_PATTERN = "src/**/__codegen__/*.yml"

    @property
    def _templates(self):
        return glob.glob(self.TEMPLATE_PATTERN, recursive=True)

    @property
    def _data_blobs(self):
        return glob.glob(self.BLOB_PATTERN, recursive=True)

    @property
    def _codegen_targets(self):
        _strip = lambda _path: os.path.splitext(_path)[0]
        data_blobs = {_strip(v): v for v in self._data_blobs}
        templates = {_strip(v): v for v in self._templates}
        all_keys = set(data_blobs.keys()) & set(templates.keys())
        _val = lambda _key: (templates[_key], data_blobs[_key])
        return {k: _val(k) for k in all_keys}

    def _run_codegen(self):
        _targets = self._codegen_targets
        for py_filename in _targets:
            template_filename, data_blob_filename = _targets[py_filename]
            py_filename = f"{py_filename}.py"
            self._run_one_codegen(py_filename, template_filename, data_blob_filename)
            self._format_code(py_filename)
            self._write_init(py_filename)

    def _format_code(self, py_filename):
        _dargs = dict(fast=False, mode=black.FileMode(), write_back=black.WriteBack.YES)
        assert black.format_file_in_place(pathlib.Path(py_filename), **_dargs), py_filename

    def _write_init(self, py_filename):
        init_path = os.path.join(os.path.dirname(py_filename), '__init__.py')
        if not os.path.exists(init_path):
            open(init_path, 'w').close()

    def _run_one_codegen(self, py_filename, template_filename, data_blob_filename):
        with open(py_filename, 'w') as py_file:
            py_str = self._render(template_filename, data_blob_filename)
            py_file.write(py_str)

    def _template_by_path(self, full_path):
        dir_name, file_name = os.path.split(full_path)
        loader = jinja2.FileSystemLoader(searchpath=dir_name)
        return jinja2.Environment(loader=loader).get_template(file_name)

    def _render(self, template_filename, data_blob_filename):
        blob = yaml.safe_load(open(data_blob_filename))
        _vars = lambda: blob
        template = self._template_by_path(template_filename)
        return template.render(vars=_vars, **blob)

    def run(self):
        self._run_codegen()
        super().run()

if __name__ == "__main__":
    _cmdclass = dict(build_py=type('BuildPyCodeGen', (CodeGen, _build_py, ), {}),
                     develop=type('DevelopCodeGen', (CodeGen, _develop, ), {}),
                     )
    setup(use_pyscaffold=True,
          cmdclass=_cmdclass,
          )
