class ErrorCodes = {
    user = {
        'success': [0, 'Successfully completed operation.'],
        'invalidOrMissingParameters': [1, 'Invalid or missing parameters.'],
        'userNotAuthorized': [2, 'The User is not authorized for this operation.'],
        'userTokenExpired': [3, 'The provided UserToken has expired. Refresh your session and try again.'],
        'invalidId': [10, 'The given ID is invalid.'],
        'userNotAuthorizedForRole': [10, 'This User is not authorized to instantiate the given Role.'],
        'invalidVirtueId': [10, 'The given Virtue ID is invalid.'],
        'invalidCredentials': [11, 'Credentials are not valid for the indicated User.'],
        'virtueAlreadyExistsForRole': [11, 'A Virtue already exists for the given User and the given Role.'],
        'virtueAlreadyLaunched': [11, 'The indicated Virtue has already been launched.'],
        'virtueAlreadyStopped': [11, 'The indicated Virtue is already stopped.'],
        'virtueNotStopped': [11, 'The indicated Virtue is not stopped. Please stop it and try again.'],
        'invalidApplicationID': [11, 'The given Application ID is invalid.'],
        'userAlreadyLoggedIn': [12, 'The given User is already logged into another session. This response is \
                only given if the forceLogoutOfOtherSessions flag was false.'],
        'invalidRoleId': [12, 'The given Role ID is not valid.'],
        'virtueStateCannotBeLaunched': [12, 'The indicated Virtue is in a state where it cannot be launched. \
                Check the current Virtue state and take necessary actions.'],
        'virtueStateCannotBeStopped': [12, 'The indicated Virtue is in a state where it cannot be stopped. \
                Check the current Virtue state and take necessary actions.'],
        'applicationNotInVirtue': [12, 'The indicated Application is not in this Virtue/Role.'],
        'userDoesntExist': [13, 'The given User does not exist in the system.'],
        'cantEnableTransducers': [13, 'One of the configured Transducers can\'t be enabled on this Virtue.'],
        'cantLaunchEnabledTransducers': [13, 'One or more of the enabled Transducers can\'t be launched.'],
        'virtueNotRunning': [13, 'The Virtue holding this Application is not running. Launch it and try again.'],
        'applicationAlreadyLaunched': [14, 'The indicated Application has already been launched.'],
        'resourceCreationError': [100, 'There was an error creating the resources for the Virtue. Check \
                user messages and server logs.'],
        'serverLaunchError': [100, 'There was an unanticipated server error launched the indicated Virtue. \
                Check user messages for more information.'],
        'serverStopError': [100, 'There was an unanticipated server error stopping the indicated Virtue. \
                Check user messages and server logs for more information.'],
        'serverDestroyError': [100, 'There was an unanticipated server error destroying the indicated Virtue. \
                Check user messages and server logs for more information.'],
        'notImplemented': [254, 'This function has not been implemented.'],
        'unspecifiedError': [255, 'An otherwise unspecified error. Check user messages and/or error logs \
                for more information.']
    }
