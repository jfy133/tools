#!/usr/bin/env python
""" Tests covering the modules commands
"""

import nf_core.modules

import os
import shutil
import tempfile
import unittest
import pytest
from rich.console import Console


class TestModules(unittest.TestCase):
    """Class for modules tests"""

    def setUp(self):
        """ Create a new PipelineSchema and Launch objects """
        # Set up the schema
        root_repo_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.template_dir = os.path.join(root_repo_dir, "nf_core", "pipeline-template")
        self.pipeline_dir = os.path.join(tempfile.mkdtemp(), "mypipeline")
        shutil.copytree(self.template_dir, self.pipeline_dir)
        self.mods = nf_core.modules.PipelineModules()
        self.mods.pipeline_dir = self.pipeline_dir

    def test_modulesrepo_class(self):
        """ Initialise a modules repo object """
        modrepo = nf_core.modules.ModulesRepo()
        assert modrepo.name == "nf-core/modules"
        assert modrepo.branch == "master"

    def test_modules_list(self):
        """ Test listing available modules """
        self.mods.pipeline_dir = None
        listed_mods = self.mods.list_modules()
        console = Console(record=True)
        console.print(listed_mods)
        output = console.export_text()
        assert "fastqc" in output

    def test_modules_install_nopipeline(self):
        """ Test installing a module - no pipeline given """
        self.mods.pipeline_dir = None
        assert self.mods.install("foo") is False

    def test_modules_install_emptypipeline(self):
        """ Test installing a module - empty dir given """
        self.mods.pipeline_dir = tempfile.mkdtemp()
        with pytest.raises(UserWarning) as excinfo:
            self.mods.install("foo")
        assert "Could not find a 'main.nf' or 'nextflow.config' file" in str(excinfo.value)

    def test_modules_install_nomodule(self):
        """ Test installing a module - unrecognised module given """
        assert self.mods.install("foo") is False

    def test_modules_install_fastqc(self):
        """ Test installing a module - FastQC """
        assert self.mods.install("fastqc") is not False
        module_path = os.path.join(self.mods.pipeline_dir, "modules", "nf-core", "software", "fastqc")
        assert os.path.exists(module_path)

    def test_modules_install_fastqc_twice(self):
        """ Test installing a module - FastQC already there """
        self.mods.install("fastqc")
        assert self.mods.install("fastqc") is False

    def test_modules_remove_fastqc(self):
        """ Test removing FastQC module after installing it"""
        self.mods.install("fastqc")
        module_path = os.path.join(self.mods.pipeline_dir, "modules", "nf-core", "software", "fastqc")
        assert self.mods.remove("fastqc")
        assert os.path.exists(module_path) is False

    def test_modules_remove_fastqc_uninstalled(self):
        """ Test removing FastQC module without installing it """
        assert self.mods.remove("fastqc") is False

    def test_modules_lint_fastqc(self):
        """ Test linting the fastqc module """
        self.mods.install("fastqc")
        module_lint = nf_core.modules.ModuleLint(dir=self.pipeline_dir)
        module_lint.lint(print_results=False, all_modules=True)
        assert len(module_lint.passed) == 19
        assert len(module_lint.warned) == 0
        assert len(module_lint.failed) == 0

    def test_modules_lint_empty(self):
        """ Test linting a pipeline with no modules installed """
        module_lint = nf_core.modules.ModuleLint(dir=self.pipeline_dir)
        module_lint.lint(print_results=False, all_modules=True)
        assert len(module_lint.passed) == 0
        assert len(module_lint.warned) == 0
        assert len(module_lint.failed) == 0

    def test_modules_create_succeed(self):
        """ Succeed at creating the FastQC module """
        module_create = nf_core.modules.ModuleCreate(self.pipeline_dir, "fastqc", "@author", "process_low", True, True)
        module_create.create()
        assert os.path.exists(os.path.join(self.pipeline_dir, "modules", "local", "fastqc.nf"))

    def test_modules_create_fail_exists(self):
        """ Fail at creating the same module twice"""
        module_create = nf_core.modules.ModuleCreate(
            self.pipeline_dir, "fastqc", "@author", "process_low", False, False
        )
        module_create.create()
        with pytest.raises(UserWarning) as excinfo:
            module_create.create()
        assert "Module file exists already" in str(excinfo.value)
