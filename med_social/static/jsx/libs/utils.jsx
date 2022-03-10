var React = require('react');
var form2js = require('../libs/form2js.js').form2js;

var Utils = function(){
  var that = this;
  $.fn.animateOnce = function(animationName, cb){
    that.animate(this, animationName, cb);
  };
};


Utils.prototype.animate = function($element, animationName) {
  $element.one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
    $element.removeClass('animated ' + animationName);
  });
  $element.addClass('animated ' + animationName);
};


Utils.prototype.getFormData = function($form){
  return form2js($form, '.', false);
};

Utils.prototype.isArrayEqual = function(array1, array2) {
  return JSON.stringify(array1.slice().sort()) == JSON.stringify(array2.slice().sort());
};

Utils.prototype.startsWith = function(string, suffix) {
  return string.indexOf(suffix) == 0;
};

endsWith = function(string, suffix) {
  return string.indexOf(suffix, string.length - suffix.length) !== -1;
};

getQueryStringFromURL = function(url) {
  return url.split('?')[1] || url.split('?')[0];
};

Utils.prototype.queryStringToObject = function(qs){
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
};

Utils.prototype.objectToQueryString = function(obj) {
  var qs = '';
  _.each(obj, function(value, key){
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
};

Utils.prototype.getParamValueFromQueryString = function(url, name){
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
};


Utils.prototype.InfiniteValueGenerator = function(values) {
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
};

Utils.prototype.RandomValueGenerator = function(values){
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
};

Utils.prototype.isValidUrl = function(str) {
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
};

Utils.prototype.invertColor = function(hexTripletColor){
  var color = hexTripletColor;
  color = color.substring(1);           // remove #
  color = parseInt(color, 16);          // convert to integer
  color = 0xFFFFFF ^ color;             // invert three bytes
  color = color.toString(16);           // convert to hex
  color = ("000000" + color).slice(-6); // pad with leading zeros
  color = "#" + color;                  // prepend #
  return color;
};


Utils.prototype.lightOrDarkColor = function(color) {
  r = parseInt(color.slice(1, 3), 16);
  g = parseInt(color.slice(3, 5), 16);
  b = parseInt(color.slice(5, 7), 16);
  brightness = (r * 299 + g * 587 + b * 114) / 1000;
  if (brightness < 180) {
    return '#FFFFFF';
  } else {
    return '#00000';
  }
};

Utils.prototype.toRGBA = function(color, alpha) {
  alpha = alpha || 255;
  r = parseInt(color.slice(1, 3), 16);
  g = parseInt(color.slice(3, 5), 16);
  b = parseInt(color.slice(5, 7), 16);
  return 'rgba(' + r + ',' + g + ',' +  b + ',' + alpha + ')';
};

Utils.prototype.toHex = function(color) {
  console.log(color.slice(5, -1));
  var rgba = _.map(color.slice(5, -1).split(','), function(val){
    return Number(val);
  });
  var r = rgba[0],
      g = rgba[1],
      b = rgba[2],
      a = rgba[3];
  console.log(r, g, b, a);
  if (r > 255 || g > 255 || b > 255 || a > 255)
      throw "Invalid color component";
  return (256 + r).toString(16).substr(1) +((1 << 24) + (g << 16) | (b << 8) | a).toString(16).substr(1);
};

Utils.prototype.truncatedJoin = function(list, n, delimiter) {
  var items = _.take(list, n);
  var value = items.join(delimiter);
  var more = list.length - items.length;
  if (more > 0) {
    value += ' & ' + more + ' more';
  }
  return value;
}

Utils.prototype.filenameFromURL = function(url) {
  var a = document.createElement('a');
  a.href = url;
  return decodeURIComponent(_.last(a.pathname.split('/')));
}

Utils.prototype.getGrade = function(score, inverse, size) {
  var score = Math.round((inverse === true ? score : 10 - score) / 2);
  var grade = 'E';
  if (score <= 1) {
    grade = 'A';
  } else if (score <= 2) {
    grade = 'B';
  } else if (score <= 3) {
    grade = 'C';
  } else if (score <= 4) {
    grade = 'D';
  }
  
  var gradeColor = {
    'A': 'success', 'B': 'warning', 'C': 'warning',
    'D': 'danger', 'E': 'danger'
  };

  return <span>
    <span className={"grade-badge " + gradeColor[grade] + " grade-badge-" + size}>{grade}</span><br/>
  </span>
}

module.exports = new Utils();
