---
published: true
title: Mellanox Openstack status update
layout: post
tags: [mellanox]
categories: [post]
---
This IBM challenge is to develop a Chef cookbook that supports the Mellanox Openstack plugin on their CloudX platform.

According to Mellanox, it brings the following benefits to the openstack.
Mellanox provides a cost-effective and scalable infrastructure that consolidates network and storage to an efficient fabric.
It delivers the best application performance with hardware-based acceleration for messaging, network traffic, and storage.
The APIs provided by Mellanox are easy to manage and are standardized. It also sports native integration with Openstack Quantum and Cinder provisioning APIs
They provide tenant and application security and isolation, and end-to-end hardware based traffic isolation and security filtering.

Our plan is to utilize the mellanox-openstack puppet module, and use it’s behavior as a baseline to develop a cookbook that integrates with the other openstack-cookbooks in stackforge. We plan to contribute necessary documentation and tests recommended by chef to ensure that it is easily deployable.

The puppet module contained four semi-independent major parts. These are are compute, which take care of provisioning compute nodes, storage, which handles provisioning storage nodes, network handling networking resources, and controller for integration between these.

We have completed an initial analysis of the all the four puppet modules. For each of these modules, we have developed chef equivalents, either using pre-existing openstack-cookbooks where possible, or implementing the functionality on our own. We are at a point where we start the integration of these different recipes, and verifying that our solution works.

Our plan forward is to first get the original puppet module running which can then serve as a useful example of the behavior of the system. Next, we will bring up each of the compute, network, storage and controller instances, and verify that the packages, configuration files and services are installed and started as expected. We will also be writing unit tests at this point to ensure that components work individually. Finally, we plan to combine them together, and verify that they work as expected as a complete system. We will also write the integration tests to ensure that this is as expected.
