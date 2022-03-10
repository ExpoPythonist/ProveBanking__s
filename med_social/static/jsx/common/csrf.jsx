// find a better place for this
var csrftoken = $('#csrf-middleware-token').attr('value');
$(document).ajaxSend(function(event, jqXHR, settings ) {
  jqXHR.setRequestHeader('X-CSRFToken', csrftoken);
});


module.exports = {
  'CSRFManager': ''
};
