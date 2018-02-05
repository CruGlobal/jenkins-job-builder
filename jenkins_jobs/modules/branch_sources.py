# -*- coding: utf-8 -*-
#
# Based on jenkins_jobs/modules/reporters.py by
# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


"""
Branch sources are only applicable to Multibranch Pipeline projects.
They define what should be searched to automatically create Pipeline jobs.

**Component**: branch-sources
  :Macro: branch-source
  :Entry Point: jenkins_jobs.reporters

Example::

  job:
    name: test_job
    project-type: multibranch-pipeline
    branch-sources:
      - github:
          owner: SomeOwner
          repository: some-repository
"""

import xml.etree.ElementTree as XML

from jenkins_jobs.errors import JenkinsJobsException
import jenkins_jobs.modules.base


# def git(registry, xml_parent, data):
#     """yaml: git
#     Git branch source


def github(registry, xml_parent, data):
    """yaml: github
    Github branch source

    """
    source = XML.SubElement(
        xml_parent,
        'source',
        {
            'class': 'org.jenkinsci.plugins.github_branch_source.'
                     'GitHubSCMSource',
            'plugin': 'github-branch-source'
        }
    )

    credentials_id = data.get('credentials-id', None)
    if credentials_id is not None:
        XML.SubElement(source, 'credentialsId').text = credentials_id

    XML.SubElement(source, 'repoOwner').text = data['owner']
    XML.SubElement(source, 'repository').text = data['repository']
    add_property_strategy(xml_parent, data)


def add_property_strategy(xml_parent, data):
    # I'm not implementing this now,
    # but this is where a non-default property strategy would be set up.

    strategy_xml = XML.SubElement(
        xml_parent,
        'strategy',
        {'class': 'jenkins.branch.DefaultBranchPropertyStrategy'}
    )
    XML.SubElement(
        strategy_xml,
        'properties',
        {'class': 'empty-list'}
    )


class BranchSources(jenkins_jobs.modules.base.Base):
    sequence = 85

    component_type = 'branch-source'
    component_list_type = 'branch-sources'

    def gen_xml(self, xml_parent, data):
        if 'branch-sources' not in data:
            return

        mb_class = 'org.jenkinsci.plugins.workflow.multibranch.' \
                   'WorkflowMultiBranchProject'
        if xml_parent.tag != mb_class:
            raise JenkinsJobsException(
                "Branch Sources may only be used for Multibranch Pipelines"
            )

        sources = XML.SubElement(
            xml_parent,
            'sources',
            {
                'class': 'jenkins.branch.MultiBranchProject$BranchSourceList',
                'plugin': 'branch-api'
            }
        )
        data_xml = XML.SubElement(sources, 'data')

        for source in data.get('branch-sources', []):
            branch_source = XML.SubElement(
                data_xml,
                'jenkins.branch.BranchSource'
            )
            self.registry.dispatch('branch-source', branch_source, source)

        XML.SubElement(
            sources,
            'owner',
            {
                'class': mb_class,
                'reference': '../..'
            }
        )
