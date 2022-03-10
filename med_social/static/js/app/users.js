Messenger.options = {
    extraClasses: 'messenger-fixed messenger-on-bottom messenger-on-right',
    theme: 'flat',
};

_inExec.register({
  name: 'users',
  routes: ['^/u/\\d+/edit/$',
           '^/users/',
           '^/users/register/$',
           '^/users/invite/$',
           '^/u/\\d+/\\d+/$'],
  initialize: function($container){
    // Make BS load the remote modal content everytime it is initialized
    $('#userDeleteModal').on('hidden.bs.modal', function () {
      $(this).find('.modal-body').html('');
      var $div = $('<div></div>', {'class': 'spinner-holder'});
      $(this).find('.modal-body').append($div);
      var spinner = new Spinner({
          length: 10,
          radius: 15,
          hwaccel: true,
      }).spin($(this).find('.spinner-holder')[0]);
      $(this).removeData('bs.modal');
    });
    _inExec.modules.events.on('form:success#resend-invite-form', function(ev){
      var $form = $('#resend-invite-form');
      $form.parents('.modal').modal('hide');
      location.reload();

      var notif = window.Messenger().post({
        'showCloseButton': true,
        'type': 'success',
        'message': 'Invitation sent successfully',
        'hideAfter': 3,
      });

    });


    if(!$('#id_kind').is(":checked")) {
      $('#div_id_vendor').addClass('hide');
    }
    $('#id_kind').change(function() {
        
        if($(this).is(":checked")) {
          $('#div_id_vendor').removeClass('hide');
        }
        else{
          $('#div_id_vendor').addClass('hide');
        }        
    });

    $("#confirmation").change(function() {
      var signupForm = $("#content")
      var agreementText = $("#agreement")
      if(this.checked) {
        signupForm.removeClass('hide');
        agreementText.addClass('text-muted');
      }
      else{
        signupForm.addClass('hide');
        agreementText.removeClass('text-muted');
      }
    });
  }
});
