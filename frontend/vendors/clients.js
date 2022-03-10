import { POST } from '../common/ajax';


var ADD_MODAL = '.clients__add-modal';
var VERIFY_MODAL = '.clients__verify-modal';
var OVERLAY = ".black-overlay";


function getProofUrl(vendorId, referenceId) {
  return '/vendors/' + vendorId + '/' + referenceId + '/invoice/';
}

function getEmailUrl(referenceId) {
  return '/vendors/' + referenceId + '/clients/reference/update/';
}

function getVendorId() {
  return $('.data-for-frontend .clients__vendor-id').val();
}

function getAddClientUrl() {
  return $('.clients__add-client-url').val();
}

function setVerifyModal(name, logoSrc, vendorId, referenceId) {
  var modal = $(VERIFY_MODAL);
  $(OVERLAY).show();

  modal.show();
  modal.css({top: '400px'});
  window.scrollTo(0, 100);

  var headerTag = modal.find('.modal-header'),
    headerTitle = 'Why should I verify ' + name + '?',
    logo = modal.find('.clients__modal-logo'),
    emailBtn = modal.find('.clients__verify-email').first(),
    proofBtn = modal.find('.clients__verify-proof').first();

  headerTag.text(headerTitle);

  logo.attr('src', logoSrc);
  logo.attr('alter', name);
  emailBtn.attr('href', getEmailUrl(referenceId));
  proofBtn.attr('href', getProofUrl(vendorId, referenceId));
}

function setUpAddClient () {
  var url = getAddClientUrl(),
    addClientWindow = $(ADD_MODAL),
    overlay = $(OVERLAY),
    verifyClientWindow = $(VERIFY_MODAL),
    vendorId = getVendorId();

  $('.clients__btn-add').on('click', function () {
    addClientWindow.show();
    overlay.show();
  })

  $('.clients__add-form').on('submit', function (e, form) {
    e.preventDefault();
    $('.clients__errors').text('');
    var data = $(this).serialize();
    console.log(data);
    POST(url, data)
      .then(function (res) {
        const { name, logo, reference_id } = res;
        addClientWindow.hide();
        setTimeout(function () {
          setVerifyModal(name, logo, vendorId, reference_id);
        }, 1000)
      })
      .fail(function (res) {
        $('.clients__errors').text('Fix errors in form');
      })
  })
}

export default function initialize() {
  var vendorId = getVendorId();

  setUpAddClient();

  $('.black-overlay, .cancel-button, .clients__verify-email, ' +
    '.clients__verify-proof').on('click', function () {
    $(".popup").hide();
    $(".black-overlay").hide();
  })

  $('.clients__btn-verify').on('click', function (event) {
    var target = $(event.target),
      clientRow = target.closest('.clients__row'),
      clientName = clientRow.find('.clients__name').text(),
      clientLogo = clientRow.find('.clients__logo').attr('src'),
      referenceId = clientRow.attr('id').replace(/^client-reference-/, '');

    setVerifyModal(clientName, clientLogo, vendorId, referenceId);
  });

  $(".clients__add-form").validate({
    rules: {
      "client_form-client": {
        required: true,
        minlength: 1
      }
    }
  });
}