var Form = function($target){
  this.$target = $target;
  this.setUp();
};

Form.prototype.bind = function(){
  var that = this;
  this.$form.on('submit', $.proxy(this.submit, this));
  this.$form.on('reset', $.proxy(this.cancel, this));
  _inExec.modules.formEnhance.initialize(this.$form);
};

Form.prototype.setUp = function(){
  this.$results = $(this.$target.attr('data-editable'));
  this.$hide = $(this.$target.attr('data-hide'));
  if (this.$hide.length == 0) {
    this.$hide = this.$results;
  }
  this.$formContainer = $(this.$target.attr('data-form-container'));
  this.url = this.$target.attr('href');
  _inExec.modules.ui.block(this.$hide);
  var that = this;
  $.get(this.url).success(function(data){
    that.$form = $(data.trim());
    that.$formContainer.html(that.$form);
    that.$formContainer.removeClass('hide');
    that.$hide.addClass('hide');
    that.bind();
  }).fail(function(){
  }).always(function(){
    _inExec.modules.ui.unblock(that.$hide);
  });
};

Form.prototype.insertAfter = function($old, $new){
  $new.insertAfter($old);
};

Form.prototype.prepend = function($old, $new){
  $($old.attr('data-result-container')).prepend($new);
};

Form.prototype.append = function($old, $new){
  $($old.attr('data-result-container')).append($new);
};

Form.prototype.cancel = function(ev){
  this.$form[0].reset();
  this.$form.addClass('hide');
  this.$hide.removeClass('hide');
};

Form.prototype.submit = function(ev){
  ev.stopPropagation();
  ev.preventDefault();
  var that = this;
  _inExec.modules.ui.block(this.$form);
  var formData = that.$form.serializeArray();
  $.ajax({
    type: 'POST',
    url: that.$form.attr('action'),
    data: formData,
    dataType: 'html'
  }).success(function(data, textStatus, jqXHR){
    if (jqXHR.getResponseHeader('X-Form-Valid') == 'True') {
      that.$form.trigger('success');
      that.$form[0].reset();
      var $result = $(data.trim());
      var id = '#' + $result.attr('id');
      var $existing = that.$results.find(id);
      if ($result.attr('data-deleted') == 'True') {
        $existing.remove();
      } else {
        if ($existing.length == 0) {
          that.$results.append($result);
        } else {
          $existing.replaceWith($result);
        }
      }
      that.$form.html('').addClass('hide');
      that.$hide.removeClass('hide');
      that.$results.find('[data-type="placeholder"]').remove();
      _inExec.modules.formEnhance.initialize(that.$form);
      _inExec.modules.events.trigger('formSaved:' + that.$form.attr('id'), {result: $result, jqXHR: jqXHR});
    } else {
      that.$form.trigger('error');
      var $response = $(data.trim());
      that.$form.html($response.html());
      _inExec.modules.formEnhance.initialize(that.$form);
      _inExec.modules.events.trigger('formError:' + that.$form.attr('id'), {result: $result, jqXHR: jqXHR});
    }
  }).always(function(){
    _inExec.modules.ui.unblock(this.$form);
  });
};


