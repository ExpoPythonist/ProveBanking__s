_inExec.register({
  name: 'selectableList',
  routes: ['^/users/$',
           '^/vendors/$', 
           '^/staffing/r/\\d+/user/add/$', 
           '^/staffing/r/\\d+/vendor/add/$'],
  initialize: function($container){
    this.$container = $container;
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
  },
  setup: function(){
    var that = this;
    this.csrftoken = $('#csrf-middleware-token').attr('value');
    this.$requestBtns = $('.btn-request-modal');
    this.$addToRequestBtn = $('.btn-add-user');
    this.$container.on('click', '.select-input', $.proxy(this.onSelectChanged, this));
    this.$container.find('.select-input').filter(':checked').trigger('change');
    this.$addToRequestBtn.on('click', function(){
      var $selectedList = $('.selected');
      var $url = $(this).attr('data-add-staffing-url');
      var $redirect_url = $(this).attr('data-success-url');
      var list = [];
      $selectedList.find('button').each(function(){ 
        list.push($(this).attr('data-value'));
      })
      if (list.length > 0){
         $.ajax({
            url: $url,
            type: 'POST',
            data: {
              'csrfmiddlewaretoken': that.csrftoken,
              'id_list': list
            }
          }).success(function(){
            window.location.replace($redirect_url);
          })
          $(that.$addToRequestBtn).addClass('disabled btn-default').removeClass('btn-primary');
      }

    });

    if (window._vttd !== undefined) {
      window._vttd.Events.on('cart:changed', this.cartChanged);
    }
  },

  cartChanged: function(e, cart){
    var selected = [];

    _.each(cart.people, function(person){
      selected.push('#user-' + person.id);
    });

    _.each(cart.vendors, function(person){
      selected.push('#vendor-' + person.id);
    });

    var $selected = $(selected.join(','));
    $('.selectable.selected').not($selected).removeClass('selected');
    $selected.addClass('selected');
  },

  animateSelection: function($card, $destination) {

      var cardCopy = $card.clone()
          .offset({
          top: $card.offset().top,
          left: $card.offset().left
      })
          .css({
          'opacity': '0.5',
              'position': 'absolute',
              'height': '150px',
              'width': '150px',
              'z-index': '100'
      })
          .appendTo($('body'))
          .animate({
          'top': $destination.offset().top + 10,
              'left': $destination.offset().left + 10,
              'width': 20,
              'height': 20
      }, 800);
      cardCopy.animate({
          'width': 0,
              'height': 0
      }, function () {
          $(this).detach()
      });
  },

  onSelectChanged: function(ev){
    var that = this;
    var $btn = $(ev.target);
    var $selectable = $btn.parents('.selectable');
    var $cart = $('.cart-folder');

    $selectable.toggleClass('selected');
    var $json = $selectable.find('.as-json');

    if ($selectable.hasClass('selected')) {
      if ($json.attr('data-type') === 'person') {
        window.cartActions.addPerson(JSON.parse($json.text()));
      } else if($json.attr('data-type') === 'vendor') {
        window.cartActions.addVendor(JSON.parse($json.text()));
      }
      this.animateSelection($selectable, $cart);

    } else {
      if ($json.attr('data-type') === 'person') {
        window.cartActions.removePerson(JSON.parse($json.text()));
      } else if($json.attr('data-type') === 'vendor') {
        window.cartActions.removeVendor(JSON.parse($json.text()));
      }
    }
    $cart.animateOnce('bounce', {direction: "up"});
  },
  updateSelection: function($selectable){
    var that = this;
    var $selectedList = $($selectable.attr('data-selected-list'));
    var $selectedLabel = $($selectedList.attr('data-label'));
    var count = $selectedList.find('.selectable').length;
    var $count = $($selectable.attr('data-counter'));

    $count.find('.count').text(count);
      if (count > 0) {
      $count.animateOnce('bounce');
      $selectedLabel.removeClass('hide');
      $count.addClass('btn-primary').removeClass('btn-default disabled');
      $(that.$addToRequestBtn).addClass('btn-primary').removeClass('btn-default disabled');
    } else {
      $count.addClass('btn-default disabled').removeClass('btn-primary');
      $(that.$addToRequestBtn).addClass('btn-default disabled').removeClass('btn-primary');
      $selectedLabel.addClass('hide');
    }
    this.$requestBtns.each(function(i, btn){
      var $btn = $(btn);
      var qs = _inExec.modules.utils.getQueryStringFromURL($btn.attr('href'));
      var url = $btn.attr('href').split('?')[0];
      if (url) {
        url = url + '?mode=modal&';
        url = url + $selectedList.find('input').serialize();
        $btn.attr('href', url);
      }
    });
  }
});
