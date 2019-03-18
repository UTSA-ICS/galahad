# Galahad Test Plan

To test Galahad, we need to demonstrate everything that is listed on the Wiki at https://github.com/starlab-io/galahad/wiki/User-Case-Testing-Guide (copied below). This covers a large set of day-to-day functionality for the Galahad system, but we're not sure how much of it actually works, what the workflow will be for each process, and so forth. Our job is to take these test cases apart, figure out what needs to happen, document the steps we take, and then record the results. Many of these tests are NOT functional tests, so it will be difficult to automate the tests.

Assumptions:

- Galahad is installed on AWS
- Galahad is configured with at least one administrative user and at least one non-admin user
- Galahad has a small number of applications available for creating roles
    - Firefox
    - Thunderbird
    - Terminal
    - One Windows application (which one?)

Proposed process:

- Triage the tests: figure out which tests we know how to do and which ones need more information
- Per test item:
    - Using a standardized template, record the test preconditions, the steps taken to perform the test, the expected results, and the actual results
    - Record test results in a living document / wiki page (prefer document in repository)
    - Record any issues discovered as issues in GitHub
    - Work with rest of Galahad team to determine correct assignee for issue
- Check in the current test results

## Wiki List of Test Cases

Use Case Exercise: Please exercise the below use cases noting any gaps in functionality or performance as issues. Attempt to correct any issues identified.

I (Alex) assigned each test case a t-shirt sized estimate of difficulty, based on what I know of the system. Let's discuss.

- 1.0. Admin Use Cases:
    - 1.1 [?] With Galahad 'cloud-formed', deploy a collection of valors. Do some scalability testing and get a sense of performance, i.e., time to deploy, do all valors show up on BFT, etc.
    - 1.2 [S] Using the Admin CLI, retrieve a list of roles. What data is provided when we do this?
    - 1.3 [S] Using the Admin CLI, retrieve a list of users. What data is provided when we do this?
    - 1.4 [M] Using the Admin CLI, create a new role. Test with linux and windows apps, test different combinations of apps, etc.
    - 1.5 [L] Add a new user in Galahad, i.e., consider the case where a new person shows up and they must then use Galahad. This particular use case is focused on adding to AD, Ldap, etc. (the stuff before creating virtues) such that the Admin API can be used in the future. What happens when we try and add an existing user?
    - 1.6 [M] Using the Admin CLI, create roles for or assign existing roles to a user present in Galahad (step above). Is this intuitive? Verify the user can then login to Canvas and start virtues (not roles).
    - 1.7 [L] Build an app that will eventually be used to create a role. Is this something in Admin CLI or not? If not, does it need to be? What’s our plan for this when for the eval?
    - 1.8 [S] Using the Admin CLI, stop a given user’s virtue.
    - 1.9 [S] Using the Admin CLI, migrate a given user’s virtue. Can we also migrate all virtues on a given valor?
    - 1.10 [S] Using the Admin CLI, bring down a valor? Test different scenarios for when this might happen, i.e., the valor has no virtues, the valor has one virtue, the valor has several virtues, etc.
    - 1.11 [L] Package a user’s roles. Do we have to do this one role at a time or can we package them all at one time?
- 2.0. Security Use Cases:
    - 2.1 [M] Using the Admin CLI, set the security configuration for all valors and virtues, i.e., this configuration applies to all running virtues and valors. This includes setting the migration on/off and frequency and introspection on/off and frequency. Get a sense for how much effort it takes an admin to initially set and forget the security configuration. We don’t want the admin to have to set security each time a new virtue starts.
    - 2.2 [M] Using the Admin CLI, change the security configuration for a single valor and virtue. Can the Admin get a list of configurations that can be changed to help inform his decision? This includes setting the migration time.
    - 2.3 [M] Using the Admin CLI, set the logging configuration for all valors and virtues, i.e., this configuration applies to all running virtues and valors.
    - 2.4 [S] Using the Admin CLI, change the logging configuration for a single valor and virtue. Can the Admin get a list of configurations that can be changed to help inform his decision?
- 3.0. Typical User Use Cases:
    - 3.1 [S] User logins in and immediately sees available virtues in Canvas.
    - 3.2 [L] User can start all virtues in their dock, what’s the performance like? What are the impacts of migration? Use the apps as you investigate.
    - 3.3 [M] User can save a file to a file share
    - 3.4 [L] User can open a file from an app using a file share
    - 3.5 [M] User can copy contents from one virtue to another virtue.
    - 3.6 [L] User can print
    - 3.7 [S] User can use an email client in a virtue without having to enter the settings each time.
    - 3.8 [S] User can immediately close an application then open it again
    - 3.9 [S] Virtues with no apps interacting with the user are stopped, paused, destroyed??
