# -*- coding: utf-8 -*-
#
# Based on jenkins_jobs/modules/project_pipeline.py by
# Copyright (C) 2016 Mirantis, Inc.
#
# The above (project_pipeline.py) was based on
# jenkins_jobs/modules/project_workflow.py by
# Copyright (C) 2015 David Caro <david@dcaro.es>
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
The Multibranch Pipeline Project module handles creating
Multibranch Jenkins Pipeline projects.
You may specify ``multibranch-pipeline`` in the ``project-type`` attribute of
the :ref:`Job` definition.


"""
import xml.etree.ElementTree as XML

import jenkins_jobs.modules.base


class MultibranchPipeline(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        mb_prefix = 'org.jenkinsci.plugins.workflow.multibranch.'
        xml_parent = XML.Element(
            mb_prefix + 'WorkflowMultiBranchProject',
            {'plugin': 'workflow-multibranch'}
        )

        factory_xml = XML.SubElement(
            xml_parent,
            'factory',
            {'class': mb_prefix + 'WorkflowBranchProjectFactory'}
        )
        XML.SubElement(
            factory_xml,
            'owner',
            {
                'class': mb_prefix + 'WorkflowMultiBranchProject',
                'reference': '../..'
            }
        )

        script_path = data.get('script-path', 'Jenkinsfile')
        XML.SubElement(factory_xml, 'scriptPath').text = script_path

        return xml_parent
