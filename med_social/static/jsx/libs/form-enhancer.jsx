var React = require('react');


var Mixin = {
  componentDidMount: function(){
    $(this.getDOMNode()).find('input[type=date]').pickadate({
      monthsShort: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      weekdaysShort: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
      format: 'd mmmm, yyyy',
      selectYears: 30,
      selectMonths: true,
      theme: 'classic',
      container: 'body',
    });
  },

  componentWillUnmount: function(){
    $(this.getDOMNode()).find('input[type=date]').each(function(i, input){
      $(input).pickadate('picker').stop();
    });
  }
};


module.exports = {
  'Mixin': Mixin
};
