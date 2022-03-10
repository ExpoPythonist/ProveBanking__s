_inExec.register({
  name: 'ajax',
  initialize: function(){
    var that = this;

    this.csrftoken = $('#csrf-middleware-token').attr('value');
    $( document ).ajaxSend(function(event, jqXHR, settings ) {
      jqXHR.setRequestHeader('X-CSRFToken', that.csrftoken);
    });

    $(document).on('click', 'a[data-replace]', function(ev){
      that.onClicked(ev, $(this));
    });

    $(document).on('click', 'a[data-remove]', function(ev){
      var $target = $($(this).attr('data-remove'));
      $target.remove();
      ev.stopPropagation();
      ev.preventDefault();
    });
  },
  onClicked: function(ev, $element){
    // FIXME: Debounce this to prevent double clicks, etc.
    var that = this;
    ev.preventDefault();
    ev.stopPropagation();
    var url = $element.attr('href');
    var target = $element.attr('data-replace').trim();
    if (target !== '') {
      var $target = $(target);
    } else {
      var $target = $element;
    }
    var method = $element.attr('data-method') || 'get';
    if ($element.hasClass('btn')) {
      $element.button('loading');
    }
    var data = {};
    _.each($element.get(0).attributes, function(attr, i){
      if (_inExec.modules.utils.startsWith(attr.name, 'x-form-data')) {
        var name = attr.name.split('x-form-data-')[1];
        data[name] = attr.value;
      }
    });
    data['csrfmiddlewaretoken'] = that.csrftoken;

    $.ajax({
      url: url,
      type: method,
      data: data
    }).success(function(data, textStatus, jqXHR){
      var klass = $element.attr('data-class');
      var $result = $(data.trim());
      $result.addClass(klass);
      $result.attr('data-class', klass);
      $target.replaceWith($result);
      var eventName = $result.attr('data-event-success');
      if (eventName !== undefined) {
        _inExec.modules.events.trigger(eventName, {$result: $result, jqXHR: jqXHR});
      }
    });
  }
});