_inExec.register({
  name: 'channelForms',
  routes: [''],

  initialize: function($container){
    var that = this;
    this.atJSClosedAt = new Date();
    this.$container = $container;
    this.isEnter = function(ev) {
      var keyCode = ev.keyCode || ev.which;
      if (keyCode === 13){
        if (ev.shiftKey == true) {
          return false;
        }
        return true;
      }
    }

    $container.on('submit', 'form[list-append]', function(ev){
      ev.preventDefault();
      ev.stopPropagation();
      var $form = $(this);
      var $list = $($form.attr('list-append'));

      if ($form.find('#id_body').val().trim() == '') {
        return;
      }

      //_inExec.modules.ui.block(this.$form);
      var formData = $form.serializeArray();
      $.ajax({
        type: $form.attr('method'),
        url: $form.attr('action'),
        data: formData,
        dataType: 'html'
      }).success(function(data, textStatus, jqXHR){
        if (jqXHR.getResponseHeader('X-Form-Valid') == 'True') {
          $form.trigger('success');
          $form[0].reset();
          var $result = $(data.trim());
          $list.append($result);
          _inExec.modules.events.trigger('formSaved:' + $form.attr('id'), {result: $result, jqXHR: jqXHR});
        } else {
          $form.trigger('error');
          var $response = $(data.trim());
          $form.html($response.html());
          _inExec.modules.formEnhance.initialize($form);
          _inExec.modules.events.trigger('formError:' + $form.attr('id'), {result: $result, jqXHR: jqXHR});
        }
      }).always(function(){
       // _inExec.modules.ui.unblock(this.$form);
      });

    });
    this.destroy();
    this.update();
  },
  update: function(){
    var that = this;
    _inExec.modules.events.on('')

    _inExec.modules.events.on('newItem:' + 'user-mention', function(ev){
      var email = ev.text;
      $('.email-mention[data-email="' + email + '"]').find(
        '.text').html('Invited <b>' + email + '</b>');
    });

    $("[data-phoneinput=true]").intlTelInput();
    $('.phonefield-form').submit(function(){
      var number = $('.phonefield-form [data-phoneinput=true]')
      var dialCode = '+' + number.intlTelInput("getSelectedCountryData").dialCode
      var diallength = dialCode.length
      if (number.val().slice(0,diallength) == dialCode){
          number.val(number.val());
      } else{
          if(number.val()){
            number.val(dialCode + number.val());
          } else{
            number.val(number.val());
          }
      }
    });

    $('textarea#id_body.channel-message').each(function(){
      var $txtarea = $(this);
      var cachequeryMentions = {};
      $txtarea.atwho({
        at: "@",
        search_key: 'search_index',
        tpl: "<li data-value='@${username}'>${first_name} ${last_name} (@${username})</li>",
        callbacks: {
          remote_filter: _.debounce(function(query, callback){
            var url = this.$inputor.parents('form').attr('data-suggestions-url');
            var search_id = query + '+' + url;
            if (cachequeryMentions[search_id] !== undefined) {
              callback(cachequeryMentions[search_id]);
            } else {
              $.getJSON(url, {q: query}, function(data) {
                cachequeryMentions[search_id] = data;
                _.each(data, function(d, i){
                  d.search_index = d.username + ' ' + d.first_name + ' ' + d.last_name;
                });
                callback(data);
              });
            }
          }, 300)
        }
      });
      $txtarea.on('hidden.atwho', function(){
        that.atJSClosedAt = new Date();
      });

      $txtarea.on('keydown', function(ev){
        if (that.isEnter(ev)) {
          var ago = new Date() - that.atJSClosedAt;
          ev.preventDefault();
          ev.stopPropagation();
          if (ago > 100) {
            $(this).parents('form').submit();
          }
        }
      });

    });
  },
  destroy: function(){
  }
});


_inExec.register({
  name: 'formEnhance',
  routes: ['^.*$'],
  __initDone: false,

  initialize: function($container) {
    var that = this;
    this.$container = $container || $('body');
    if (this.__initDone === false) {
      this.$container.on('initialize.form', 'form', function(){
        var $this = $(this);
        that.setUp($this);
      });
      this.__initDone = true;
    }
    this.setUp();
  },

  update: function(){
    this.setUp();
  },

  setUp: function($container){
    var $container = $container || this.$container;
    $container.find('form').not('[force-validate]').attr('novalidate', '');
    $container.find('input[type=file]').filestyle({size: "sm",buttonBefore:true});
    $container.find('textarea[autoresize=true]').autosize();
    _inExec.modules.autocomplete.resetInstances($container);
    _inExec.modules.datepicker.resetInstances($container);
    $container.find('input[type=checkbox]:not([ignore-enhance])').each(function(i, e){
      new Switchery(e, {color: '#fd6107'});
    });

    var $radioFields = $container.find('.radio-field > .controls').not('[ignore-enhance]');
    /*
    $radioFields.each(function(i, radio){
      var $radio = $(radio).find('.radio');
      var $buttonGroup = $('<div class="btn-group btn-group-radio" data-toggle="buttons"></div>');
      $radio.each(function(i, option) {
        var $option = $(option);
        $option.removeClass('radio');
        $option.addClass('btn btn-default btn-sm');
        $buttonGroup.append($option);
        if ($radio.find('input').hasClass('btn-block')) {
          $buttonGroup.addClass('btn-block');
          $buttonGroup.find('.btn').addClass('col-xs-6');
        }
      });
      $(radio).prepend($buttonGroup);
      $buttonGroup.find('.btn').button();
    });
    */
    $radioFields.find('input').filter(':checked').click();

    $container.find('.btn-delete').click(function(ev) {
      ev.preventDefault();
      ev.stopPropagation();
      var $form = $(ev.target).parents('form');
      bootbox.dialog({
        title: "Confirm Deletion",
        message: "Are you sure you want to delete this?",
        buttons: {
          no: {
            label: 'Cancel',
            className: ' ',
          },
          yes: {
            label: 'Delete',
            className: ' ',
            callback: function() {
              $form.find("#id_delete").attr('value', 'True');
              $form.submit();
            }
          },
        }
      })
    });
  }
});


