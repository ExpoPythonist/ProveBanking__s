_inExec.register({
  name: 'vendorList',
  routes: ['^/vendors/.*',
           '^/vendors/$',
           '^/search/$'],
  initialize: function($container){
    this.update();
  },
  update: function(){
    var that = this;
    that.search_query = null;
    that.search_query_find = null;
    this.destroy();
    var find = _inExec.modules.autocomplete.$instances['filter-form_id_find'];
    if (find) {
      find.$selectize.on('change', function(){
        var selected = find.$selectize.getValue();
        var selected_string = ""
        _.each(selected, function(value, i){
          if (value.split('-')[0] === 'user') {
            window.location = '/users/' + value.split('-')[1];
            return false;
          }

          if (value.split('-')[0] === 'search') {
              value = value.replace(' ', '+')
          }

          if(i==0){
            selected_string = selected_string + '?find=' + value;
          } else{
            selected_string = selected_string + '&find=' + value;
          }
          
        });
        
        if (history.pushState) {
            var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + selected_string;
            window.history.pushState({path:newurl},'',newurl);
        }
      });

      find.$selectize.on('blur', function(){
        var selected = find.$selectize.getValue();
        if (selected.length < 1 && that.search_query_find ){
          search_item = 'search-' + that.search_query_find
          find.$selectize.addOption({text: search_item, value: search_item})
          find.$selectize.addItem(search_item)
        }
        that.search_query_find = null;
      });

      find.$selectize.on('type', function(str){
        that.search_query_find = str;
      });

    }

    var search_find = _inExec.modules.autocomplete.$instances['undefined_id_find'];
    if (search_find) {
      search_find.$selectize.on('change', function(){
        var selected = search_find.$selectize.getValue();
        _.each(selected, function(value, i){
          if (value.split('-')[0] === 'user') {
          $('.btn-cta').addClass('disabled');
            window.location = '/users/' + value.split('-')[1];
            return false;
          }
        });

      });

      search_find.$selectize.on('blur', function(){
        var selected = search_find.$selectize.getValue();
        if (selected.length < 1 && that.search_query ){
          search_item = 'search-' + that.search_query;
          search_find.$selectize.addOption({text: that.search_query, value: search_item})
          search_find.$selectize.addItem(search_item)
          search_find.$selectize.refreshOptions();
        }
        that.search_query = null;
      });

      search_find.$selectize.on('type', function(str){
        that.search_query = str;
      });

    }

    _inExec.modules.events.on('form:success#engage-form', function(ev){
      var $form = $('#engage-form');
      $form.parents('.modal').modal('hide');
      location.reload();
    });

    var clientSelect = _inExec.modules.autocomplete.$instances['client-form_id_client_form-client']
    if(clientSelect) {
      var result_exist = $('#result-exist');
      var logo = result_exist.attr('data-logo-url');

      if (result_exist.length > 0){
        var selected = clientSelect.$selectize.options[clientSelect.$selectize.getValue()];
        $('#div_id_client_form-client').after(
            '<div id="client-details" class="text-center col-sm-6 client-detail-snip">' +
              '<strong class=" text-center strong">' + selected.text + '</strong><br>' +
              '<img width=120 height=120 id="selected-client-logo" src="' + logo + '">' +
              (selected.size ? ('<small class="text-muted">' + selected.size + ' employees</small><br>') : '') +
              (selected.industries ? ('<small class="text-muted">' + selected.industries.slice(0,2) + '</small>') : '') +
            '</div>');
        var slug = $('#vendor-slug').html();
        $.getJSON('/clients/score/' + slug + '/?domain=' + selected.domain, function(data) {
          $('#client-details').append('<strong style="display: block;" class="text-muted">Potential Proven Score: ' + data.old + ' &rarr; ' + data.new + '</strong>');
        });
      }

      clientSelect.$selectize.on('change', function(){
        var selected = clientSelect.$selectize.options[clientSelect.$selectize.getValue()];
        console.log(selected);
        $('#client-form #client-details').remove();
        if (!selected || selected.is_editable){
          $('#div_id_client_form-logo').removeClass('hide');
          $('#div_id_client_form-size').removeClass('hide');
          $('#div_id_client_form-industries').removeClass('hide');
          $('#div_id_client_form-website').removeClass('hide');
        } else {
          $('#div_id_client_form-logo').addClass('hide');
          $('#div_id_client_form-size').addClass('hide');
          $('#div_id_client_form-website').addClass('hide');
          $('#div_id_client_form-industries').addClass('hide');
          $('.client-detail-snip').addClass('hide');
          $('#div_id_client_form-client').after(
            '<div id="client-details" class="text-center col-sm-6 client-detail-snip">' +
              '<strong class=" text-center strong">' + selected.text + '</strong><br>' +
              '<img id="selected-client-logo" src="' + selected.logo + '">' +
              (selected.size ? ('<small class="text-muted">' + selected.size + ' employees</small><br>') : '') +
              (selected.industries ? ('<small class="text-muted">' + selected.industries.slice(0,2) + '</small>') : '') +
            '</div>');
          var slug = $('#vendor-slug').html();
          $.getJSON('/clients/score/' + slug + '/?domain=' + selected.domain, function(data) {
            $('#client-details').append('<strong style="display: block;" class="text-muted">Potential Proven Score: ' + data.old + ' &rarr; ' + data.new + '</strong>');
          });
        }
      });
    }

    _inExec.modules.events.on('form:success#client-add-form', function(ev){
      var $form = $('#client-add-form');
      var url = $('.result-item').attr('data-url');
      $('#selected-client-logo').attr('src', url);
      var slug = $('#vendor-slug').html();
      var domain = $('#client-domain').html();
      $.getJSON('/clients/score/' + slug + '/?domain=' + domain, function(data) {
        $('#client-details').append('<strong style="display: block;" class="text-muted">Potential Proven Score: ' + data.old + ' &rarr; ' + data.new + '</strong>');
      });
    });

    $('.shortlist-form').submit(function(e) { return false; });
    button_clicked = false;
    $('.shortlist-form input[type="checkbox"]').change(function(e) {
      if(!button_clicked) {
        button_clicked = true;
        e.stopPropagation();
        e.preventDefault();
        var $this = $(this).parent();
        var $action = null;
        if($this.data('shortlisted') != 'yes') {
          $action = $this.data('action-add');
        } else {
          $action = $this.data('action-remove');
        }
        $.post($action, function(data, status_code) {
          $('.selected-qty span').html(data['count']);
          if(data['shortlisted']) {
            $this.data('shortlisted', 'yes');
          } else {
            $this.data('shortlisted', 'no');
          }
          button_clicked = false;
        });
      }
      return false;
    })
    $('.shortlist-all').click(function() {
      $('.shortlist-form input[type="checkbox"]:not(:checked)').click();
    });

    $('.location-delete-btn').click(function(ev) {
      $(ev.target).closest('.btn-group').addClass('hide');
      $.post($(ev.target).attr('data-url'));
    })

    $('#vendor-kind-select .kind-option').click(function(ev) {
      ev.preventDefault()
      var $elm = $(ev.target);
      var $kindOptions = $('#vendor-kind-select .kind-option');
      var $kindValue = $('#vendor-kind-select #kind-value');
      $.post($('#vendor-kind-select').attr('data-url'), {kind: $elm.attr('data-kind')});

      $kindOptions.removeClass('hide');
      $elm.addClass('hide');
      $kindValue.html($elm.attr('data-label'));
      $kindOptions.each(function(i, item){
        $kindValue.closest('button').removeClass('btn-' + $(item).attr('data-color'));
      });
      $kindValue.closest('button').addClass('btn-' + $elm.attr('data-color'));
    })

    var certSelect = _inExec.modules.autocomplete.$instances['vendor-cert-form_id_cert']
    if(certSelect) {
      certSelect.$selectize.on('change', function(){
        var selected = certSelect.$selectize.options[certSelect.$selectize.getValue()];
        if (!selected || selected.kind != "2"){
          $('#vendor-cert-form #div_id_email').removeClass('hide');
          $('#vendor-cert-form #div_id_url').removeClass('hide');
          $('#vendor-cert-form #hint_id_email_msg').html('');
          $('#vendor-cert-form #id_email_msg').html('');
        } else {
          $('#vendor-cert-form #div_id_email').addClass('hide');
          $('#vendor-cert-form #div_id_url').addClass('hide');
          $('#vendor-cert-form #hint_id_email_msg').html(
            ('Please include the name and the email address of your contact at this ' + 
             'organization or link to a website/press release or enter details to help ' +
             'them verify your relationship'));
          var email_msg = $('#vendor-cert-form #id_email_msg').attr('data-initial');
          $('#vendor-cert-form #id_email_msg').html(email_msg);
        }
      });
    }

    $('.toggle-btn').on('click',function(ev) {
      $(ev.target).parent('.description').toggleClass('less more');
      $(ev.target).toggleClass('fa-angle-down fa-angle-up');
    })

    function getParameterByName(name) {
      name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
      var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
          results = regex.exec(location.search);
      return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
    }

    var search_param = getParameterByName('search');
    if(search_param){
      $('#id_search').val(search_param);
    }

    if (window._vttd !== undefined) {
      window._vttd.Events.on('cart:changed', this.cartChanged);
    }

    $('.shortlist-btn').on('click', function(e){
      e.preventDefault();
      e.stopPropagation();
      var $btn = $(this);
      var $json = $($btn.attr('data-target'));
      var $cart = $('.cart-folder');

      if ($json.hasClass('selected')) {
        window.cartActions.removeVendor(JSON.parse($json.text()));
        $btn.text('shortlist supplier');
      } else {
        window.cartActions.addVendor(JSON.parse($json.text()));
        that.animateSelection($btn.parents().find('.animate-on-shortlist'), $cart);
        $btn.text('remove from shortlist');
      }
      $cart.animateOnce('bounce');
    });

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

  cartChanged: function(e, cart){
    var selected = [];

    _.each(cart.vendors, function(vendor){
      selected.push('.as-json[data-type=vendor][data-id=' + vendor.id + ']');
    });

    var $selected = $(selected.join(','));
    $('.as-json').not($selected).removeClass('selected');
    $selected.addClass('selected');
  },

  destroy: function(){
    $('.shortlist-btn').off('click');
    $('.toggle-btn').off('click');
    _inExec.modules.events.off('form:success#engage-form')
    window._vttd.Events.off('cart:changed', this.cartChanged);
  },
});


