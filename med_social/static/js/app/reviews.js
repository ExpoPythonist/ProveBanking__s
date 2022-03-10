_inExec.extendClass({
  name: 'npsRating',

  initialize: function(options) {
    var that = this;
    this.$nps = options.$nps;
    this.$nps.parents('.form-control').removeClass('form-control');
    this.$select = $(this.$nps.attr('href'));
    //var defaultVal = this.$select.val();

    if (this.$nps.attr('data-readonly') != 'true') {
      this.$nps.find('.btn').on('click', function(){
        var $btn = $(this);
        $('.nps-choice').removeClass('active');
        $btn.addClass('active');
        that.$select.val($btn.attr('value'));
      });
    }
  }
});

_inExec.extendClass({
  name: 'reviewRating',

  initialize: function(option) {
    var that = this;
    this.$rating = option.$rating;
    this.$rating.parents('.form-control').removeClass('form-control');
    this.$select = $(this.$rating.attr('href'));
    var defaultVal = this.$select.val();
    this.$rating.find('li.selected').prevAll().addClass('selected');

    if (this.$rating.attr('data-readonly') != 'true') {
      this.$rating.find('li').on('click', function(){
        that.selectItem($(this));
      });

      this.$rating.find('li').hover(function(){
        that.highlightItem($(this), true);
      }, function(){
        that.highlightItem($(this), false)
      });
    }
  },

  selectItem: function($item){
    $item.addClass('selected');
    $item.prevAll().addClass('selected');
    $item.nextAll().removeClass('selected');
    this.$select.val($item.val());
  },

  highlightItem: function($item, on){
    if (on == true) {
      prevCount = 0;
      prevCount = $item.prevAll('li').length+1;
      //alert(prevCount);
      $item.parent().addClass('hover star'+prevCount);
      $item.addClass('hover');
      $item.prevAll().addClass('hover');
      $item.nextAll().removeClass('hover');
    } else {
      $item.parent().find('li.hover').removeClass('hover');
      $item.parent().removeClass('hover star'+prevCount);
    }
  }

});

_inExec.register({
  name: 'reviews',
  routes: ['^/projects/\\d+/requests/\\d+/reviews/\\d+/',
           '^/reviews/\\d+/',
           '^/vendors/.*/clients/confirm/.*/',
           '^/vendors/.*/clients/confirm/.*/',
           '^/reviews/public/create/.*'],
  initialize: function($container){
    this.$container = $container;
    this.ratingControllers = [];
    this.npsControllers = [];
    this.setup();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
    _.each(this.ratingControllers, function(i, controller){
      // FIXME: Destroy controllers here
    });
  },
  setup: function(){
    var that = this;
    this.$container.find('.star-rating-input').each(function(){
      that.ratingControllers.push(new _inExec.classes.reviewRating({'$rating': $(this)}))
    });

    this.$container.find('.nps-input').each(function(){
      that.npsControllers.push(new _inExec.classes.npsRating({'$nps': $(this)}))
    });
  },
});
