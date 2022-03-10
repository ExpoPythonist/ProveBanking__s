_inExec.register({
  name: 'utils',
  initialize: function(){
    var that = this;

    $.fn.animateOnce = function(animationName, cb){
      that.animate(this, animationName, cb);
    };
  },

  animate: function($element, animationName, cb) {
    $element.one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
      $element.removeClass('animated ' + animationName);
      if (cb !== undefined) {
        cb();
      }
    });
    $element.addClass('animated ' + animationName);
  },

  isArrayEqual: function(array1, array2) {
    return JSON.stringify(array1.slice().sort()) == JSON.stringify(array2.slice().sort());
  },

  startsWith: function(string, suffix) {
    return string.indexOf(suffix) == 0;
  },

  endsWith: function(string, suffix) {
    return string.indexOf(suffix, string.length - suffix.length) !== -1;
  },

  getQueryStringFromURL: function(url) {
    return url.split('?')[1] || url.split('?')[0];
  },

  queryStringToObject: function(qs){
    if (qs[0] === '?') {
      qs = qs.slice(1);
    }
    var obj = {};
    _.each(qs.split('&'), function(param) {
      if (param !== '') {
        param = param.split('=');
        var name = param[0];
        var value = param[1];
        var old_value = obj[name];
        if (old_value === undefined) {
          obj[name] = value;
        } else {
          if (_.isArray(old_value)) {
            old_value.push(value);
            obj[name] = old_value;
          } else {
            var new_value = [old_value, value];
            obj[name] = new_value;
          }
        }
      }
    });
    return obj;
  },

  objectToQueryString: function(obj, options) {
    options = options || {};
    var qs = '';
    _.each(obj, function(value, key){
      if (_.isEmpty(value) && options.skipEmpty) {
        return;
      }
      if (_.isArray(value)) {
        _.each(value, function(val){
          qs += '&' + key + '=' + val;
        });
      } else {
        qs += '&' + key + '=' + value;
      }

    });
    qs = qs.slice(1);
    qs = '?' + qs;
    return qs;
  },

  getParamValueFromQueryString: function(url, name){
    var that = this;
    if (!url) {
      return null;
    }
    var search = url.split('?')[1] || url.split('?')[0];
    if (search){
      var param = _.find(search.split('&'), function(param){
        return that.startsWith(param, name + '=');
      });
      if (param){
        return param.split('=')[1];
      }
    }
    return null;
  },

  infiniteValueGenerator: function(values) {
    if (!_.isArray(values) || values.length == 0) {
      throw 'Argument 1 must be a non-empty array';
      return;
    }
    this._values = values;
    this._index = 0,

    this.next = function() {
      var value = this._values[this._index++];
      if (value == undefined) {
        this._index = 0;
        value = this.next();
      }
      return value;
    };
    this.reset = function(){
      this._index = 0;
    };
    return this;
  },

  randomValueGenerator: function(values){
    if (!_.isArray(values) || values.length == 0) {
      throw 'Argument 1 must be a non-empty array';
      return;
    }
    this._values = values;
    this._previousValue = null;
    this.length = this._values.length - 1;

    this.next = function() {
      var value = this._values[_.random(0, this.length)];
      if (value == this._previousValue) {
        return this.next();
      } else {
        this._previousValue = value;
        return value;
      }

    };
    return this;
  },

  promptDialog: function(message, default_value) {
    default_value = default_value || '';
  },

  isValidUrl: function(str) {
    var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
    '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
    '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
    '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
    '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
    '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    if(!pattern.test(str)) {
      return false;
    } else {
      return true;
    }
  },
});
