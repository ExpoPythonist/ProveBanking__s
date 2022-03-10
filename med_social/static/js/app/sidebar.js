_inExec.register({
  name: 'sidebars',
  initialize: function($container){
    this.$container = $container;
    this.$body = $('body');
    this.$sidebarContainer = $('#sidebar-container');
    this.$sidebarBackdrop = $('#sidebar-backdrop');
    this.setUp();
  },

  show: function($sidebar){
    var that = this;
    var $sidebar = $sidebar;
    this.$container.find('.sidebar.in').not($sidebar).removeClass('in');
    $sidebar.addClass('in');
    this.$sidebarBackdrop.removeClass('hide');
    this.$sidebarContainer.addClass('in');
    setTimeout(function(){
      that.$body.addClass('no-overflow');
    }, 100);
  },

  hide: function($sidebar){
    var that = this;
    var $sidebar = $sidebar;
    that.$sidebarBackdrop.addClass('hide');
    $sidebar.removeClass('in');
    this.$sidebarContainer.removeClass('in');
    setTimeout(function(){
      if (that.$container.find('.sidebar.in').length == 1) {
        that.$body.removeClass('no-overflow');
      }
    }, 300);
  },

  setUp: function() {
    var that = this;
    this.$sidebarBackdrop.on('click', function(ev){
      if (ev.target !== this) {
        return;
      }
      that.hide(that.$container.find('.sidebar'));
      ev.stopPropagation();
      ev.preventDefault();
    });

    this.$container.on('click', '.sidebar', function(){
      that.hide(that.$container.find('.sidebar'));
    });

    // show when trigger is clicked
    this.$container.on('click', '.offcanvas-btn', function(ev){
      var $sidebar = $('#' + $(this).attr('data-target'));
      that[$sidebar.hasClass('in')? 'hide': 'show']($sidebar);
      ev.stopPropagation();
      ev.preventDefault();
    });
  }
});
