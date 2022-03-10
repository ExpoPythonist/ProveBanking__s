Messenger.options = {
    extraClasses: 'messenger-fixed messenger-on-bottom messenger-on-right',
    theme: 'flat',
};

_inExec.register({
  name: 'staffingRequests',
  routes: [
    '^/staffing/r/\\d+/$',
    '^/staffing/$',
    '^/projects/\\d+/$',
  ],
  initialize: function($container){
    var that = this;

    this.client = new $.RestClient('/api/');
    this.client.add('requests');
    this.client.requests.addVerb('archive', 'POST', {url: 'archive/'});
    this.client.requests.addVerb('unarchive', 'POST', {url: 'unarchive/'});

    this.filters = [];
    this.$container = $container;
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
    //this.$form.find('input[name=staff]').off('change', this.onStaffed);
    // TODO: destroy filter instances
    _inExec.modules.events.off('staffing:acl:vendors');
  },
  setup: function(){
    $('.btn-archive-request').on('click', $.proxy(this.archiveRequest, this));
    $('.btn-unarchive-request').on('click', $.proxy(this.unarchiveRequest, this));

    _inExec.modules.events.on('staffing:acl:vendors',
        $.proxy(this.onStaffingACLVendors));
    $('#genericModal').on('submit', 'form.staffing-acl-vendor-form', function(ev){
      ev.stopPropagation();
      ev.preventDefault();
      var $form = $(this);
      $.post(
        $form.attr('action'),
        $form.serialize()
      ).success(function(data){
        var $result = $(data.trim());
        $form.parents('#genericModal').modal('hide');
        var btnId = '.staffing-' + $form.attr('data-staffing-id') + '-acl';
        window.RR = $result.find(btnId);
        $(btnId).replaceWith($result.find(btnId));
      });
    });
  },

  unarchiveRequest: function(ev){
    ev.preventDefault();
    var that = this;
    var $target = $(ev.target);
    var $request = $target.parents('.request-item');
    var pk = $request.attr('data-pk');
    this.client.requests.unarchive(pk, {}).done(function(){
      $request.removeClass('hide');
      $target.removeClass('btn-unarchive-request').addClass('btn-archive-request');
    });
  },

  archiveRequest: function(ev){
    ev.preventDefault();
    var that = this;
    var $target = $(ev.target);
    var $request = $target.parents('.request-item');
    var pk = $request.attr('data-pk');
    var title = $request.attr('data-title');

    var notif = window.Messenger().post({
      'showCloseButton': true,
      'type': 'info',
      'message': 'Archiving "' + title + '"'
    });

    this.client.requests.archive(pk, {}).done(function(){
      $request.addClass('hide');
      $target.removeClass('btn-archive-request').addClass('btn-unarchive-request');

      notif.update({type: "success",
        message: 'Archived "' + title  + '"',
        actions: {
          undo: {
            label: "Undo",
            action: function(){
              that.unarchiveRequest(ev);
              notif.hide();
            }
          }
        }
      });
    });

  },

  onStaffingACLVendors: function(){
    var $btn = $('<a>');
    $btn.attr['href'] = '/users/owais/modal/';
    $btn.attr['data-toggle'] = 'modal';
    $btn.attr['data-target'] = '#genericModal';
    window.$btn = $btn;
    $btn.click();
  }
});

_inExec.register({
  name: 'staffingAndFixed',
  routes: ['^/projects/\\d+/requests/\\d+/edit/$',
           '^/projects/\\d+/requests/create/staffing|fixed/',
           '^/projects/\\d+/requests/\\d+/staffing|fixed/edit/',
           '^/staffing/r/s/\\d+/',
           '^/staffing/r/create/',
           '^/staffing/r/\\d+/create/staffing|fixed'
  ],
  initialize: function($container){
    var that = this;
    this.filters = [];
    this.$container = $container;

    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
    //this.$form.find('input[name=staff]').off('change', this.onStaffed);
    // TODO: destroy filter instances
  },
  setup: function(){
    var that = this;
    this.$form = $('#staffing-request-form');

    this.$form.find('input[name=viewable_by]').on('change', function(){
      var message = '';
      if (that.$form.find('#id_viewable_by_2').is(':checked') === true) {
        $('#div_id_vendors').show();
      } else {
        $('#div_id_vendors').hide();
      }
      that.$form.find('#hint_id_viewable_by').text(message);
    });

    if (that.$form.find('#id_viewable_by_2').is(':checked') === true) {
      that.$form.find('#id_viewable_by_2').click();
    } else if (that.$form.find('#id_viewable_by_1').is(':checked') === true) {
      that.$form.find('#id_viewable_by_1').click();
    }
  },
});
