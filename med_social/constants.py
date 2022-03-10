class AvailabilityConstantsMixin(object):
    UNAVAILABLE = 1
    AVAILABLE_10 = 2
    AVAILABLE_20 = 3
    AVAILABLE_30 = 4
    AVAILABLE_FULLTIME = 5
    AVAILABILITY_CHOICES = (
        (UNAVAILABLE, 'unavailable',),
        (AVAILABLE_10, 'upto 10 hours/week',),
        (AVAILABLE_20, '10 - 20 hours/week',),
        (AVAILABLE_30, '20 - 30 hours/week',),
        (AVAILABLE_FULLTIME, 'full-time',),
    )


class OnboardingConstantsMixin(object):
    SETUP_PASSWORD_SET = 1
    SETUP_LINKEDIN_FETCH = 2
    SETUP_USER_PROFILE = 3
    SETUP_VENDOR_PROFILE = 4
    SETUP_INVITATIONS = 5
    # Welcome must be the last step.
    SETUP_WELCOME = 100
    SETUP_STEP_CHOICES = (
        (SETUP_PASSWORD_SET, "change_password"),
        (SETUP_LINKEDIN_FETCH, "fetch_linkedin"),
        (SETUP_USER_PROFILE, 'user_profile',),
        (SETUP_VENDOR_PROFILE, 'vendor_profile',),
        (SETUP_WELCOME, 'user_welcome',),
    )
    SETUP_STEPS_DICT = dict(SETUP_STEP_CHOICES)

    SETUP_STEPS_DEFAULT = [
        SETUP_PASSWORD_SET,
        SETUP_USER_PROFILE,
#         SETUP_WELCOME
    ]
    SETUP_STEPS_CLIENT = [
        SETUP_PASSWORD_SET,
        SETUP_USER_PROFILE,
#         SETUP_WELCOME
    ]
    SETUP_STEPS_FIRST_CLIENT = SETUP_STEPS_CLIENT

    SETUP_STEPS_VENDOR = [
        SETUP_PASSWORD_SET,
        SETUP_USER_PROFILE,
        SETUP_VENDOR_PROFILE,
#         SETUP_WELCOME
    ]

    SETUP_STEPS_FIRST_VENDOR = [
        SETUP_PASSWORD_SET,
        SETUP_USER_PROFILE,
        SETUP_VENDOR_PROFILE,
#         SETUP_WELCOME
    ]


class UserKindConstantsMixin(object):
    NONE = 0
    VENDOR = 1
    CONSULTANT = 2
    KIND_CHOICES = (
        (NONE, 'None',),
        (VENDOR, 'Vendor'),
        (CONSULTANT, 'Consultant'),
    )

class UserRoleConstantsMixin(object):
    NONE = 0
    EXECUTIVE = 1
    MANAGER = 2
    RELATION = 3

    ROLE_CHOICES = (
        (NONE, 'None',),
        (RELATION, 'Relations Personnel'),
        (MANAGER, 'Manager'),
        (EXECUTIVE, 'Executive Personnel'),
    )
