---
layout: post
categories : student
tagline: "."
tags : [student kenzietano 2023]
e: Creating a DAP-Compatible Debug Adapter between Binaries and Debuggers.
---

#### 12 CP Research Thesis (BC)

Creating a DAP-Compatible Debug Adapter between Binaries and Debuggers.

**By Kenzie Tano**

Supervised by: Rahul Gopinath

#### Abstract

Software development involves cycles of coding, testing, and debugging. As software
ecosystems diversify and grow in complexity, there’s a pressing need for debugging
tools that can seamlessly interface with varying programs and binaries. Current
debuggers might not be equipped to adapt swiftly to these evolving environments.
To address this, this thesis explores the Debug Adapter Protocol (DAP). DAP aims
to standardize communication between development tools, IDEs, and various de-
buggers, enabling programmers to debug consistently across different environments
without delving deep into each debugger’s specifics.

To enable this, a tool called the Debug Adapter is required, which functions as a
pivotal intermediary that connects existing debuggers to various binaries or tools via
DAP. Given that expecting all existing debuggers to fully adopt DAP is unrealistic
due to the extensive modifications needed, the emphasis is on how DAP eases the
integration of new debuggers. This offers a unified platform for tools, like IDEs that
provide a UI element for end users, to communicate with different debuggers while
preserving extensibility.

DAP utilizes a JSON communication protocol that ensures adaptability in the
language used for the debug adapter’s implementation, addressing debugger-specific
nuances. Its high-level design abstracts complex debugger operations, yet the proto-
col guarantees that users can easily interact with the debugger via intuitive string-
based data structures.

This project enables communication between debuggers and binaries/programs
from languages such as C or Python. It delves into the challenges of designing
a debug adapter that bridges the gap between programs, binary executables, and
debuggers, all under the DAP framework. The ultimate goal is to enhance the
debugging process’s interoperability and efficiency, emphasizing the Debug Adapter
Protocol’s role in optimizing software debugging tools.
