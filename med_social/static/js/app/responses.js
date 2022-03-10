_inExec.register({
  name: 'responses',
  routes: ['^/projects/\\d+/requests/\\d+/\\d+/$', '/projects/\\d+/',
           '^/staffing/r/\\d+/$', '^/staffing/proposed/\\d+/'],
  initialize: function($container){
    this.$container = $container;
    this.csrftoken = $('#csrf-middleware-token').attr('value');
    this._xhr = {};
    this.update();
  },
  destroy: function(){
    this.$container.off('click', '.proposed-status-btn');
  },
  update: function(){
    var that = this;
    this.destroy();
    this.$container.find('#responses-page-tab').find('a').on('click', function(){
      var $this = $(this);
      var $siblings = $this.siblings();
      $siblings.removeClass('btn-default active').addClass('btn-default');
      $this.removeClass('btn-default').addClass('btn-default active');
    });
    this.$container.find('i.response-contradiction').tooltip();
    this.$container.on('click', '.proposed-status-btn', function(e){
      e.stopPropagation();
      e.preventDefault();
      that.onStatusChange(this);
    });

    this.$container.on('click', '.vendor-confirm-btn', function(e){
      e.stopPropagation();
      e.preventDefault();
      that.onVendorActionChange(this);
    });

    this.$container.on('click', '.cancel-btn', function(e){
      $('.status-change-confirmation').hide()
    });
  },
  onStatusChange: function(target){
    var that = this;
    var $target = $(target);
    var $blockCover = $target.parents('.proposed-staff-card').find('.block-cover');
    $blockCover.removeClass('hide');
    $target.parents('ul').siblings('.dropdown-toggle').trigger('click');

    var staffId = $target.attr('data-staff-id');
    var $toReplace = $($target.attr('data-target'));

    var xhr = this._xhr[staffId];
    if (xhr !== undefined) {
      xhr.abort();
    }

    this._xhr[staffId] = $.ajax({
      url: $target.attr('data-action-url'),
      type: 'POST',
      data: {
        'csrfmiddlewaretoken': that.csrftoken,
        'status': $target.attr('data-status-id')
      }
    }).success(function(data, textStatus, jqXHR){
      var $new = $(data.trim());
      $toReplace.replaceWith($new);
      $('.status-change-confirmation').hide()
    }).fail(function(){
    }).always(function(){
      $blockCover.addClass('hide');
    });
  },

  onVendorActionChange: function(target){

    var that = this;
    var $target = $(target);
    $target.parents('ul').siblings('.dropdown-toggle').trigger('click');
    var answer = $target.attr('data-answer');
    $.get($target.attr('data-action-url'));
  }
});