_inExec.register({
  name: 'forms',
  editBtnSelector: '.edit-trigger',

  initialize: function($container){
    var that = this;
    $container.on('click', this.editBtnSelector, function(ev){
      ev.preventDefault();
      that.edit(ev, $(this));
    });

    $container.on('click', '.btn-form-submit', function(ev){
      ev.preventDefault();
      var $this = $(this);
      var $form = $($this.attr('href'));
      if ($form.length > 0) {
        $form.trigger('submit', {'submitBtn': $this});
      }
    });

    $container.on('submit', 'form[data-ajax-form]', function(ev, data){
      var $form = $(this);
      var $iframe = $('iframe#' + $form.attr('target'));
      _inExec.modules.ui.showLoading();
      if ($iframe.length === 0) {
        ev.stopPropagation();
        ev.preventDefault();
        var serialized = $form.serialize();
        if (data && data.submitBtn) {
          serialized = _inExec.modules.utils.queryStringToObject(serialized);
          serialized[data.submitBtn.attr('data-name')] = data.submitBtn.attr('data-value');
          serialized = _inExec.modules.utils.objectToQueryString(serialized);
        }
        $.post($form.attr('action'), serialized)
         .success(function(data){
           var eventName = '';
           $result = $(data.trim());

           if ($result.find('.has-error').length === 0) {
             eventName = 'form:success#';
             $form.replaceWith($result);
             $form.trigger('reset');
           } else {
             eventName = 'form:error#';
             $form.replaceWith($result);
           }
           $result.trigger('initialize.form');

           _inExec.modules.events.trigger(eventName + $form.attr('id'));

           var $resultItem = $();
           if ($result.hasClass('result-item')) {
             $resultItem = $result;
           } else if ($result.find('.result-item').length !== 0) {
             $resultItem = $result.find('.result-item');
           }

           if ($resultItem.length !== 0) {
             var pk = $resultItem.attr('data-pk');
             var kind = $resultItem.attr('data-kind');
             var text = $resultItem.attr('data-text');
             _inExec.modules.events.trigger({
               type: 'newItem:' + kind,
               pk: pk,
               kind: kind,
               text: text,
               $result: $resultItem
             });
           }
         })
         .complete(function(){
          _inExec.modules.ui.hideLoading();
         });
        return;
      } else {
        $iframe.on('load', function(){
          var $iframe = $(this);
          var contents = $iframe[0].contentWindow.document.body.innerHTML;
          var $form = $($iframe.attr('data-form'));

          var $result = $(contents.trim());
          $form.replaceWith($result);
          $form = $result;
          if ($result.hasClass('result-item')) {
            var pk = $result.attr('data-pk');
            var kind = $result.attr('data-kind');
            var text = $result.attr('data-text');
            _inExec.modules.events.trigger({
              type: 'newItem:' + kind,
              pk: pk,
              kind: kind,
              text: text,
            });
          } else {
            $result.trigger('initialize.form');
          }
          _inExec.modules.ui.hideLoading();
        });
      }
    });
  },

  edit: function(ev, $target) {
    new Form($target);
  },
});


