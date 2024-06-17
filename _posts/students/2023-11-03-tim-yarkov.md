---
layout: post
categories : student
tagline: "."
tags : [student timyarkov 2023]
e: Increasing the Breadth and Accuracy of Build System Detection for Supply Chain Security Analysis
---

#### Honours Thesis

Increasing the Breadth and Accuracy of Build System Detection for Supply Chain Security Analysis

**By Tim Yarkov**

Supervised by:   Rahul Gopinath, Behnaz Hassanshani, Xi Wu, Yash Shirvastava (Nominal)

**Acknowledgements**

Trong Nhan Mai, Paddy Krishnan and the rest of Oracle Labs

#### Abstract

Modern software projects are often built upon a multitude of dependencies to other projects, both direct and indirect; on average, 445 external open-source libraries or artifacts, as well as more closed-source ones (1). Manual verification of the security of such projects is a time consuming and error-prone process, and attack vectors can be opened very easily when improper processes are followed throughout the supply chain. SLSA (Supply-chain Levels for Software Artifacts) is a specification that standardises supply chain security practices for projects to help give guarantees to consumers that the proper security steps have been taken by dependency producers. Oracle Labs’ Macaron project analyses repositories for their conformance to SLSA via a variety of checks. This analysis has limitations in breadth and accuracy though, particularly in relation to analysis of build tools. Support for common tooling like NPM, Yarn, Go and Docker is missing, and Macaron cannot analyse repositories with multiple build tools. This project seeks to implement such support, extending Macaron’s analysis capabilities to more real-world situations, for example. The results of this project show that given a dataset of 76 repositories, breadth of detection improved by 6.42% overall, and 21.99% for repositories using the new tools specifically, and accuracy improved by 9.59% overall, and 16.21% for repositories using the new tools specifically.


