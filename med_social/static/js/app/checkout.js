_inExec.register({
  name: 'checkout',
  routes: ['^/shortlist/$'],
  initialize: function($container){
    var that = this;

    var cartList = document.getElementById('cart-list');
    if (cartList !== null) {
      _vttd.cartActions.mountListOnNode(cartList);
    }

    $('#create-new-request').on('click', function(e){
      e.preventDefault();
      e.stopPropagation();
      _vttd.cartActions.removeRequest();
      window.location.pathname = $(this).attr('data-href');
    });

    $('.selectable').find('.select-input').on('click',
      function(){
        that.select($(this).parents('.selectable'));
      });

    _vttd.Events.on('cart:changed', $.proxy(this.cartChanged, this));
    _vttd.cartActions.showIfReady();
  },

  cartChanged: function(e, cart){
    var $selected = $('.selectable.selected');
    if (cart.request) {
      var $newSelected = $('#request-' + cart.request.id);
      $selected = $selected.not($newSelected);
      $newSelected.addClass('selected');
    }
    $selected.removeClass('selected');
  },

  select: function($selectable){
    that = this;
    var $cart = $('.cart-folder');

    var $json = $selectable.find('.as-json');
    if ($json.attr('data-type') === 'request') {
      if ($selectable.hasClass('selected')) {
        _vttd.cartActions.removeRequest();
      } else {
        _vttd.cartActions.addRequest(JSON.parse($json.text()));
        this.animateSelection($selectable, $cart);
      }
      $cart.animateOnce('bounce', {direction: "up"});
    }
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
  }
});
