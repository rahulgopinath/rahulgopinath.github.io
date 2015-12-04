---
published: true
title: Mellanox cookbook status update
layout: post
tags: [mellanox]
categories: [post]
---
Our challenge was to develop a Mellanox openstack  chef plugin for the Mellanox CloudX platform. According to Mellanox, it brings the following benefits to the openstack.

Mellanox provides a cost-effective and scalable infrastructure that consolidates network and storage to an efficient fabric.
It delivers the best application performance with hardware-based acceleration for messaging, network traffic, and storage.
The APIs provided by Mellanox are easy to manage and are standardized. It also sports native integration with Openstack Quantum and Cinder provisioning APIs
They provide tenant and application security and isolation, and end-to-end hardware based traffic isolation and security filtering.

We started with the Mellanox puppet module as a base, and used the mellanox documentation to come up with an up-to-date chef plugin for managing mellanox infrastructure. We planned for three phases. For phase I, we targeted mellanox over ethernet, for phase II our target was Mellanox over infiniband, and for Phase III, we utilize Unified Fabric Manager for Infiniband.

Phase I includes complete implementation of  Neutron Server nodes,  Compute Nodes, Network Nodes and Cinder Nodes.

Phase I has been added as a pull request to OSUOSL Mellanox cookbook. It includes configuration changes, but needs to be validated on hardware. It also includes updates to sister projects such as network and block storage, which are added as pull requests to the respective projects.

For phase II we target the subnet Manager node using Open SM. It includes updates to Neutron, Compute and Network nodes along with Linux Bridge recipes

For Phase III, we plan to  update SM Node with Unified Fabric Manager

The work required for Phase II and III has been scoped out and documented in our project wiki. Phase I has been completed
