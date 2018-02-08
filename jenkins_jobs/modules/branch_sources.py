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

import jenkins_jobs.modules.base
from jenkins_jobs.errors import JenkinsJobsException, InvalidAttributeError
from jenkins_jobs.modules.helpers import convert_mapping_to_xml


# def git(registry, xml_parent, data):
#     """yaml: git
#     Git branch source


def github(registry, xml_parent, data):
    """yaml: github
    Github branch source

    """
    xml_parent.attrib['class'] = 'org.jenkinsci.plugins.github_branch_source.' \
                                 'GitHubSCMSource'
    xml_parent.attrib['plugin'] = 'github-branch-source'

    credentials_id = data.get('credentials-id', None)
    if credentials_id is not None:
        XML.SubElement(xml_parent, 'credentialsId').text = credentials_id

    XML.SubElement(xml_parent, 'repoOwner').text = data['owner']
    XML.SubElement(xml_parent, 'repository').text = data['repository']

    behaviors = data.get('behaviors', None)
    if behaviors is not None:
        traits = XML.SubElement(xml_parent, 'traits')
        for behavior, behavior_data in behaviors.items():
            add_behavior(behavior, behavior_data, traits)


def add_behavior(behavior, behavior_data, traits):
    behavior_data = {} if behavior_data is None else behavior_data
    behavior_handlers = {
        'discover-branches': add_discover_branches_trait,
        'discover-pull-requests-from-origin': add_pull_requests_from_origin,
        'discover-pull-requests-from-forks': add_pull_requests_from_forks,
        'filter-by-name-with-wildcards': filter_by_name_with_wildcards_trait
    }

    if behavior in behavior_handlers:
        handler = behavior_handlers[behavior]
    else:
        raise InvalidAttributeError(
            'behaviors',
            behavior,
            behavior_handlers.keys()
        )
    handler(behavior_data, traits)


def add_discover_branches_trait(behavior_data, traits):
    trait = XML.SubElement(traits, '%s.BranchDiscoveryTrait' % gbs_prefix())

    options = {
        'exclude-branches-filed-as-prs': 1,
        'only-branches-filed-as-prs': 2,
        'all': 3
    }
    mapping = [
        ('strategy', 'strategyId', 'exclude-branches-filed-as-prs', options)
    ]
    convert_mapping_to_xml(trait, behavior_data, mapping, fail_required=True)


def add_pull_requests_from_origin(behavior_data, traits):
    trait = XML.SubElement(
        traits,
        '%s.OriginPullRequestDiscoveryTrait' % gbs_prefix()
    )

    add_pull_request_discovery_strategy(behavior_data, trait)


def add_pull_requests_from_forks(behavior_data, traits):
    trait = XML.SubElement(
        traits,
        '%s.ForkPullRequestDiscoveryTrait' % gbs_prefix()
    )

    add_pull_request_discovery_strategy(behavior_data, trait)
    trait_prefix = 'org.jenkinsci.plugins.github_branch_source.' \
                   'ForkPullRequestDiscoveryTrait$'
    mapping = {
        'contributors': trait_prefix + 'TrustContributors',
        'everyone': trait_prefix + 'TrustEveryone',
        'admins-and-writers': trait_prefix + 'TrustPermission',
        'nobody': trait_prefix + 'TrustNobody'
    }

    trait_key = behavior_data.get('trust', 'contributors')
    if trait_key not in mapping.keys():
        raise InvalidAttributeError('trust', trait_key, mapping.keys())

    XML.SubElement(trait, 'trust', {'class': mapping[trait_key]})


def gbs_prefix():
    return 'org.jenkinsci.plugins.github__branch__source'


def add_pull_request_discovery_strategy(behavior_data, trait):
    mapping = [(
        'strategy',
        'strategyId',
        'merge-prs-with-current-target-branch-revision',
        {
            'merge-prs-with-current-target-branch-revision': 1,
            'use-current-pr-revision': 2,
            'both-current-pr-and-merge-with-target-branch-revision': 3
        }
    )]
    convert_mapping_to_xml(trait, behavior_data, mapping, fail_required=True)


def filter_by_name_with_wildcards_trait(behavior_data, traits):
    trait = XML.SubElement(
        traits,
        'jenkins.scm.impl.trait.WildcardSCMHeadFilterTrait',
        {'plugin': 'scm-api'}
    )

    mapping = [
        ('include', 'includes', '*'),
        ('exclude', 'excludes', ''),
    ]
    convert_mapping_to_xml(trait, behavior_data, mapping)


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
            source_xml = XML.SubElement(branch_source, 'source')
            self.registry.dispatch('branch-source', source_xml, source)
            source_data = next(iter(source.values()))
            add_property_strategy(branch_source, source_data)

        XML.SubElement(
            sources,
            'owner',
            {
                'class': mb_class,
                'reference': '../..'
            }
        )


def add_property_strategy(xml_parent, data):
    # I'm not implementing this now,
    # but this is where a non-default property strategy would be set up.

    properties = data.get('properties', [])
    strategy_xml = XML.SubElement(
        xml_parent,
        'strategy',
        {'class': 'jenkins.branch.DefaultBranchPropertyStrategy'}
    )
    class_name = 'java.util.Arrays$ArrayList' if properties else 'empty-list'
    properties_xml = XML.SubElement(
        strategy_xml,
        'properties',
        {'class': class_name}
    )

    for _property in properties:
        element = XML.SubElement(
            properties_xml,
            'a',
            {'class': 'jenkins.branch.BranchProperty-array'}
        )
        XML.SubElement(element, to_branch_property(_property, 'properties'))


def to_branch_property(_property, attribute_name):
    mapping = {
        'suppress-automatic-scm-triggering':
            'jenkins.branch.NoTriggerBranchProperty'
    }
    if _property in mapping.keys():
        return mapping[_property]
    else:
        raise InvalidAttributeError(attribute_name, _property, mapping.keys())
