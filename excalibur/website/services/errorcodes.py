class ErrorCodes():
    user = {
        'success': {
            'status': 'success',
            'result': [0, 'Successfully completed operation.']
        },
        'invalidOrMissingParameters': {
            'status': 'failed',
            'result': [1, 'Invalid or missing parameters.']
        },
        'userNotAuthorized': {
            'status': 'failed',
            'result': [2, 'The User is not authorized for this operation.']
        },
        'userTokenExpired': {
            'status':
            'failed',
            'result': [
                3,
                'The provided UserToken has expired. Refresh your session and try again.'
            ]
        },
        'invalidId': {
            'status': 'failed',
            'result': [10, 'The given ID is invalid.']
        },
        'userNotAuthorizedForRole': {
            'status':
            'failed',
            'result':
            [10, 'This User is not authorized to instantiate the given Role.']
        },
        'invalidVirtueId': {
            'status': 'failed',
            'result': [10, 'The given Virtue ID is invalid.']
        },
        'invalidCredentials': {
            'status': 'failed',
            'result':
            [11, 'Credentials are not valid for the indicated User.']
        },
        'virtueAlreadyExistsForRole': {
            'status':
            'failed',
            'result': [
                11,
                'A Virtue already exists for the given User and the given Role.'
            ]
        },
        'virtueAlreadyLaunched': {
            'status': 'failed',
            'result': [11, 'The indicated Virtue has already been launched.']
        },
        'virtueAlreadyStopped': {
            'status': 'failed',
            'result': [11, 'The indicated Virtue is already stopped.']
        },
        'virtueNotStopped': {
            'status':
            'failed',
            'result': [
                11,
                'The indicated Virtue is not stopped. Please stop it and try again.'
            ]
        },
        'invalidApplicationId': {
            'status': 'failed',
            'result': [11, 'The given Application ID is invalid.']
        },
        'userAlreadyLoggedIn': {
            'status':
            'failed',
            'result': [
                12,
                'The given User is already logged into another session. This response is '
                +
                'only given if the forceLogoutOfOtherSessions flag was false.'
            ]
        },
        'invalidRoleId': {
            'status': 'failed',
            'result': [12, 'The given Role ID is not valid.']
        },
        'virtueStateCannotBeLaunched': {
            'status':
            'failed',
            'result': [
                12,
                'The indicated Virtue is in a state where it cannot be launched. '
                + 'Check the current Virtue state and take necessary actions.'
            ]
        },
        'virtueStateCannotBeStopped': {
            'status':
            'failed',
            'result': [
                12,
                'The indicated Virtue is in a state where it cannot be stopped. '
                + 'Check the current Virtue state and take necessary actions.'
            ]
        },
        'applicationNotInVirtue': {
            'status': 'failed',
            'result':
            [12, 'The indicated Application is not in this Virtue/Role.']
        },
        'userDoesntExist': {
            'status': 'failed',
            'result': [13, 'The given User does not exist in the system.']
        },
        'cantEnableTransducers': {
            'status':
            'failed',
            'result': [
                13,
                'One of the configured Transducers can\'t be enabled on this Virtue.'
            ]
        },
        'cantLaunchEnabledTransducers': {
            'status':
            'failed',
            'result':
            [13, 'One or more of the enabled Transducers can\'t be launched.']
        },
        'virtueNotRunning': {
            'status':
            'failed',
            'result': [
                13,
                'The Virtue holding this Application is not running. Launch it and try again.'
            ]
        },
        'applicationAlreadyLaunched': {
            'status': 'failed',
            'result':
            [14, 'The indicated Application has already been launched.']
        },
        'applicationAlreadyStopped': {
            'status': 'failed',
            'result':
            [14, 'The indicated Application is already stopped.']
        },
        'resourceCreationError': {
            'status':
            'failed',
            'result': [
                100,
                'There was an error creating the resources for the Virtue. Check '
                + 'user messages and server logs.'
            ]
        },
        'serverLaunchError': {
            'status':
            'failed',
            'result': [
                100,
                'There was an unanticipated server error launched the indicated Virtue. '
                + 'Check user messages for more information.'
            ]
        },
        'serverStopError': {
            'status':
            'failed',
            'result': [
                100,
                'There was an unanticipated server error stopping the indicated Virtue. '
                + 'Check user messages and server logs for more information.'
            ]
        },
        'serverDestroyError': {
            'status':
            'failed',
            'result': [
                100,
                'There was an unanticipated server error destroying the indicated Virtue.'
                + 'Check user messages and server logs for more information.'
            ]
        },
        'notImplemented': {
            'status': 'failed',
            'result': [254, 'This function has not been implemented.']
        },
        'unspecifiedError': {
            'status':
            'failed',
            'result': [
                255,
                'An otherwise unspecified error. Check user messages and/or error logs '
                + 'for more information.'
            ]
        }
    }

    admin = {
        'success': {
            'status': 'success',
            'result': [0, 'Successfully completed operation.']
        },
        'invalidOrMissingParameters': {
            'status': 'failed',
            'result': [1, 'Invalid or missing parameters']
        },
        'userNotAuthorized': {
            'status': 'failed',
            'result': [2, 'The User is not authorized for this operation.']
        },
        'userTokenExpired': {
            'status':
            'failed',
            'result': [
                3,
                'The provided UserToken has expired. Refresh your session and try again.'
            ]
        },
        'invalidId': {
            'status': 'failed',
            'result': [10, 'The given ID is invalid.']
        },
        'invalidRoleId': {
            'status': 'failed',
            'result': [11, 'The given Role ID is invalid.']
        },
        'invalidVirtueId': {
            'status': 'failed',
            'result': [11, 'The given Virtue ID is invalid.']
        },
        'invalidVirtueState': {
            'status':
            'failed',
            'result': [
                12,
                'The given Virtue is not in a proper state to perform operation'
            ]
        },
        'invalidRoleState': {
            'status': 'failed',
            'result': [
                12,
                'The given Role is not in a proper state to perform operation'
            ]
        },
        'invalidCredentials': {
            'status':
            'failed',
            'result': [
                13,
                'You don\'t have the correct credentials to attach this resource.'
            ]
        },
        'invalidFormat': {
            'status':
            'failed',
            'result': [
                10,
                'The implementation does not understand the format of this object.'
            ]
        },
        'invalidApplicationId': {
            'status': 'failed',
            'result': [11, 'One or more of the Application Ids is invalid.']
        },
        'invalidResourceId': {
            'status': 'failed',
            'result': [12, 'One or more Resource IDs is invalid.']
        },
        'invalidTransducerId': {
            'status': 'failed',
            'result': [13, 'One or more of the Transducer IDs is invalid.']
        },
        'uniqueConstraintViolation': {
            'status':
            'failed',
            'result': [
                14,
                'This Role cannot be created because it violates a unique constraint.'
            ]
        },
        'NoApplicationId': {
            'status': 'failed',
            'result': [15, 'No Application Id specified in the role, One or more Application Ids are required.']
        },
        'storageError': {
            'status': 'failed',
            'result': [10, 'There was an error trying to store the object.']
        },
        'invalidUsername': {
            'status': 'failed',
            'result':
            [10, 'The given username is invalid, or doesn\'t exist.']
        },
        'userNotLoggedIn': {
            'status': 'failed',
            'result': [10, 'The indicated User is not currently logged in.']
        },
        'userAlreadyAuthorized': {
            'status': 'failed',
            'result': [12, 'The User is already authorized for that Role.']
        },
        'userNotAlreadyAuthorized': {
            'status': 'failed',
            'result': [12, 'The User is not authorized for that Role']
        },
        'userUsingVirtue': {
            'status': 'failed',
            'result': [
                13,
                'The indicated user is logged in and currently using a Virtue with the '
                + 'indicated Role. Force their logout and try again.'
            ]
        },
        'imageNotFound': {
            'status': 'failed',
            'result': [
                16,
                'A matching Docker image was not found for this application.'
            ]
        },
        'virtueUsingRole': {
            'status': 'failed',
            'result': [
                14,
                'A virtue exists which is using the specified role. '
                + 'Destroy the virtue before attempting to destroy the role.'
            ]
        },
        'virtueUsingResource': {
            'status': 'failed',
            'result': [
                14,
                'A virtue exists which is using the specified resource. '
                + 'Detach the resource before attempting to destroy.'
            ]
        },
        'userUsingRole': {
            'status': 'failed',
            'result': [
                15,
                'A user exists which is authorized to use the specified role. '
                + 'Unauthorize the user for the role before attempting to '
                + 'destroy the role.'
            ]
        },
        'roleDestroyError': {
            'status': 'failed',
            'result': [
                100,
                'There was an unanticipated error destroying the indicated Role.'
                + 'Check user messages and server logs for more information.'
            ]
        },
        'cantAttach': {
            'status': 'failed',
            'result': [100, 'Can\'t attach to the Resource']
        },
        'cantDetach': {
            'status': 'failed',
            'result': [100, 'Can\'t detach the Resource']
        },
        'notImplemented': {
            'status': 'failed',
            'result': [254, 'This function has not been implemented.']
        },
        'unspecifiedError': {
            'status':
            'failed',
            'result': [
                255,
                'An otherwise-unspecified error. Check user messages and/or error logs.'
            ]
        }
    }

    security = {
        'success': {
            'status': 'success',
            'result': [0, 'Successfully completed operation.']
        },
        'invalidOrMissingParameters': {
            'status': 'failed',
            'result': [1, 'Invalid or missing parameters']
        },
        'userNotAuthorized': {
            'status': 'failed',
            'result': [2, 'The User is not authorized for this operation.']
        },
        'userTokenExpired': {
            'status':
            'failed',
            'result': [
                3,
                'The provided UserToken has expired. Refresh your session and try again.'
            ]
        },
        'invalidId': {
            'status': 'failed',
            'result': [10, 'The given ID is invalid.']
        },
        'invalidTransducerId': {
            'status': 'failed',
            'result': [10, 'The given Transducer ID is invalid.']
        },
        'invalidVirtueId': {
            'status': 'failed',
            'result': [11, 'The given Virtue ID is invalid.']
        },
        'virtueStateError': {
            'status':
            'failed',
            'result': [
                12,
                'The Virtue\'s current state prevents the Transducer from being enabled.'
            ]
        },
        'invalidConfigurationFormat': {
            'status':
            'failed',
            'result': [
                13,
                'The configuration provided cannot be understood by this implementation.'
            ]
        },
        'transducerNotEnabled': {
            'status':
            'failed',
            'result': [
                13,
                'The indicated Transducer is not enabled in the indicated Virtue.'
            ]
        },
        'notImplemented': {
            'status': 'failed',
            'result': [254, 'This function has not been implemented.']
        },
        'unspecifiedError': {
            'status':
            'failed',
            'result': [
                255,
                'An otherwise unspecified error. Check user messages and/or error logs '
                + 'for more information.'
            ]
        }
    }
