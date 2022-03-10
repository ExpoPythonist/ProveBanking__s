/** @jsx React.DOM */
var React = require('react');
var moment = require('moment');

var Ago = React.createClass({
  render: function(){
    var today = new Date();
    var formatString = today.getFullYear() == this.props.date.getFullYear() ? 'Do MMM' : 'Do MMM YYYY';
    return <span className={this.props.classes}>{moment(this.props.date).format(formatString)}</span>;
  }
});


var Range = React.createClass({
  asDate: function(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  },

  render: function(){
    var today = this.asDate(new Date());
    var start = this.asDate(this.props.start);
    var end = this.asDate(this.props.end);

    var cx = React.addons.classSet;
    var startClasses = cx({
      'urgent': today <= start
    });

    var endClasses = cx({
      'urgent': start <= today <= end
    });

    return <span className="timestamp"><Ago classes={startClasses} date={this.props.start}/> - <Ago classes={endClasses} date={this.props.end}/></span>
  }
});


module.exports = {
  Range: Range,
  Ago: Ago
}
