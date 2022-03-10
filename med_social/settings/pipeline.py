import os

DEBUG = os.getenv('DEBUG', 'False') == 'True'

PIPELINE = {
    'PIPELINE_ENABLED': True,
    'CSS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'JS_COMPRESSOR': 'pipeline.compressors.uglifyjs.UglifyJSCompressor',
    'BROWSERIFY_ARGUMENTS': '',
    'COMPILERS': (
      'pipeline_browserify.compiler.BrowserifyCompiler',
      'react.utils.pipeline.JSXCompiler',
      'pipeline.compilers.less.LessCompiler',
    ),
    'MIMETYPES': (
        ('text/javascript', '.js'),
    ),
    'STYLESHEETS': {
        'libs': {
            'source_filenames': (
              'less/libs.less',
              'css/libs/intlTelInput.css',
              'css/libs/geosuggest.css',
            ),
            'output_filename': 'css/libs.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'libs_blue': {
            'source_filenames': (
              'less/libs_blue.less',
              'css/libs/intlTelInput.css',
            ),
            'output_filename': 'css/libs_blue.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'app': {
            'source_filenames': (
              'less/app/app.less',
            ),
            'output_filename': 'css/app.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'app_blue': {
            'source_filenames': (
              'less/app/app_blue.less',
            ),
            'output_filename': 'css/app_blue.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'public': {
            # Doesn't need libs bundle to work as it includes it's own requirements
            'source_filenames': (
              'less/app/public.less',
            ),
            'output_filename': 'css/public.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'landing': {
            # Doesn't need libs bundle to work as it includes it's own requirements
            'source_filenames': (
              'less/landing.less',
            ),
            'output_filename': 'css/landing.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'public-landing': {
            # Doesn't need libs bundle to work as it includes it's own requirements
            'source_filenames': (
              'less/app/public-landing-bundle.less',
            ),
            'output_filename': 'css/public-landing-bundle.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'hero': {
            # Doesn't need libs bundle to work as it includes it's own requirements
            'source_filenames': (
              'less/hero.less',
            ),
            'output_filename': 'css/hero.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
        'blog': {
            'source_filenames': (
              'less/app/blog.less',
            ),
            'output_filename': 'css/blog.css',
            'extra_context': {
                'media': 'screen,projection',
            },
        },
    },
    'JAVASCRIPT': {
        'app-ng': {
            'source_filenames' : (
              'jsx/app.browserify.js',
            ),
            'output_filename': 'js/app.browserified.js',
        },
        'app-legacy': {
            'source_filenames' : (
              'js/app.js',
              'js/app/notification.js',
            ),
            'output_filename': 'js/app.legacy-dependencies.js',
        },
        'libs': {
            'source_filenames': (
              # polyfills
              'js/polyfills/es5-shim.min.js',
              'js/polyfills/es5-sham.min.js',
              'js/polyfills/console.js',

              # libraries

              'js/lib/jquery-1.10.2.min.js',
              'js/lib/jquery-migrate-1.2.1.min.js',
              'js/lib/modernizr.custom.js',
              'js/lib/jquery.pjaxr.min.js',
              'js/lib/jquery.rest.min.js',
              'js/lib/jquery.sortable.min.js',
              'js/lib/lodash.min.js',
              'js/lib/retina.js',
              'js/lib/deparam.min.js',
              'js/lib/bootstrap.min.js',
              'js/lib/vendor/bootbox.js',
              'js/lib/pickadate/picker.js',
              'js/lib/pickadate/picker.date.js',
              'js/lib/minwidth.js',
              'js/lib/drop.min.js',
              'js/lib/messenger.min.js',
              'js/lib/messenger-theme-flat.js',
              'colourfield/jscolor/jscolor.js',
              'js/lib/sifter.min.js',
              'js/lib/microplugin.min.js',
              'js/lib/selectize.js',
              'js/lib/bootstrap-maxlength.min.js',
              'js/lib/jquery.autosize.min.js',
              'js/lib/parsley.min.js',
              'js/lib/spin.min.js',
              'js/lib/jquery.spin.js',
              'js/lib/jquery.caret.min.js',
              'js/lib/jquery.atwho.min.js',
              'js/lib/jquery.deserialize.min.js',
              'js/lib/bootstrap-filestyle.min.js',
              'js/lib/switchery.min.js',
              'js/lib/inputmask/jquery.inputmask.js',
              'js/lib/inputmask/jquery.inputmask.regex.extensions.js',
              'js/lib/inputmask/jquery.inputmask.extensions.js',
              'js/lib/inputmask/jquery.inputmask.numeric.extensions.js',
              'js/lib/icheck.min.js',
              'js/lib/radiocheck.js',
              'js/lib/Chart.min.js',
              'js/lib/jquery.onepage-scroll.min.js',
              'js/lib/intlTelInput.min.js',
              'js/lib/humanize.js',
              'js/lib/google-places.js',
            ),
            'output_filename': 'js/libs.js',
        },
        'charts': {
            'source_filenames': (
                'js/lib/Chart.min.js',
                'js/app/charts/*.js',
            ),
            'output_filename': 'js/charts.js',
        },
        'app': {
            'source_filenames': (
              'js/app.js',
              'js/app/utils.js',
              'js/app/events.js',
              'js/app/router.js',
              'js/app/panels.js',
              'js/app/ajax.js',
              'js/app/UI.js',
              'js/app/links.js',
              'js/app/notification.js',
              'js/app/popovers.js',
              'js/app/partial-accordion.js',
              'js/app/inline-popovers.js',
              'js/app/tooltips.js',
              'js/app/buttons.js',
              'js/app/autocomplete.js',
              'js/app/tags.js',
              'js/app/dates.js',
              'js/app/forms.js',
              'js/app/filters.js',
              'js/app/sidebar.js',
              'js/app/modals.js',
              'js/app/quotes.js',
              'js/app/projects.js',
              'js/app/metric_list.js',
              'js/app/role_list.js',
              'js/app/category_list.js',
              'js/app/metric_form.js',
              'js/app/location_list.js',
              'js/app/reviews.js',
              'js/app/contact.js',
              'js/app/users.js',
              'js/app/vendors.js',
              'js/app/list.js',
              'js/app/profile.js',
              'js/app/responses.js',
              'js/app/staffing.js',
              'js/app/propose_resources.js',
              'js/app/activity.js',
              'js/app/checkout.js',
              'js/app/vendor_profile.js',
              'js/app/clients.js',
            ),
            'output_filename': 'js/application.js',
        },
        'profiles': {
            'source_filenames': (
                'js/profiles/*',
            ),
            'output_filename': 'js/profiles.js',
        },
        'legacy': {
            # To suppport IE8 like respond and other polyfills
            'source_filenames': (
              'js/polyfills/ie8.js',
              'js/polyfills/html5shiv.min.js',
              'js/lib/respond.min.js',
              'js/lib/pickadate/legacy.js',
              'js/lib/excanvas.min.js',
            ),
            'output_filename': 'js/legacy.js',
        },
        'onboarding': {
            'source_filenames': (
              'js/app/links.js',
              'js/onboarding/*.js',
            ),
            'output_filename': 'js/onboarding.js',
        },
        'landing': {
            'source_filenames': (
              'js/lib/jquery-1.10.2.min.js',
              'js/lib/jquery-migrate-1.2.1.min.js',
              'js/lib/jquery.pjaxr.min.js',
              'js/lib/lodash.min.js',
              'js/lib/bootstrap.min.js',
              'js/lib/retina.js',
              'js/lib/parsley.min.js',
              'js/landing/*',
            ),
            'output_filename': 'js/landing.js',
        }
    }
}
