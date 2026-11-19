Refer to the README markdown files for the respective section's .md file.

This readme is intended to state how this program follows the clean architecture, such that the source code dependencies only point inward.

Container.py (in WI29_Server) wires all of these here:

    1A. Backend interface for routing

    1B. Infrastructures (DBs and OAuth) for implementing ports

    2. Application (function or step, which will check the domain rules)

    3. Domain (rules and data - determines what is valid)

Where Container.py -> 1A and 1B -> 2 -> 3
such that a route (interface) calls a function (application), which uses some (domain) rules to call a port (for the infrastructure)


