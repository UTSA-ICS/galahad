# Test Template

This section provides a template that can be used to describe future tests. Please add a new fie to the appropriate directory (to keep things neat) and number it appropriately, and then fill in the test data below. Please end the file with a blank line so that it keeps the file concatenation happy when generating the overview documentation.

Start copying after this line.

## X.XX - Test Name

### Test Description

*Describe the test to be performed. Refer to the test plan for the numeric identifier.*

### Preconditions

*Describe any necessary preconditions for the test to execute. You can assume that the `cloud init` stage has just completed and that there is one admin user and one non-admin user created as part of that process. Other than that, make as few assumptions as possible.*

### Steps to Test

*Describe steps necessary to perform the test, in detail. For example, copy and paste the exact commands you used, or describe what needs to happen*

### Expected Result

*Describe what we expect to happen, including information about the time it takes for an operation to complete. Describe in terms of what we would see from the command line interface, the blue force tracker, and from the user's perspective.*

### Actual Result

*Describe what actually happens. Record the branch and version (treeish) of the repository you performed the test on. When re-tested after some major code change, add the result at that point to the writeup here. This will record what happens as the codebase evolves.*
