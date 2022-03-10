_inExec.register({
  name: 'filters',
  routes: [
    '^/users/$',
    '^/projects/$',
    '^/staffing/$',
    '^/vendors/$',
    '^/lifecycles/instances/$',
    '^/staffing/r/\\d+/user/add/$',
    '^/staffing/r/\\d+/vendor/add/$',
    '^/p/',
    '^/search/',
  ],
  initialize: function($container){
    this._xhr = null;
    this._previousSeachTerm = '';
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
    if (this.$orderDropdown) {
      this.$orderDropdown.find('a').off('click');
    }
  },
  setup: function(){
    var that = this;
    this.$filterTags = $('#filter-tags');
    this.$inputSearch = $('#id_search');
    this.$filterToggle = $('#filter-toggle');
    this.$inputSearch.on('focus', function(){
      $(this).click();
    });
    this.$filterForm = $('#filter-form');
    this.$filterForm.find('input, select').on('change', $.proxy(this.filterFormChanged, this));
    this.$filterForm.find('.dropdown-menu *').on('click', function(e){
      e.stopPropagation();
    });

    this.$filterForm.find('.filter-btn').on('click', function(){
      $(this).parent().find('.selectize-input').click();
    });

    $( document ).ready(function() {
      if(that.$filterTags.children().length > 0){
          that.filterFormChanged();
       }
    });

    this.$filterTags.on('click', '.btn-remove', function(){
      var $this = $(this);
      var $tag = $($this.parent());
      var field = $('[name=' + $tag.attr('data-for') + ']')[0];
      $selectize = that._getSelectizeForField(field);
      $selectize.removeItem($tag.attr('data-value'));
    });

    this.$filterForm.find('select').each(function(i, elem) {
      that.updateFilterTags(elem);
    });

    this.setupFilterBtns();

    this.$inputSearch.on('keyup', _.debounce($.proxy(this.searchTermChanged, this), 300));

    $('#results-list').on('click', '#filter-toggle', function(e) {
      url = $(this).attr('data-action') + '?' + that.$filterForm.serialize() + '&filter=yes'
      window.location = url;
    });

    $('[data-humanize="compactInteger"]').each(function(i, el){
      var elm = $(el);
      elm.text(humanize.numberFormat(elm.text(), 0))
    });

    this.updateFilterUrls();
    this.setupScroll();
  },

  setupFilterBtns: function(){
    var that = this;
    this.$filterResultsCount = $('.filter-results-count');
    this.$orderDropdown = $('.list-order-dropdown');
    /*
    this.$orderDropdown.find('a').on('click', function(){
      var $this = $(this);
      $this.parents.find('.dropdown').find('.order-label').text($this.text());
    });
    */

    this.$filterBtns = $('.fake-filter-btn');
    this.$filterBtns.each(function(i, btn){
      $btn = $(btn);
      if ($btn.hasClass('active')) {
        var name = $btn.attr('data-name');
        that.$filterForm.find('input[name=' + name +']').remove();
        var $input = $('<input name="' + name + '" class="hide">');
        $input.val($btn.attr('data-value'));
        that.$filterForm.append($input);
      }
    });

    this.$filterBtns.on('click', function(e){
      e.preventDefault();
      e.stopPropagation();
      var $this = $(this);
      var name = $this.attr('data-name');
      that.$filterForm.find('input[name="' + name + '"]').val($(this).attr('data-value'));
      that.filterFormChanged();
      $this.siblings('.fake-filter-btn').removeClass('active');
      $this.addClass('active');
    });
  },

  checkVisible: function(elm, preload) {
    var vpH = $(window).height(), // Viewport Height
        st = $(window).scrollTop(), // Scroll Top
        y = $(elm).offset().top,
        elementHeight = $(elm).height();
    if (preload) return y < (vpH + st + preload);
    return y < (vpH + st);
  },

  setupScroll: function(e){
    var that = this;
    this.$filterScroll = $('#filter-scroll');

    if (this.$filterScroll.length === 0) return;

    // trigger scroll if page-end is already visible
    if (that.checkVisible('#filter-scroll')){
      toInfinityAndBeyond();
    }

    $(window).scroll(function () {
      var preload = that.$filterScroll.data('preload-offset');
      if (that.checkVisible('#filter-scroll', preload)) {
        toInfinityAndBeyond();
      }
    });

    function toInfinityAndBeyond(){
      if(!that.$filterScroll.data('last-page') && !that.$filterScroll.data('loading')){
        that.$filterScroll.data('loading', true)
        var page = that.$filterScroll.data('page') || 2;
        that.filterFormChanged(undefined, page);
      }
    }
  },

  destroyScroll: function(e){
    $(window).off('scroll');
  },

  searchTermChanged: function(e){
    var term = this.$inputSearch.val().trim();
    if (this._previousSearchTerm === term) {
      return;
    }
    this._previousSearchTerm = term;
    this.$inputSearch.trigger('change');
  },

  updateFilterTags: function(element){
    var that = this;
    var $elem = $(element);
    var $selectize = this._getSelectizeForField(element);
    if ($selectize === undefined) {
      return;
    }

    var values = $selectize.items;
    var isMultiple = $elem.attr('multiple') !== undefined;
    var validTags = [];
    _.each(values, function(value, i){
      validTags.push('.tag[data-value=' + value + ']');
      var $item = $selectize.getItem(value);
      var $tag = that.$filterTags.find('.tag#tag_' + $elem.attr('name') + '_' + value);
      if ($tag.length === 0 ){
        var text = $item.text();
        if (isMultiple === true) {
          text = text.slice(0, -1);
        }
        var $tag = $('<div class="btn-group btn-group-xs selected-keyword"><span  class="btn btn-default btn-o disabled">' + $elem.attr('name') + ': ' + text + '</span><a href="#" class="btn-remove btn btn-default remove-keyword"><i class="fa fa-times"></i></a></div>');
        $tag.attr('id', 'tag_' + $elem.attr('name') + '_' + value);
        $tag.attr('data-value', value);
        $tag.attr('data-for', $elem.attr('name'));
        $tag.addClass('tag');
        $tag.addClass('field-' + $elem.attr('name'));
        if ($selectize.$wrapper.parents('.btn-group').hasClass('hide')) {
          $tag.addClass('hide');
        }
        that.$filterTags.append($tag);
      }
    });
    this.$filterTags.find('.tag[data-for=' + $elem.attr('name') + ']').not(validTags.join(',')).remove();
  },

  _getSelectizeForField: function(field) {
    var s = _inExec.modules.autocomplete.$instances[this.$filterForm.attr('id') + '_' + field.id];
    if (s !== undefined) {
      return s.$selectize;
    } else {
      return undefined;
    }
  },

  updateFilterUrls: function(){
    var filterQuery = '?' + this.$filterForm.serialize() + '&filter=yes';
    $('.filter-url').each(function(i, link) {
      var $link = $(link);
      var url = $link.attr('default-href').split('?');
      var query = url[1] || '';
      url = url[0];

      var filters = _inExec.modules.utils.queryStringToObject(filterQuery);
      var defaultFilters = _inExec.modules.utils.queryStringToObject(query);
      filters = _.extend(filters, defaultFilters);
      url = url + _inExec.modules.utils.objectToQueryString(filters, {skipEmpty: true});
      $link.attr('href', url);
    });
  },

  filterFormChanged: function(e, page){
    var that = this;
    if (e !== undefined) {
      this.updateFilterTags(e.target);
    }

    var filterQuery = '?' + this.$filterForm.serialize() + '&filter=yes';
    if (page) {
      filterQuery += '&page=' + page;
    }
    var url = this.$filterForm.attr('action') + filterQuery;

    if (this._xhr !== null) {
      this._xhr.abort();
    }

    if (!page) {
      $('#results-list .block-cover').removeClass('hide');
      that.$filterResultsCount.text('...');
    } else {
      $('#filter-loading-icon').removeClass('hide');
    }

    this._xhr = $.ajax({
      type: 'GET',
      url: url,
      dataType: 'html'
    }).success(function(data, textStatus, jqXHR){
      var $result = $(data.trim());
      if(!page) {
        $('#results-list').html($result);
        $('.pin-columns').masonry('destroy');
        $('.pin-columns').masonry({itemSelector: '.pin-column'});
        _inExec.modules.tooltips.update($('#results-list'));
        _inExec.modules.projects.update($('#results-list'));
        var count = $result.find('#results-count').text();
        that.$filterResultsCount.text(count);
      } else {
        that.$filterScroll.remove();
        $('.results-items').append($result);
        $('.pin-columns').masonry('appended', $result);
      }
      that.destroyScroll();
      that.setupScroll();
      that.setupFilterBtns();
      _inExec.modules.events.trigger('filters:changed', {form: that.$filterForm.attr('id')});
      that.updateFilterUrls();

      $('[data-humanize="compactInteger"]').each(function(i, el){
        var elm = $(el);
        elm.text(humanize.numberFormat(elm.text(), 0))
      });
    });
  }
});
